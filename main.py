#!/usr/bin/env python3

import os
import re
import random
import string
from datetime import date
import logging
import sys
import time

import fortiadc

root = logging.getLogger()
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

# From Certbot hook # "/etc/letsencrypt/live/example.com"
RENEWED_LINEAGE = os.environ.get("RENEWED_LINEAGE", None)

# Not used if RENEWED_LINEAGE is set
DOMAIN = os.environ.get("DOMAIN", None)

INTERMEDIATE = os.environ.get("INTERMEDIATE", "letsencrypt-rsa")
LOCAL_CERT_GROUP = os.environ.get("LOCAL_CERT_GROUP", "certbot")

USER = os.environ.get("FORTIADC_USER", "admin")
HOST = os.environ.get("FORTIADC_HOST", None)
if HOST is None:
    logging.error("FORTIADC_HOST needs to be set. Example: FORTIADC_HOST=fortiadc.example.com")
    raise ValueError("FORTIADC_HOST needs to be set. Example: FORTIADC_HOST=fortiadc.example.com")
PASSWORD = os.environ.get("FORTIADC_PASSWORD", None)
if PASSWORD is None:
    logging.error("FORTIADC_PASSWORD needs to be set. Example: FORTIADC_PASSWORD=mypassword")
    raise ValueError("FORTIADC_PASSWORD needs to be set. Example: FORTIADC_PASSWORD=mypassword")
if RENEWED_LINEAGE is not None:
    DOMAIN = str(os.path.basename(os.path.normpath(RENEWED_LINEAGE)))
elif DOMAIN is None:
    logging.error("RENEWED_LINEAGE or DOMAIN needs to be set")
    raise ValueError("RENEWED_LINEAGE or DOMAIN needs to be set")

LETSENCRYPT_LIVE_FOLDER = os.environ.get("LETSENCRYPT_LIVE_FOLDER", "/etc/letsencrypt/live/")

CERT_PATH = os.environ.get("CERT_PATH", os.path.join(LETSENCRYPT_LIVE_FOLDER, DOMAIN, "fullchain.pem"))
KEY_PATH = os.environ.get("KEY_PATH", os.path.join(LETSENCRYPT_LIVE_FOLDER, DOMAIN, "privkey.pem"))

if not os.path.exists(CERT_PATH):
    logging.error("Cert not found in \"{}\"".format(CERT_PATH))
    raise Exception("Cert not found in \"{}\"".format(CERT_PATH))
if not os.path.exists(KEY_PATH):
    logging.error("Key not found in \"{}\"".format(KEY_PATH))
    raise Exception("Key not found in \"{}\"".format(KEY_PATH))

logging.info("Domain: \"{}\". Will upload to \"{}\" and add to group \"{}\".".format(DOMAIN, HOST, LOCAL_CERT_GROUP))
logging.info("CERT_PATH {}".format(CERT_PATH))
logging.info("KEY_PATH {}".format(KEY_PATH))

cert_name = DOMAIN.replace(".","_")

client = fortiadc.client(host=HOST, username=USER, password=PASSWORD)
logging.info("Connected to FortiADC: {}.".format(HOST))

#p = re.compile('^certbot_(.+)_(\d{8})-(\w+)$')
#certs = [cert for cert in client.get_certificate_local() if p.match(cert["mkey"]) and p.match(cert["mkey"]).group(1) == cert_name]

# To not have duplicates
serial = ''.join(random.choices(string.ascii_uppercase, k=3))
current_date = date.today().strftime("%Y%m%d")
mkey = "certbot_{0}_{1}-{2}".format(cert_name, current_date, serial)

client.upload_certificate_local(mkey=mkey, cert_path=CERT_PATH, key_path=KEY_PATH)
client.add_certificate_local_group_member(pkey=LOCAL_CERT_GROUP, mkey=mkey, intermediate=INTERMEDIATE)

logging.info("\"{}\" uploaded and added to group! Sleep 5 next".format(mkey))

# To make sure the new cert is ready before removing the old
time.sleep(5)

# Get the certficate(s) from FortiADC if exists
p = re.compile('^certbot_(.+)_(\d{8})-(\w+)$')
certs = [cert for cert in client.get_certificate_local_group_members(pkey=LOCAL_CERT_GROUP) if p.match(cert["local_cert"]) and p.match(cert["local_cert"]).group(1) == cert_name]

for c in certs:
    if not c["local_cert"] == mkey:
        client.delete_certificate_local_group_member(pkey=LOCAL_CERT_GROUP, mkey=c["mkey"])
        logging.info("Removed \"{}\" from group \"{}\"".format(c["local_cert"], LOCAL_CERT_GROUP))

# ^certbot_(.+)_(\d{8})-(\d+)$
# ^certbot_gathering_systems_(\d{8})-(\d+)$
