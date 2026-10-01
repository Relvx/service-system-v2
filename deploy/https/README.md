# HTTPS рабочего сервера

Адрес: https://72.56.237.245. Сертификат Let's Encrypt выпущен для IP,
использует профиль `shortlived` и требует автоматического продления.
Покупка домена или балансировщика не требуется.

Эта конфигурация предназначена для существующего Docker Compose проекта
в `/opt/service-system-v2`. База данных и backend при её применении не
перезапускаются. Файл `active.conf` и корневой `docker-compose.override.yml`
создаются на сервере и не хранятся в Git. Приватные ключи находятся только
в `/etc/letsencrypt` на сервере.

## Первичная установка

1. Сохранить текущий nginx-конфиг и `docker-compose.yml` вне проекта.
2. Создать `/srv/service-system-acme`, `/etc/letsencrypt`, `/var/lib/letsencrypt`.
3. Скопировать `nginx-bootstrap.conf` в `deploy/https/active.conf`, а
   `deploy/https/docker-compose.override.yml` в корень проекта. Если корневой
   override уже существует, объединить настройки, не перезаписывая его.
4. Проверить `docker compose config --quiet`, затем выполнить
   `docker compose up -d --no-build --no-deps frontend`.
5. Выпустить сертификат (первую проверку проводить с `--staging` и отдельным
   именем `service-system-ip-test`; этот тестовый сертификат не устанавливать):

   ```sh
   docker compose run --rm certbot certonly --non-interactive --agree-tos \
     --register-unsafely-without-email --preferred-profile shortlived \
     --webroot -w /var/www/acme --ip-address 72.56.237.245 \
     --cert-name service-system-ip
   ```

6. Скопировать `nginx-https.conf` в `active.conf`, проверить
   `docker exec ss_frontend nginx -t`, затем применить
   `docker exec ss_frontend nginx -s reload`.
7. Установить `renew.sh` как `/usr/local/sbin/service-system-renew-tls`
   с правами 0755, service и timer в `/etc/systemd/system/`. Выполнить
   `systemctl daemon-reload` и `systemctl enable --now service-system-tls-renew.timer`.

Certbot 5.4.0 поддерживает сертификаты для IP в режиме webroot. При смене
IP следует обновить nginx-конфиг и выпустить новый сертификат.
Использование технического домена через HTTP перенаправляет на HTTPS IP;
сертификат не распространяется на HTTPS технического домена.

## Проверки и обслуживание

```sh
curl --fail https://72.56.237.245/login -o /dev/null
docker compose run --rm certbot renew --cert-name service-system-ip --dry-run
systemctl list-timers service-system-tls-renew.timer
journalctl -u service-system-tls-renew.service
```

Таймер проверяет продление дважды в день. При сбое смотри журнал service;
сам таймер не отправляет уведомления. После перезагрузки сервера Docker
поднимает контейнеры, а systemd продолжает проверки продления. Сертификаты
и webroot сохранены на хосте, а не внутри временного контейнера Certbot.

## Возврат к HTTP

Остановить таймер, восстановить прежний nginx-конфиг в `active.conf`, проверить
`nginx -t` и перезагрузить nginx. Это убирает перенаправление на HTTPS,
не затрагивая данные программы. Не удалять сертификаты для временного отката.
