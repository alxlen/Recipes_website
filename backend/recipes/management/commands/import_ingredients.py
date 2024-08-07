import csv
import os

from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает данные из файла .csv'

    def handle(self, *args, **options):
        file_path = './data/Ingredients.csv'

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
            return

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

                    if Ingredient.objects.filter(
                            name=row_data['name'],
                            measurement_unit=row_data['measurement_unit']
                    ).exists():
                        self.stdout.write(
                            self.style.WARNING(
                                f'Ингредиент уже существует: '
                                f'{row_data["name"]} '
                                f'({row_data["measurement_unit"]})'))
                        continue

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
                self.style.ERROR(f'Неизвестная ошибка: {e}'))
