# collect_switch_info

Проект **collect_switch_info** предназначен для сбора данных с коммутатора Cisco Catalyst.
Вывод с сетевого устройства может быть обработан при помощи шаблонов TextFSM или сохранен в неизменном виде.
Результаты сохраняются в файлы (папка `files`) и при необходимости выводятся в консоль.
На текущий момент осуществляется сбор следующей информации:
- Версия коммутатора.
- Стартовая конфигурация.
- Текущая конфигурация.
- Сведения о списках контроля доступа.
- Сведения об интерфейсах.

### Стэк технологий:
- Python (необходима версия не ниже 3.10)
- Netmiko
- Docker

### Как запустить проект:
- Склонируйте репозиторий на свой компьютер
- Создайте `.env` файл в корневой директории, рядом с файлом `docker-compose.yml`.
  В `.env` файле должны содержаться следующие переменные (в репозитории представлен пример данного файла .env.example):
```
DEVICE_TYPE=cisco_ios
HOST=192.168.100.1
USERNAME=cisco
PASSWORD=cisco
SECRET=cisco
```
- Из корня проекта запустите Docker
`$ docker-compose up`