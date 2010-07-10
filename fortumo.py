import os
import hashlib
import yaml

# fortumo saadab andmeid XML formaadis
from xml.dom import minidom

#load data from fortumo.yaml
f = open("fortumo.yaml")
fortumo_config = yaml.load(f, Loader=yaml.Loader)

class RequestValidator:
    allowed_ips = fortumo_config["allowed_ips"]
    api_key = fortumo_config["api_key"]
    secret = fortumo_config["secret"]
    
    def check_ip(self, remote_addr):
        return remote_addr in self.allowed_ips

    def check_api_key(self, api_key):
        #Always return true if API key checking is disabled
        return not self.api_key or self.api_key == api_key
    
    def signature(self, params_array):
        str = ''
        for k in self.ksort(params_array):
            v = params_array[k]
            if k != 'sig':
                str += u"%s=%s" % (k,v)
        str += unicode(self.secret)

        # hashlib doesn't like unicode, so it needs to be encoded
        signature = hashlib.md5(str.encode("utf-8")).hexdigest()
        return signature
    
    def check_signature(self, params_array):
        #Always return true if signature checking is disabled
        if not self.secret:
            return True
        if not "sig" in params_array:
            return False
        return params_array['sig']==self.signature(params_array)
    
    def ksort(self, d, func = None):
        keys = d.keys()
        keys.sort(func)
        return keys

def GenerateSignature(arg_list):
    req = RequestValidator()
    return req.signature(arg_list)

def CheckValidRequest(arg_list):

    req = RequestValidator()
    if not req.check_ip(os.environ['REMOTE_ADDR']):
        return False

    if not 'api_key' in arg_list or not req.check_api_key(arg_list['api_key']):
        return False

    if not req.check_signature(arg_list):
        return False

    return True
    
# Tegeleb XML päringute analüüsimisega
class RequestHandler:

    # võtab sisendiks XML stringi
    def parseRequestXML(self, sXML):
    
        xmlNode = minidom.parseString(sXML.encode("utf-8"))
    
        if xmlNode.firstChild.tagName == "create-service-request":
            return self.createServiceRequest(xmlNode.firstChild)
        elif xmlNode.firstChild.tagName == "remove-countries-request":
            return self.removeCountriesRequest(xmlNode.firstChild)
      
        return False
    
    # uue teenuse lisamine
    def createServiceRequest(self, xmlNode):

        xml_service = xmlNode.getElementsByTagName('service')[0]
        xml_user    = xmlNode.getElementsByTagName('user')[0]
        xml_locale  = xmlNode.getElementsByTagName('locale')[0]
        xml_service_countries = xml_service.getElementsByTagName('countries')[0].getElementsByTagName('country')
    
        service = {
            'id':  xml_service.getElementsByTagName('id')[0].firstChild.data
        }
    
        user = {
            'id':      xml_user.getElementsByTagName('id')[0].firstChild.data,
            'email':   xml_user.getElementsByTagName('email')[0].firstChild.data,
            'phone':   xml_user.getElementsByTagName('phone')[0].firstChild.data,
            'realname':xml_user.getElementsByTagName('realname')[0].firstChild.data,
            'country': xml_user.getElementsByTagName('country')[0].firstChild.data,
            'locale':  xml_locale.firstChild.data.upper()
        }
   
        countries = []    
        for country in xml_service_countries:
            countries.append({
                'name':      country.getElementsByTagName('name')[0].firstChild.data.upper(), 
                'shortcode': country.getElementsByTagName('shortcode')[0].firstChild.data,
                'keyword':   country.getElementsByTagName('keyword')[0].firstChild.data.upper(),
                'price':     country.getElementsByTagName('price')[0].firstChild.data,
                'currency':  country.getElementsByTagName('currency')[0].firstChild.data.upper()
            })
        
        return {'user': user, 'service': service, 'countries': countries}

    # maade muutmine
    def removeCountriesRequest(self, xmlNode):
        xml_service = xmlNode.getElementsByTagName('service')[0]
        xml_user    = xmlNode.getElementsByTagName('user')[0]
        xml_service_countries = xml_service.getElementsByTagName('countries')[0].getElementsByTagName('country')

        service = xml_service.getElementsByTagName('id')[0].firstChild.data
        user    = xml_user.getElementsByTagName('id')[0].firstChild.data
   
        countries = []
        for country in xml_service_countries:
            countries.append({
                'name':     country.getElementsByTagName('name')[0].firstChild.data.upper(),
                'end_date': country.getElementsByTagName('end_date')[0].firstChild.data.upper()
            })

        return {'user': user, 'service': service, 'countries': countries}
