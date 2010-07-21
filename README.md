VoteSMS
=======

URLid
-----

* **Message URL** (sissetulevad sõnumid) - `http://server.com/api/incoming`
* **Create URL** (uue teenuse loomine) - `http://server.com/api/user`
* **Delete URL** (teenuse kustutamine) - `http://server.com/api/remove`
* **Edit URL** (sisselogimine) - `http://server.com/login`

Konfiguratsioon
----------------

Konfiguratsioonifailiks on `fortumo.yaml` - sinna tuleb sisestada `api_key` ja `secret` väärtuse, mille leiab Fortumo lehelt teenustüübi andmete juurest.

PO failide genereerimine
------------------------

Tõlkefailide genereerimiseks tasub luua järgmine skript, kus `/home/andris/google_appengine` märgib Google App Engine kataloogi. Skript võtab parameetriks lokaali (en|et_EE jne) ning genereerib sellele vastava PO faili kataloogi `conf/locale`. Skript tuleb käivitada konkreetse rakenduse juurkataloogis.

    #!/bin/sh
    PYTHONPATH=/home/andris/google_appengine/lib/django/ /home/andris \
    google_appengine/lib/django/django/bin/make-messages.py -l $1

MO failide genereerimine
------------------------

MO faile genereerib poEdit ise, kui aga failid on tõlgitud "otse", saab MO failid genereerida järgmise skriptiga. Skript tuleb käivitada konkreetse rakenduse juurkataloogis. Lokaali ette määrama ei pea, MO failid luuakse kõikidest saadaolevatest lokaalidest.

    #!/bin/sh
    PYTHONPATH=/home/andris/google_appengine/lib/django/ \
    /home/andris/google_appengine/lib/django/django/bin/compile-messages.py

TODO
----

Teenuse kustutamine on bugine - selle asemel et eemaldada riike (ja sealhulgas ka viivitusega), kustutatakse koheselt kogu teenus (muudetakse mitteaktiivseks).