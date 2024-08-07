import csv
import os

from django.core.management import BaseCommand
from django.db import connection, transaction

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает данные из файла .csv'

    def handle(self, *args, **options):
        file_path = './data/Ingredients.csv'

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
            return

        self.stdout.write(self.style.NOTICE('Очистка базы данных'))

        Ingredient.objects.all().delete()

        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM sqlite_sequence WHERE name='recipes_ingredient';")

        self.stdout.write(self.style.NOTICE('Загрузка данных'))

        ingredients = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = ['name', 'measurement_unit']

                for row in reader:
                    if len(row) != len(headers):
                        self.stdout.write(
                            self.style.ERROR(f'Несоответствие формата: {row}'))
                        continue

                    row_data = dict(zip(headers, row))
                    ingredients.append(Ingredient(
                        name=row_data['name'],
                        measurement_unit=row_data['measurement_unit']
                    ))

            Ingredient.objects.bulk_create(ingredients)

            self.stdout.write(self.style.SUCCESS('Импорт завершен'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
        except csv.Error as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при чтении CSV файла: {e}'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Произошла непредвиденная ошибка: {e}'))
