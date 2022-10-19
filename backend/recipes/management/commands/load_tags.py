from django.core.management import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):
    help = "Создание тегов в БД."

    def handle(self, *args, **kwargs):
        data = [
            {"name": "завтрак", "color": "#90EE90", "slug": "breakfast"},
            {"name": "обед", "color": "#49B64E", "slug": "dinner"},
            {"name": "полдник", "color": "#40E0D0", "slug": "lunch"},
            {"name": "ужин", "color": "#8775D2", "slug": "supper"},
            {"name": "перекус", "color": "#FFD700", "slug": "snack"},
        ]
        Tag.objects.bulk_create(Tag(**tag) for tag in data)
        self.stdout.write(
            self.style.SUCCESS("***Теги успешно загружены!***")
        )
