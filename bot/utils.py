import re

def validate_yandex_music_url(url: str) -> bool:
    """Проверка валидности ссылки Яндекс.Музыки"""
    patterns = [
        r'^https?://music\.yandex\.(ru|com)/track/\d+',
        r'^https?://music\.yandex\.(ru|com)/album/\d+/track/\d+',
        r'^https?://music\.yandex\.(ru|com)/users/[\w-]+/playlists/\d+',
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    
    return False

def format_duration(seconds: int) -> str:
    """Форматирование длительности в читаемый вид"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"