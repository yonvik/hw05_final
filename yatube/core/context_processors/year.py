from datetime import datetime


def year(request):
    now = datetime.now().year
    """Добавляет переменную с текущим годом."""
    return {
        'year': now,
    }
