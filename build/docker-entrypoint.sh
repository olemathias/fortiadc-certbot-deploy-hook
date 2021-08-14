#!/bin/sh
mkdir -p /etc/letsencrypt/renewal-hooks/deploy/
cat <<EOF >/etc/letsencrypt/renewal-hooks/deploy/run.sh
#!/bin/sh
python3 /opt/main.py
EOF
chmod +x /etc/letsencrypt/renewal-hooks/deploy/run.sh

while :; do certbot renew --logs-dir /etc/letsencrypt/logs --work-dir /etc/letsencrypt/workdir; sleep 12h; done;
