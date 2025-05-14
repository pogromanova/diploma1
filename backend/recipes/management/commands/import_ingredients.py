import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from recipes.models import Ingredient


class Command(BaseCommand):

    help = 'Импортирует ингредиенты из JSON-файла'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            nargs='?', 
            help='Путь к JSON-файлу с ингредиентами'
        )

    def handle(self, *args, **options):
        try:
            file_path = options.get('file_path') or os.getenv('INGREDIENTS_FILE_PATH', '/app/data/ingredients.json')
            
            if not os.path.exists(file_path):
                alternate_paths = [
                    '/app/data/ingredients.json',
                    '/data/ingredients.json',
                    '/app/data/ingredients.csv',
                    '/data/ingredients.csv'
                ]
                
                for alt_path in alternate_paths:
                    if os.path.exists(alt_path):
                        file_path = alt_path
                        self.stdout.write(f'Файл найден по альтернативному пути: {alt_path}')
                        break
                else:
                    raise CommandError(f'Файл не найден. Проверенные пути: {file_path}, {", ".join(alternate_paths)}')
                    
            with open(file_path, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)
                
            if not isinstance(ingredients_data, list):
                raise CommandError(
                    'Файл должен содержать список ингредиентов'
                )
                
            counter = 0
            for ingredient in ingredients_data:
                try:
                    Ingredient.objects.get_or_create(
                        name=ingredient['name'],
                        measurement_unit=ingredient['measurement_unit']
                    )
                    counter += 1
                except KeyError as e:
                    self.stderr.write(
                        f'Ошибка в данных: отсутствует поле {e}'
                    )
                except IntegrityError:
                    self.stderr.write(
                        f'Ингредиент {ingredient["name"]} уже существует'
                    )
                    
            self.stdout.write(
                self.style.SUCCESS(f'Успешно импортировано {counter} ингредиентов из {file_path}')
            )
            
        except Exception as e:
            raise CommandError(f'Ошибка при импорте ингредиентов: {e}')