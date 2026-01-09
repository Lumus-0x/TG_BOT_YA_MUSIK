import asyncio
import os
import tempfile
from yandex_music import Client
from yandex_music.exceptions import UnauthorizedError
import requests
from pydub import AudioSegment
import ffmpeg
import logging

logger = logging.getLogger(__name__)

# Инициализация клиента Яндекс.Музыки
yandex_client = None

def init_yandex_client(token: str = None):
    """Инициализация клиента Яндекс.Музыки"""
    global yandex_client
    try:
        if token:
            yandex_client = Client(token).init()
            logger.info("Yandex Music client initialized with token")
        else:
            yandex_client = Client().init()
            logger.info("Yandex Music client initialized without token")
    except UnauthorizedError:
        logger.warning("Invalid Yandex Music token")
        yandex_client = Client().init()

async def download_yandex_music_track(url: str):
    """
    Скачивание трека из Яндекс.Музыки
    Возвращает словарь с результатом
    """
    try:
        # Инициализация клиента при необходимости
        if yandex_client is None:
            from bot.main import os
            token = os.getenv("YANDEX_MUSIC_TOKEN")
            init_yandex_client(token)
        
        # Парсинг ID трека из URL
        track_id = extract_track_id_from_url(url)
        if not track_id:
            return {"success": False, "error": "Не удалось извлечь ID трека из ссылки"}
        
        # Получение информации о треке
        track = await asyncio.to_thread(lambda: yandex_client.tracks([track_id])[0])
        
        if not track:
            return {"success": False, "error": "Трек не найден"}
        
        # Получение ссылки на скачивание
        download_info = await asyncio.to_thread(lambda: track.get_download_info(get_direct_links=True))
        
        if not download_info:
            return {"success": False, "error": "Не удалось получить информацию для скачивания"}
        
        # Выбор наилучшего качества
        best_quality = max(download_info, key=lambda x: x.bitrate_in_kbps)
        direct_link = await asyncio.to_thread(lambda: best_quality.get_direct_link())
        
        if not direct_link:
            return {"success": False, "error": "Не удалось получить прямую ссылку"}
        
        # Создание временного файла
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        # Скачивание файла
        await download_file(direct_link, temp_path)
        
        # Конвертация в MP3 (если нужно)
        if not temp_path.endswith('.mp3'):
            converted_path = temp_path.replace('.', '_converted.')
            await convert_to_mp3(temp_path, converted_path)
            os.remove(temp_path)
            temp_path = converted_path
        
        return {
            "success": True,
            "file_path": temp_path,
            "title": track.title,
            "artist": track.artists[0].name if track.artists else "Неизвестный исполнитель",
            "duration": track.duration_ms // 1000
        }
        
    except Exception as e:
        logger.error(f"Error downloading track: {e}")
        return {"success": False, "error": str(e)}

def extract_track_id_from_url(url: str) -> str:
    """Извлечение ID трека из URL"""
    import re
    
    # Паттерны для разных форматов ссылок
    patterns = [
        r'track/(\d+)',
        r'album/\d+/track/(\d+)',
        r'track_id=(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

async def download_file(url: str, filepath: str):
    """Асинхронная загрузка файла"""
    loop = asyncio.get_event_loop()
    
    def _download():
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    
    await loop.run_in_executor(None, _download)

async def convert_to_mp3(input_path: str, output_path: str):
    """Конвертация аудио в MP3"""
    loop = asyncio.get_event_loop()
    
    def _convert():
        # Используем pydub для конвертации
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="mp3", bitrate="192k")
    
    await loop.run_in_executor(None, _convert)