import re

def validate_yandex_music_url(url: str) -> bool:
    """Проверка валидности ссылки Яндекс.Музыки"""
    # Удаляем параметры запроса для проверки
    url_without_params = url.split('?')[0] if '?' in url else url
    
    patterns = [
        r'^https?://music\.yandex\.(ru|com)/track/\d+',
        r'^https?://music\.yandex\.(ru|com)/album/\d+/track/\d+',
        r'^https?://music\.yandex\.(ru|com)/users/[\w-]+/playlists/\d+',
    ]
    
    for pattern in patterns:
        if re.match(pattern, url_without_params):
            return True
    
    return False

def format_duration(seconds: int) -> str:
    """Форматирование длительности в читаемый вид"""
    if seconds <= 0:
        return "0:00"
    
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

def clean_url(url: str) -> str:
    """Очистка URL от параметров отслеживания"""
    # Удаляем параметры utm_ и другие трекеры
    parsed = re.sub(r'[?&](utm_[^&]+|ref=[^&]+|from=[^&]+)', '', url)
    # Удаляем оставшиеся ? или & в конце
    parsed = re.sub(r'[?&]$', '', parsed)
    return parsed if parsed else url