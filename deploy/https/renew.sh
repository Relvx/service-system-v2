#!/bin/sh
set -eu
cd /opt/service-system-v2
exec 9>/run/service-system-tls-renew.lock
flock -n 9 || exit 0
docker compose run --rm certbot renew --cert-name service-system-ip --non-interactive --no-random-sleep-on-renew
docker exec ss_frontend nginx -t
docker exec ss_frontend nginx -s reload
