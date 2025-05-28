#!/usr/bin/env python

import os
import sys
from pathlib import Path


def initialize_django():

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as error:
        error_message = (
            "Не удалось импортировать Django. "
            "Убедитесь, что он установлен и доступен в переменной окружения PYTHONPATH. "
            "Возможно, вы забыли активировать виртуальное окружение?"
        )
        raise ImportError(error_message) from error
    
    return execute_from_command_line


def main():
    django_command = initialize_django()
    django_command(sys.argv)


if __name__ == '__main__':
    main()