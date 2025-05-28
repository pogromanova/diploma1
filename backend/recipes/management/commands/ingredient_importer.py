import os
import json
from collections import defaultdict

from django.db import transaction
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient


class Command(BaseCommand):

    help = 'Импорт ингредиентов'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_path', 
            nargs='?',
            type=str, 
            help='Путь к JSON-файлу с данными ингредиентов'
        )
        parser.add_argument(
            '--batch-size',
            dest='chunk_size',
            type=int,
            default=5000,
            help='Количество записей для одновременной вставки в БД'
        )

    def handle(self, *args, **options):
        try:
            chunk_size = options.get('chunk_size')
            source_path = options.get('json_path')
            
            if not source_path:
                source_path = os.getenv('INGREDIENTS_FILE_PATH', '/app/data/ingredients.json')
            
            source_path = self._find_data_file(source_path)
                    
            self.stdout.write(f'Начинается загрузка данных из {source_path}')
            ingredient_list = self._load_json_data(source_path)
            
            total_items = len(ingredient_list)
            self.stdout.write(f'В файле найдено {total_items} записей')
            
            existing_items = self._fetch_existing_ingredients()
            self.stdout.write(f'В базе данных уже имеется {len(existing_items)} ингредиентов')
            
            with transaction.atomic():
                imported_count = self._process_ingredients(
                    ingredient_list, 
                    existing_items, 
                    chunk_size
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Импорт завершен: добавлено {imported_count} из {total_items} ингредиентов'
                )
            )
            
        except Exception as error:
            raise CommandError(f'Ошибка при импорте: {error}')
    
    def _find_data_file(self, primary_path):
        if os.path.exists(primary_path):
            return primary_path
        
        alternative_locations = [
            '/app/data/ingredients.json',
            '/data/ingredients.json',
            '/app/data/ingredients.csv',
            '/data/ingredients.csv'
        ]
        
        for location in alternative_locations:
            if os.path.exists(location):
                self.stdout.write(f'Файл обнаружен в альтернативном месте: {location}')
                return location
        
        searched_paths = [primary_path] + alternative_locations
        raise CommandError(f'Не удалось найти файл данных. Проверенные пути: {", ".join(searched_paths)}')
    
    def _load_json_data(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        
        if not isinstance(data, list):
            raise CommandError('Некорректный формат данных: ожидается список ингредиентов')
            
        return data
    
    def _fetch_existing_ingredients(self):
        ingredients_dict = defaultdict(bool)
        
        for item in Ingredient.objects.all().values('name', 'measurement_unit'):
            unique_key = (item['name'], item['measurement_unit'])
            ingredients_dict[unique_key] = True
            
        return ingredients_dict
    
    def _process_ingredients(self, ingredients_list, existing_dict, batch_size):
        pending_items = []
        added_count = 0
        error_count = 0
        
        for item in ingredients_list:
            try:
                ingredient_name = item['name']
                ingredient_unit = item['measurement_unit']
                
                if not existing_dict.get((ingredient_name, ingredient_unit)):
                    pending_items.append(
                        Ingredient(
                            name=ingredient_name,
                            measurement_unit=ingredient_unit
                        )
                    )
                    added_count += 1
                
                if len(pending_items) >= batch_size:
                    self._save_batch(pending_items)
                    pending_items = []
            
            except KeyError as key_error:
                error_count += 1
                if error_count <= 10:  
                    self.stderr.write(f'Отсутствует обязательное поле: {key_error}')
        
        if pending_items:
            self._save_batch(pending_items)
        
        return added_count
    
    def _save_batch(self, items):
        Ingredient.objects.bulk_create(items, ignore_conflicts=True)
        self.stdout.write(f'Добавлено {len(items)} ингредиентов в базу данных')