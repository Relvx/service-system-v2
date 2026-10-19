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


## Домен CRM

Дополнительные файлы `nginx-crm-bootstrap.conf` и `nginx-crm.conf` обслуживают
`crm.analitgaz.ru`, сохраняя прежний вход по IP и сайт компании.
A-запись должна указывать на 72.56.237.245; старых AAAA быть не должно.

1. Загрузить эти файлы и `install-crm-vhost.py` на сервер. Установить bootstrap:
   `python3 deploy/https/install-crm-vhost.py deploy/https/nginx-crm-bootstrap.conf`.
   Установщик меняет только собственный блок в active.conf, сохраняет inode
   bind-mounted файла, делает закрытую копию и проверяет Nginx перед reload.
2. Проверить публичный ACME webroot, затем выпустить сертификат существующим
   Certbot (из `/opt/service-system-v2`):

   ```sh
   docker compose run --rm certbot certonly --non-interactive --webroot \
     -w /var/www/acme --cert-name service-system-crm -d crm.analitgaz.ru
   ```

   Используется существующая учётная запись ACME.
3. Применить `nginx-crm.conf` тем же установщиком. Сертификат обязателен.
4. Установить `renew-crm.sh` как `/usr/local/sbin/service-system-crm-renew-tls`
   с правами 0755, unit и timer `service-system-crm-tls-renew.*` — в
   `/etc/systemd/system/`. После daemon-reload включить timer и проверить
   `certbot renew --cert-name service-system-crm --dry-run`.
   Все таймеры используют общий lock; IP/preview таймеры сохраняются.
5. Проверить /login, /api/health, защиту /api/auth/me и /api/website-requests,
   ресурсы, HTTP→HTTPS и сохранение IP/preview. Фронтенд рабочего образа
   использует относительный `/api`, пересборка и изменение CORS не нужны.
6. После HTTPS-проверки изменить только SERVICE_SYSTEM_LEAD_URL сайта
   на `https://crm.analitgaz.ru/api/integrations/website/service-requests`
   в закрытом env, сохранить ключ и остальные настройки; пересоздать только
   сайт и worker. Это также переводит ссылку почтовых уведомлений на CRM.

При первом входе по домену нужно авторизоваться заново: localStorage токена
браузер хранит отдельно для IP и домена. Учётные записи и данные не меняются.
