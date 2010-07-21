#!/usr/bin/env python
# coding: utf-8
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import logging

from django.utils import simplejson as json
from google.appengine.api import memcache

from google.appengine.api import urlfetch
import urllib

from google.appengine.ext.webapp import template

# IP järgi asukohamaa leidmine
sys.path.insert(0, 'iploc.zip')
from iploc import convert as iptocountry

# GETTEXT
os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'
from django.conf import settings
settings._target = None
from django.utils import translation

# fortumo sõnumite autoriseerimiseks
import fortumo
import yaml

# DB
from google.appengine.ext import db
from models import User, Service, Message

# asukoha ja keele map IP kontrolli ja country parameetri jaoks
country_to_locale = {
    "ee":"et"
}



class MainHandler(webapp.RequestHandler):
    def get(self):
        
        SetLanguage(self, check_ip = True)
        
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'views/front.html')
        self.response.out.write(template.render(path, template_values))

class EditHandler(webapp.RequestHandler):
    def get(self):

        SetLanguage(self, check_ip = True)
        
        req = fortumo.RequestValidator()
        if not req.check_signature({
                'api_key': fortumo.fortumo_config["api_key"],
                'service_id': self.request.get('service_id'),
                'sig':self.request.cookies.get('sig')
            }):
            return ShowError(self, _("Session expired"))
        
        service = GetService(self.request.get('service_id'))
        if not service:
            return ShowError(self, _("Unknown service"))
        
        user = service.user
        SetLanguage(self, user.locale)
        
        template_values = {
            'title': _("SMS Poll")
        }
        path = os.path.join(os.path.dirname(__file__), 'views/edit.poll.html')
        self.response.out.write(template.render(path, template_values))


##### FORTUMO PÄRINGUD ########

class IncomingMessageHandler(webapp.RequestHandler):
    def post(self):
        
        SetLanguage(self)
        
        if not fortumo.CheckValidRequest(self.request.params):
            logging.debug({"error": "authorization", "data": self.request.params})
            self.response.out.write(_('Request authentication failed'))
            return
        
        error = {"message":None}
        def tnx():
            
            service = Service.get_by_key_name(u"<%s>" % self.request.get("service_id"))
            if not service:
                error["message"] = _("Service not found")
                return

            service.messages += 1
            memcache.set(u"service-%s" % self.request.get("service_id"), service)
            
            message = Message(key_name = u"<%s>" % self.request.get("message_id"), parent = service)
            message.service   = service
            message.message_id= self.request.get("message_id")
            message.message   = self.request.get("message").strip()
            message.sender    = self.request.get("sender")
            message.country   = self.request.get("country")
            message.price     = int(float(self.request.get("price").strip())*100)
            message.currency  = self.request.get("currency")
            message.keyword   = self.request.get("keyword")
            message.shortcode = self.request.get("shortcode")
            message.operator  = self.request.get("operator")
            message.test      = self.request.get("test") == "true"
            
            db.put([message, service])
            
        try:
            db.run_in_transaction(tnx)
        except db.TransactionFailedError, e:
            error["message"] = _("Database error")
        
        if error["message"]:
            logging.debug({"error": "transaction", "message": error["message"], "data": self.request.params})
            self.response.out.write(error["message"])
            return
        
        self.response.out.write(_("Thank you for voting!"))


class LoginHandler(webapp.RequestHandler):
    def get(self):
        
        SetLanguage(self)
        
        arg_list = {
            'api_key': fortumo.fortumo_config["api_key"],
            'auth_token': self.request.get('auth_token'),
            'method': 'fortumo.auth.validateToken',
            'user_id': self.request.get('user_id')
        }
        req = fortumo.RequestValidator()
        arg_list['sig'] = req.signature(arg_list)
    
        url = "http://api.fortumo.com/service-types/api"
    
        form_data = urllib.urlencode(arg_list)
        try:
            result = urlfetch.fetch(url=url,
                payload=form_data,
                method=urlfetch.POST,
                headers={'Content-Type': 'application/x-www-form-urlencoded'})
        except:
            result = False
        
        if not result or result.status_code != 200:
            logging.debug({"error": "login", "data": self.request.params})
            return ShowError(self, _('Request authentication failed'))
        
        cookie_sig = req.signature({
            'api_key': fortumo.fortumo_config["api_key"],
            'service_id': self.request.get('service_id')
        });
        
        set_cookie(self, "sig", cookie_sig,"/")
        self.redirect("/edit?service_id=%s" % self.request.get('service_id'))


class CreateServiceRequestHandler(webapp.RequestHandler):
    def post(self):
        
        SetLanguage(self)
        
        if not fortumo.CheckValidRequest(self.request.params):
            self.error(500)
            logging.debug({"error": "authorization", "data": self.request.params})
            self.response.out.write(_('Request authentication failed'))
            return
        
        req = fortumo.RequestHandler()
        req_data = req.parseRequestXML(self.request.get("xml"))
        if not req_data:
            self.error(500)
            logging.debug({"error": "validation", "data": self.request.params})
            self.response.out.write(_('Request authentication failed'))
            return
        
        user = CheckUser(req_data["user"])
        if not user:
            self.error(500)
            logging.debug({"error": "db create user", "data": self.request.params})
            self.response.out.write(_('User verification failed'))
            return
        
        service = CheckService(req_data["service"], req_data["countries"], user)
        if not service:
            self.error(500)
            logging.debug({"error": "db create service", "data": self.request.params})
            self.response.out.write(_('Service verification failed'))
            return
        
        self.response.out.write(_('Service created'))

