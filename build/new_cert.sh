#!/bin/sh

DOMAINS=""

for var in "$@"
do
    DOMAINS="$DOMAINS-d $var "
done

certbot certonly --standalone $DOMAINS --agree-tos -m $LE_EMAIL --deploy-hook /etc/letsencrypt/renewal-hooks/deploy/run.sh
