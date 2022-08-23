import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from netmiko import Netmiko, exceptions
from tabulate import tabulate

load_dotenv()

DEVICE = {
        'device_type': os.getenv('DEVICE_TYPE'),
        'host': os.getenv('HOST'),
        'username': os.getenv('USERNAME'),
        'password': os.getenv('PASSWORD'),
        'secret': os.getenv('SECRET'),
}
COMMANDS = ('sh ver', 'sh startup', 'sh run',
            'sh access-lists', 'sh ip int br')
APP_PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_PATH = os.path.join(APP_PATH, 'templates')
OUTPUT_FILES_PATH = os.path.join(APP_PATH, 'files/')
LOG_FILENAME = __file__.split('/')[-1] + '.log'
LOG_PATH = os.path.join(APP_PATH, 'logs', LOG_FILENAME)
SEND_COMMAND = 'Успешная отправка команды {cmd} на устройство {device}'
WRITE_FILE = 'Успешная запись в файл {filename}'
WRITE_FILE_ERROR = ('Проблема при записи в файл {filename}. '
                    'Описание проблемы {error}')
READ_FILE_ERROR = ('Проблема при чтении файла {filename}. '
                   'Описание проблемы {error}')
ERROR_MESSAGE = 'Сбой в работе программы: {error}'
ENVIRONMENT_VARIABLES_MISSING = (
    'Отсутствуют обязательные переменные окружения: {name}')
STOP_SCRIPT = 'Программа принудительно остановлена.'
START_SCRIPT = 'Программа запущена.'
SHUTDOWN_SCRIPT = 'Завершение работы программы.'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] Event: %(message)s')
file_handler = RotatingFileHandler(
    LOG_PATH, maxBytes=1000000, backupCount=2
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.ERROR)
logger.addHandler(console_handler)


def send_show_command(
        device: dict[str, str], command: str, templates_path: str
        ) -> str | list[dict[str, str]]:
    """
    Получение информации с сетевого устройства.
    Обработка при помощи шаблонов textfsm, либо остаются raw данные.
    Возвращает ошибку в случае проблем с подключением.
    """
    if "NET_TEXTFSM" not in os.environ:
        os.environ["NET_TEXTFSM"] = templates_path
    try:
        with Netmiko(**device) as ssh:
            ssh.enable()
            result = ssh.send_command(command, use_textfsm=True)
            logger.info(
                SEND_COMMAND.format(device=device['host'], cmd=command)
            )
        return result
    except exceptions.NetmikoTimeoutException as error:
        raise ConnectionError(error)
    except exceptions.NetmikoAuthenticationException as error:
        raise ConnectionError(error)


def save_to_file(filename: str, data: str | list[dict[str, str]]) -> None:
    """
    Сохранение информации в файл.
    Преобразование списка словарей в читаемую конструкцию.
    Вывод без обработки textfsm сохраняется без изменений.
    """
    try:
        if isinstance(data, list):
            data = tabulate(data, headers='keys')
        with open(filename, 'w') as f:
            f.write(data)
            logger.info(WRITE_FILE.format(filename=filename.split('/')[-1]))
    except OSError as error:
        raise OSError(WRITE_FILE_ERROR.format(filename=filename, error=error))


def print_file(filename: str) -> None:
    """
    Вывод имени файла и информации из него на консоль.
    """
    try:
        with open(filename, 'r') as f:
            print('\n{:*^50}\n'.format(filename.split('/')[-1]))
            for line in f:
                if not line.startswith("!"):
                    print(line.rstrip())
    except OSError as error:
        raise OSError(READ_FILE_ERROR.format(filename=filename, error=error))


def check_environments() -> bool:
    """Проверяет доступность необходимых переменных окружения."""
    missing_env = [env for env in DEVICE.keys() if not DEVICE.get(env)]
    if missing_env:
        logger.critical(ENVIRONMENT_VARIABLES_MISSING.format(
            name=','.join(missing_env))
        )
        return False
    return True


def main() -> None:
    """
    Основная логика работы скрипта.
    """
    logger.info(START_SCRIPT)
    if not check_environments():
        logger.info(STOP_SCRIPT)
        raise ValueError(STOP_SCRIPT)
    try:
        for command in COMMANDS:
            result = send_show_command(
                DEVICE,
                command,
                templates_path=TEMPLATES_PATH
                )
            filename = '{device}_{cmd}'.format(
                device=DEVICE["host"], cmd=command
                )
            save_to_file(OUTPUT_FILES_PATH + filename, result)
            print_file(OUTPUT_FILES_PATH + filename)
    except Exception as error:
        logger.exception(ERROR_MESSAGE.format(error=error))
    finally:
        logger.info(SHUTDOWN_SCRIPT)


if __name__ == '__main__':
    main()