# TODO: Tuleks arvestada määratud ajaga, momendil võetakse kohe maha
class RemoveServiceRequestHandler(webapp.RequestHandler):
    def post(self):
        
        SetLanguage(self)
        
        if not fortumo.CheckValidRequest(self.request.params):
            self.error(500)
            logging.debug({"error": "authorization", "data": self.request.params})
            self.response.out.write(_('Service verification failed'))
            return
        
        req = fortumo.RequestHandler()
        req_data = req.parseRequestXML(self.request.get("xml"))
        if not req_data:
            self.error(500)
            logging.debug({"error": "validation", "data": self.request.params})
            self.response.out.write(_('Service verification failed'))
            return
        
        if req_data["service"]:
            service = GetService(req_data["service"])
            if service:
                try:
                    service.active = False
                    service.put()
                except:
                    pass
            memcache.delete(u"service-%s" % req_data["service"])

        self.response.out.write(_("Service removed"))


##### ANDMETE PÄRINGUD ########

# korjab välja kasutaja andmed
def GetUser(id):
    user = memcache.get(u"user-%s" % id)
    if user is None:
        user = User.get_by_key_name(u"<%s>" % id)
        if not user:
            return False
        memcache.set(u"user-%s" % id, user)
    return user

# korjab välja teenuse andmed või False, kui pole või kui on mitte aktiivne
def GetService(id):
    service = memcache.get(u"service-%s" % id)
    if service is None:
        service = Service.get_by_key_name(u"<%s>" % id)
        if not service:
            return False
        memcache.set(u"service-%s" % id, service)
    return service.active and service

# otsib algul memcache'st, edasi juba andmebaasist
# ja kui ikka veel pole, siis lisab uuena
def CheckService(service_data, country_data, user):
    service = memcache.get(u"service-%s" % service_data["id"])
    if service and service.user is not user:
        return False
    if service is None:
        service = Service.get_by_key_name(u"<%s>" % service_data["id"])
        if not service:
            pointer_to_service = {"service": None}
            def tnx(service_data, country_data, user):
                service = Service(key_name = u"<%s>" % service_data["id"])
                service.id = service_data["id"]
                service.user = user
                service.countries = json.dumps(country_data)
                service.put()
                pointer_to_service["service"] = service
            try:
                db.run_in_transaction(tnx, service_data = service_data,
                                  country_data = country_data, user=user)
                memcache.set(u"service-%s" % service_data["id"], service)
                return pointer_to_service["service"]
            except db.TransactionFailedError, e:
                return False
        memcache.set(u"service-%s" % service_data["id"], service)
        return service
    return service

# otsib algul memcache'st, edasi juba andmebaasist
# ja kui ikka veel pole, siis lisab uuena
def CheckUser(user_data):
    user = memcache.get(u"user-%s" % user_data["id"])
    if user is None:
        user = User.get_by_key_name(u"<%s>" % user_data["id"])
        if not user:
            # python sulund on "read only"
            pointer_to_user = {'user': None}
            def tnx(user_data):
                user = User(key_name = u"<%s>" % user_data["id"])
                user.id = user_data["id"]
                user.email = user_data["email"]
                user.realname = user_data["realname"]
                user.locale = user_data["locale"]
                user.country = user_data["country"]
                user.phone = user_data["phone"]
                user.put()
                pointer_to_user["user"] = user
            try:
                db.run_in_transaction(tnx, user_data = user_data)
                memcache.set(u"user-%s" % user_data["id"], user)
                return pointer_to_user["user"]
            except db.TransactionFailedError, e:
                return False
        memcache.set(u"user-%s" % user_data["id"], user)
        return user
    return user

##### UTILIIDID ########

def set_cookie(web, name, value, path):
    cookie_data = '%s=%s; path=%s' % (name.encode(), value.encode(), path.encode())
    logging.debug(cookie_data)
    web.response.headers.add_header('Set-Cookie', cookie_data)

# Näita ERROR lehte
def ShowError(self, msg):
    self.error(500)
    template_values = {
        'message': msg
    }
    path = os.path.join(os.path.dirname(__file__), 'views/error.html')
    self.response.out.write(template.render(path, template_values))
    return False

# Määrab kasutatava keele, kontrollides erinevaid parameetreid
# IP on vaikimisi väljas, kuna Fortumo päringud väljastaksid nii
# alati asukohaks eesti
def SetLanguage(self, forced=False, check_ip = False):
    
    if not forced:
        # vaikimisi
        locale = "en"

        # IP kontroll siia
        if check_ip:
            country = iptocountry()
            if country and country != "XX" and country.lower() in country_to_locale:
                locale = country_to_locale[country.lower()]

        # kontrolli country parameetrit
        if self.request.get("country") and self.request.get("country").lower() in country_to_locale:
            locale = country_to_locale[self.request.get("country").lower()]

        # kontrolli locale parameetrit 
        if self.request.get("locale"):
            locale = self.request.get("locale")
    
        # kontrolli küpsist
        if self.request.cookies.get('locale'):
            locale = self.request.cookies.get('locale')
    
    else:
        locale = forced
    
    translation.activate(locale.lower()[:2])

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/api/user', CreateServiceRequestHandler),
                                          ('/api/remove', RemoveServiceRequestHandler),
                                          ('/api/incoming', IncomingMessageHandler),
                                          ('/login', LoginHandler),
                                          ('/edit', EditHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
