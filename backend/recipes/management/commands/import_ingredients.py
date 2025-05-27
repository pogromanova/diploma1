import json
import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
from recipes.models import Ingredient
from collections import defaultdict


class Command(BaseCommand):
    help = 'Импортирует ингредиенты из JSON-файла с оптимизацией для большого объема данных'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            nargs='?', 
            help='Путь к JSON-файлу с ингредиентами'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5000,
            help='Размер пакета для массовой вставки записей'
        )

    def handle(self, *args, **options):
        try:
            batch_size = options.get('batch_size')
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
                    
            self.stdout.write(f'Загрузка данных из файла {file_path}...')
            with open(file_path, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)
            
            if not isinstance(ingredients_data, list):
                raise CommandError('Файл должен содержать список ингредиентов')
            
            total_ingredients = len(ingredients_data)
            self.stdout.write(f'Обнаружено {total_ingredients} ингредиентов в файле')
            
            existing_ingredients = self.get_existing_ingredients()
            self.stdout.write(f'В базе данных уже есть {len(existing_ingredients)} ингредиентов')
            
            with transaction.atomic():
                created_count = self.create_new_ingredients(ingredients_data, existing_ingredients, batch_size)
            
            self.stdout.write(
                self.style.SUCCESS(f'Успешно импортировано {created_count} новых ингредиентов из {total_ingredients}')
            )
            
        except Exception as e:
            raise CommandError(f'Ошибка при импорте ингредиентов: {e}')
    
    def get_existing_ingredients(self):
        existing = defaultdict(set)
        for item in Ingredient.objects.all().values('name', 'measurement_unit'):
            key = (item['name'], item['measurement_unit'])
            existing[key] = True
        return existing
    
    def create_new_ingredients(self, ingredients_data, existing_ingredients, batch_size):
        new_ingredients = []
        created_count = 0
        errors = 0
        
        for ingredient in ingredients_data:
            try:
                name = ingredient['name']
                measurement_unit = ingredient['measurement_unit']
                
                if (name, measurement_unit) not in existing_ingredients:
                    new_ingredients.append(Ingredient(
                        name=name,
                        measurement_unit=measurement_unit
                    ))
                    created_count += 1
                
                if len(new_ingredients) >= batch_size:
                    Ingredient.objects.bulk_create(new_ingredients, ignore_conflicts=True)
                    self.stdout.write(f'Создано {len(new_ingredients)} ингредиентов...')
                    new_ingredients = []
            
            except KeyError as e:
                errors += 1
                if errors <= 10: 
                    self.stderr.write(f'Ошибка в данных: отсутствует поле {e}')
        

        if new_ingredients:
            Ingredient.objects.bulk_create(new_ingredients, ignore_conflicts=True)
            self.stdout.write(f'Создано {len(new_ingredients)} ингредиентов...')
        
        return created_count