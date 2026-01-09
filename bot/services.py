import asyncio
import os
import tempfile
import logging
from yandex_music import Client
from yandex_music.exceptions import UnauthorizedError, TimedOutError
import requests
from pydub import AudioSegment
import urllib.parse

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
    except (UnauthorizedError, TimedOutError) as e:
        logger.warning(f"Yandex Music client init error: {e}")
        yandex_client = Client().init()
    except Exception as e:
        logger.error(f"Unexpected error initializing Yandex client: {e}")
        yandex_client = None

async def download_yandex_music_track(url: str):
    """
    Скачивание трека из Яндекс.Музыки
    Возвращает словарь с результатом
    """
    try:
        # Инициализация клиента при необходимости
        if yandex_client is None:
            from bot.main import os as os_module
            token = os_module.getenv("YANDEX_MUSIC_TOKEN")
            init_yandex_client(token)
        
        if yandex_client is None:
            return {"success": False, "error": "Не удалось инициализировать клиент Яндекс.Музыки"}
        
        # Парсинг ID трека из URL
        track_id = extract_track_id_from_url(url)
        if not track_id:
            return {"success": False, "error": "Не удалось извлечь ID трека из ссылки"}
        
        logger.info(f"Processing track ID: {track_id}")
        
        # Получение информации о треке с обработкой ошибки совместимости
        try:
            # Способ 1: Используем новый API
            track_short = await asyncio.to_thread(lambda: yandex_client.tracks([track_id]))
            if track_short and len(track_short) > 0:
                track = track_short[0]
            else:
                return {"success": False, "error": "Трек не найден"}
                
        except TypeError as e:
            if "common_period_duration" in str(e):
                # Ошибка совместимости - пробуем альтернативный способ
                logger.warning("Using alternative method due to compatibility issue")
                try:
                    # Получаем трек через поиск
                    search_result = await asyncio.to_thread(
                        lambda: yandex_client.search(f"trackid:{track_id}", type_="track")
                    )
                    if search_result and search_result.tracks and search_result.tracks.results:
                        track = search_result.tracks.results[0]
                    else:
                        return {"success": False, "error": "Трек не найден (альтернативный метод)"}
                except Exception as alt_e:
                    logger.error(f"Alternative method error: {alt_e}")
                    return {"success": False, "error": f"Ошибка получения трека: {alt_e}"}
            else:
                return {"success": False, "error": f"Ошибка получения трека: {e}"}
        except Exception as e:
            logger.error(f"Track fetch error: {e}")
            return {"success": False, "error": f"Ошибка получения трека: {e}"}
        
        # Получение названия и исполнителя
        try:
            title = track.title or "Без названия"
            if hasattr(track, 'artists') and track.artists:
                artist = track.artists[0].name if hasattr(track.artists[0], 'name') else "Неизвестный исполнитель"
            else:
                artist = "Неизвестный исполнитель"
        except Exception as e:
            logger.warning(f"Error getting metadata: {e}")
            title = "Без названия"
            artist = "Неизвестный исполнитель"
        
        # Получение ссылки на скачивание
        try:
            download_info = await asyncio.to_thread(
                lambda: track.get_download_info(get_direct_links=True)
            )
            
            if not download_info:
                return {"success": False, "error": "Не удалось получить информацию для скачивания"}
            
            # Выбор наилучшего качества
            best_quality = max(download_info, key=lambda x: getattr(x, 'bitrate_in_kbps', 0))
            direct_link = await asyncio.to_thread(lambda: best_quality.get_direct_link())
            
            if not direct_link:
                return {"success": False, "error": "Не удалось получить прямую ссылку"}
                
        except Exception as e:
            logger.error(f"Download info error: {e}")
            return {"success": False, "error": f"Ошибка получения информации для скачивания: {e}"}
        
        # Создание временного файла
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        # Скачивание файла
        download_success = await download_file(direct_link, temp_path)
        if not download_success:
            os.remove(temp_path)
            return {"success": False, "error": "Ошибка скачивания файла"}
        
        # Проверка размера файла
        if os.path.getsize(temp_path) < 1024:  # Меньше 1KB
            os.remove(temp_path)
            return {"success": False, "error": "Скачанный файл слишком мал (возможно, ошибка доступа)"}
        
        return {
            "success": True,
            "file_path": temp_path,
            "title": title,
            "artist": artist,
            "duration": getattr(track, 'duration_ms', 0) // 1000 if hasattr(track, 'duration_ms') else 0
        }
        
    except Exception as e:
        logger.error(f"Error downloading track: {e}", exc_info=True)
        return {"success": False, "error": f"Внутренняя ошибка: {str(e)}"}

def extract_track_id_from_url(url: str) -> str:
    """Извлечение ID трека из URL"""
    import re
    
    # Удаляем параметры запроса (все что после ?)
    url_without_params = url.split('?')[0]
    
    # Паттерны для разных форматов ссылок
    patterns = [
        r'track/(\d+)',
        r'album/\d+/track/(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_without_params)
        if match:
            return match.group(1)
    
    return None

async def download_file(url: str, filepath: str):
    """Асинхронная загрузка файла"""
    try:
        loop = asyncio.get_event_loop()
        
        def _download():
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            return True
            
        return await loop.run_in_executor(None, _download)
    except Exception as e:
        logger.error(f"Download error: {e}")
        return False