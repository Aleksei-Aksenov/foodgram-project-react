from django.http import HttpResponse


def get_shopping_list(ingredients_list):
    """Метод для скачивания списка покупок"""
    buy_list = []
    for item in ingredients_list:
        buy_list.append(f'{item["ingredient__name"]} - {item["amount"]} '
                        f'{item["ingredient__measurement_unit"]} \n')
    filename = "shopping_list.txt"
    response = HttpResponse(buy_list, content_type='text/plain,charset=utf8')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response
