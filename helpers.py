import os
import sys
import logging

from google.appengine.ext.webapp import template

# IP järgi asukohamaa leidmine
sys.path.insert(0, 'iploc.zip')
from iploc import convert as iptocountry

from django.utils import translation

# asukoha ja keele map IP kontrolli ja country parameetri jaoks
country_to_locale = {
    "ee":"et"
}

def set_cookie(web, name, value, path):
    cookie_data = '%s=%s; path=%s' % (name.encode(), value.encode(), path.encode())
    logging.debug({"set-cookie": cookie_data})
    web.response.headers.add_header('Set-Cookie', cookie_data)

# Näita ERROR lehte
def ShowError(web, msg):
    web.error(500)
    template_values = {
        'message': msg
    }
    path = os.path.join(os.path.dirname(__file__), 'views/error.html')
    web.response.out.write(template.render(path, template_values))
    return False

# Määrab kasutatava keele, kontrollides erinevaid parameetreid
# IP on vaikimisi väljas, kuna Fortumo päringud väljastaksid nii
# alati asukohaks eesti
def SetLanguage(web, forced=False, check_ip = False):
    
    if not forced:
        # vaikimisi
        locale = "en"

        # IP kontroll siia
        if check_ip:
            country = iptocountry()
            if country and country != "XX" and country.lower() in country_to_locale:
                locale = country_to_locale[country.lower()]

        # kontrolli country parameetrit
        if web.request.get("country") and web.request.get("country").lower() in country_to_locale:
            locale = country_to_locale[web.request.get("country").lower()]

        # kontrolli locale parameetrit 
        if web.request.get("locale"):
            locale = web.request.get("locale")
    
        # kontrolli küpsist
        if web.request.cookies.get('locale'):
            locale = web.request.cookies.get('locale')
    
    else:
        locale = forced

    translation.activate(locale.lower()[:2])
