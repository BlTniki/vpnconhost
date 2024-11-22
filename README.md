## About
Это компонент для [VPNconServer](https://github.com/BlTniki/vpnconserver). Служит запуска на сервере, до которого будет строится туннель.

## Initialization RU
Для начала следует настроить [**Wireguard**](https://www.digitalocean.com/community/tutorials/how-to-set-up-wireguard-on-ubuntu-20-04).
Далее следует клонировать проект
```bash
git clone https://github.com/BlTniki/vpnconhost.git
```
==Убедится, что все папки на месте!==

Следует создать файл `appconf.txt`:
```
< Пароль указываемый в заголовке запроса "Auth" : (любая строка) >
< Рабочую дирректорию в которой лежит проект. Пример: /ur/work/dir/ (Обязательно / в конце) >
< Адресс сервера, на котором запускается проет, и порт, который слушает wireguard. Пример: 0.0.0.0:0000 >
< Ответ на вопрос: "Запуск в тестовом режиме?(YES/NO)" >
< Вид SUDO команды (SUDO или пустоту если она не требуется)" >
< DNS сервера (например: 0.0.0.0, 0.0.0.0)" >
< Public key сервера >
< Ip и порт обфускатора, если он не используется, то написать null >
```
Далее запуск проекта будет следовать [этому гайду](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-20-04)
Следует создать нового пользователя `nginx`:
```bash
sudo useradd -r -s /usr/sbin/nologin nginx
sudo mv /root/vpnconhost /home/nginx/vpnconhost
```
Для конфигурации `gunicorn` следует использовать этот конфиг:
```
[Unit]
Description=Gunicorn instance to serve vpnconhost
After=network.target

[Service]
User=nginx
Group=www-data
WorkingDirectory=/home/nginx/vpnconhost
Environment="PATH=/home/nginx/vpnconhost/vpnconhostenv/bin"
ExecStart=/home/nginx/vpnconhost/vpnconhostenv/bin/gunicorn --workers 3 --bind unix:vpnconhost.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```
Для конфигурации сайта в `nginx` следует использовать этот конфиг
```
server {
    listen 80;
    listen [::]:80;
    location / {
        include proxy_params;
        proxy_pass http://unix:/home/nginx/vpnconhost/vpnconhost.sock;
   }
}
```

после всех изменений следует настроить права `nginx`:
```bash
chmod 777 /home/nginx -R
chown nginx:www-data /home/nginx -R
usermod -a -G nginx www-data
sudo visudo
```
откроется файл в который мы допишем 
```
nginx ALL=(ALL) NOPASSWD:ALL
```

После успешного запуска, можно добавить этот хост в [VPNconServer](https://github.com/BlTniki/vpnconserver). 
Пример добавления хоста:
```
{
    "name" : "test",
    "ipadress": "127.0.0.1:5000", // url to vpnconhost app
    "serverPassword": "5543678", // set in appconf.txt password
    "serverPublicKey": "lolkek" // wireguard public key
}
```
