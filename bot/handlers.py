from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart, Command
import os
from bot.services import download_yandex_music_track
from bot.utils import validate_yandex_music_url

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🎵 Привет! Я бот для скачивания музыки из Яндекс.Музыки.\n\n"
        "Отправь мне ссылку на трек из Яндекс.Музыки, и я скачаю его для тебя.\n\n"
        "Примеры ссылок:\n"
        "• https://music.yandex.ru/album/1234567/track/7654321\n"
        "• https://music.yandex.ru/track/1234567\n\n"
        "⚠️ Используйте бота только для скачивания музыки, на которую у вас есть права!"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 Помощь по использованию бота:\n\n"
        "1. Скопируйте ссылку на трек из Яндекс.Музыки\n"
        "2. Отправьте ссылку мне\n"
        "3. Я скачаю и отправлю вам трек\n\n"
        "Поддерживаемые форматы ссылок:\n"
        "- Прямая ссылка на трек\n"
        "- Ссылка на трек в альбоме\n\n"
        "❓ Проблемы? Проверьте:\n"
        "• Ссылка действительна\n"
        "• Трек доступен в вашем регионе\n"
        "• У вас есть Яндекс.Музыка токен (необязательно, но желательно)"
    )

@router.message(F.text)
async def handle_url(message: Message):
    url = message.text.strip()
    
    # Проверка валидности ссылки
    if not validate_yandex_music_url(url):
        await message.answer("❌ Пожалуйста, отправьте валидную ссылку Яндекс.Музыки.")
        return
    
    # Отправка статуса обработки
    status_msg = await message.answer("⏳ Обрабатываю ссылку...")
    
    try:
        # Скачивание трека
        result = await download_yandex_music_track(url)
        
        if result["success"]:
            await status_msg.edit_text("✅ Трек скачан! Отправляю...")
            
            # Отправка аудиофайла
            audio_file = FSInputFile(result["file_path"])
            await message.answer_audio(
                audio=audio_file,
                title=result["title"],
                performer=result["artist"],
                caption=f"🎵 {result['artist']} - {result['title']}"
            )
            
            # Удаление временного файла
            os.remove(result["file_path"])
            await status_msg.delete()
            
        else:
            await status_msg.edit_text(f"❌ Ошибка: {result['error']}")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Произошла ошибка: {str(e)}")