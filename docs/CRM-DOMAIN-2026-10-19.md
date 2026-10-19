# Service System: crm.analitgaz.ru · 19 октября 2026

Service System опубликована на **https://crm.analitgaz.ru/login**. DNS A уже
указывала на 72.56.237.245; DNS агентом не изменялась. AAAA и CAA для CRM
в публичных ответах не обнаружены.

## Что настроено

- Отдельный HTTP/HTTPS виртуальный хост в существующем Nginx ss_frontend.
  Сертификат Let's Encrypt `service-system-crm`, срок до 17 января 2027.
  HTTP перенаправляет на HTTPS с сохранением пути.
- Резервные копии конфигурации mode 0600 в `/root/service-system-crm-nginx-backups/`.
  Установщик сохраняет inode bind-mounted active.conf и другие виртуальные хосты.
  После последней корректировки: `20261019T153002266443Z.conf`.
- `X-Robots-Tag: noindex, nofollow`, в том числе на SPA index fallback.
- Timer `service-system-crm-tls-renew.timer` enabled/active, дважды в день,
  общий lock с IP/preview. Certbot dry-run завершился успешно.
- В закрытом env сайта изменён только SERVICE_SYSTEM_LEAD_URL на
  `https://crm.analitgaz.ru/api/integrations/website/service-requests`.
  Ключ не изменялся, ссылки новых почтовых уведомлений ведут на
  `https://crm.analitgaz.ru/website-requests`.
  Закрытая копия env: `/etc/analitgaz/website.env.pre-crm-20261019` (0600).
- Пересозданы только website/worker сайта, оба healthy. Контейнеры программы
  и база не перезапускались; прежний HTTPS вход по IP сохранён.

## Проверки

- /login и /website-requests: 200, два JS/CSS ресурса: 200.
- /api/health: 200, status ok.
- /api/auth/me и /api/website-requests без авторизации: 401.
- HTTP /login → HTTPS /login; сертификат проверен без отключения TLS verification.
- Старый HTTPS IP программы и preview сайта: 200.
- Из worker выполнен POST с действующим ключом и пустым объектом:
  ожидаемый 422 после проверки ключа, до сохранения. Новых обращений нет.
- В очереди остаются две ранее доставленные заявки по каждому каналу.
- Полный вход под пользователем не выполнялся: пароль у владельца. При первом
  посещении домена нужно войти существующим логином и паролем; браузер хранит
  авторизацию отдельно для IP и домена.

## Откат

Если проблема относится к новому домену, пользоваться прежним HTTPS IP.
Для конфигурации восстановить собственный CRM-блок из закрытой копии,
сохраняя inode active.conf; выполнить nginx -t перед reload. При необходимости
вернуть прежний SERVICE_SYSTEM_LEAD_URL из закрытого env-backup и пересоздать
только сайт/worker. SQLite/PostgreSQL и уже поступившие заявки не откатывать.

Основной сайт analitgaz.ru — отдельный этап: его DNS на момент этой работы
ещё указывает на прежний хостинг. Подключение CRM не переключает сайт компании.
