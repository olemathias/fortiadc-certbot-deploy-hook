# fortiadc-certbot-deploy-hook

## Docker
TODO: Add docker usage

## Example usage
```bash
FORTIADC_HOST=fortiadc.example.com \
FORTIADC_USER=admin \
FORTIADC_PASSWORD=mypassword \
LOCAL_CERT_GROUP=k8s-lab-ingress \
DOMAIN=example.com \
CERT_PATH=cert.pem \
KEY_PATH=privkey.pem \
python3 main.py
```

#### Usage with certbot (http)
Environment variables (without `DOMAIN`) needs to be set
```bash
certbot certonly --standalone -d example.org -d www.example.org \
--deploy-hook /opt/fortiadc-certbot-deploy-hook/main.py \
--agree-tos -m user@example.com \
--server https://acme-staging-v02.api.letsencrypt.org/directory
```
