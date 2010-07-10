
from google.appengine.ext import db

class User(db.Model):
    id = db.StringProperty()
    email = db.EmailProperty()
    realname = db.StringProperty()
    locale = db.StringProperty()
    country = db.StringProperty()
    phone = db.PhoneNumberProperty()
    time = db.DateTimeProperty(auto_now_add = True)


class Service(db.Model):
    id = db.StringProperty()
    user = db.ReferenceProperty(reference_class = User)
    countries = db.TextProperty()
    active = db.BooleanProperty(default = True)
    messages = db.IntegerProperty(default = 0)
    time = db.DateTimeProperty(auto_now_add = True)

class Message(db.Model):
    service   = db.ReferenceProperty(reference_class = Service)
    message_id= db.StringProperty()
    message   = db.StringProperty()
    sender    = db.StringProperty()
    country   = db.StringProperty()
    price     = db.IntegerProperty(default = 0)
    currency  = db.StringProperty()
    keyword   = db.StringProperty()
    shortcode = db.StringProperty()
    operator  = db.StringProperty()
    test      = db.BooleanProperty(default = False)
    time = db.DateTimeProperty(auto_now_add = True)
