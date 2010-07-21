VoteSMS
=======

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
