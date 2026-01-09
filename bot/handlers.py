from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart, Command
import os
from bot.services import download_yandex_music_track
from bot.utils import validate_yandex_music_url, clean_url

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🎵 Привет! Я бот для скачивания музыки из Яндекс.Музыки.\n\n"
        "Отправь мне ссылку на трек из Яндекс.Музыки, и я скачаю его для тебя.\n\n"
        "📋 Поддерживаемые форматы:\n"
        "• https://music.yandex.ru/album/1234567/track/7654321\n"
        "• https://music.yandex.ru/track/1234567\n"
        "• https://music.yandex.com/album/1234567/track/7654321\n\n"
        "Ссылки могут содержать параметры (например, utm_source), я их проигнорирую.\n\n"
        "⚠️ Используйте бота только для скачивания музыки, на которую у вас есть права!"
    )

@router.message(F.text)
async def handle_url(message: Message):
    url = message.text.strip()
    
    # Очищаем URL от параметров отслеживания
    cleaned_url = clean_url(url)
    
    # Проверка валидности ссылки
    if not validate_yandex_music_url(cleaned_url):
        await message.answer(
            "❌ Пожалуйста, отправьте валидную ссылку Яндекс.Музыки.\n\n"
            "Примеры правильных ссылок:\n"
            "• https://music.yandex.ru/album/36147972/track/138015169\n"
            "• https://music.yandex.ru/track/138015169"
        )
        return
    
    # Отправка статуса обработки
    status_msg = await message.answer("⏳ Обрабатываю ссылку...")
    
    try:
        # Скачивание трека
        result = await download_yandex_music_track(cleaned_url)
        
        if result["success"]:
            await status_msg.edit_text("✅ Трек скачан! Отправляю...")
            
            # Отправка аудиофайла
            audio_file = FSInputFile(result["file_path"])
            
            # Создаем подпись
            caption = f"🎵 {result['artist']} - {result['title']}"
            if result['duration'] > 0:
                from bot.utils import format_duration
                caption += f"\n⏱ Длительность: {format_duration(result['duration'])}"
            
            await message.answer_audio(
                audio=audio_file,
                title=result["title"],
                performer=result["artist"],
                caption=caption
            )
            
            # Удаление временного файла
            try:
                os.remove(result["file_path"])
            except:
                pass
            
            await status_msg.delete()
            
        else:
            error_msg = result['error']
            advice = ""
            
            if "не найден" in error_msg.lower():
                advice = "\n\n💡 Проверьте, что трек доступен в вашем регионе и вы правильно скопировали ссылку."
            elif "токен" in error_msg.lower():
                advice = "\n\n💡 Попробуйте обновить токен Яндекс.Музыки в настройках бота."
            
            await status_msg.edit_text(f"❌ {error_msg}{advice}")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Произошла неожиданная ошибка: {str(e)}")