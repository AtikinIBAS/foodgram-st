import json
import os

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загружает ингредиенты из файла JSON в базу данных."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="data/ingredients.json",
            help="Путь к JSON-файлу с ингредиентами",
        )

    def handle(self, *args, **options):
        file_path = options["path"]

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"Файл не найден: {file_path}"))
            return

        with open(file_path, encoding="utf-8") as file:
            try:
                ingredients_data = json.load(file)
            except json.JSONDecodeError as error:
                self.stderr.write(self.style.ERROR(f"JSON ошибка: {error}"))
                return

        for item in ingredients_data:
            name = item["name"]
            unit = item["measurement_unit"]
            if Ingredient.objects.filter(name=name, measurement_unit=unit).exists():
                self.stdout.write(
                    self.style.WARNING(f"{name} уже существует, пропускаем.")
                )
            else:
                # Add the new ingredient
                Ingredient.objects.create(name=name, measurement_unit=unit)
                self.stdout.write(self.style.SUCCESS(f"Добавлено: {name}"))
