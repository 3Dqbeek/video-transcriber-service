#!/usr/bin/env python3
"""
Скрипт запуска Video Transcriber Service
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    print("🚀 Video Transcriber Service")
    print("=" * 50)
    print("Функциональность:")
    print("✅ Транскрибация видео из URL (Rutube, YouTube и др.)")
    print("✅ Транскрибация локальных видео файлов")
    print("✅ Определение ролей говорящих (Operator/Customer)")
    print("✅ Экспорт в TXT и JSON форматах")
    print("✅ Современный веб-интерфейс")
    print("✅ Отслеживание задач в реальном времени")
    print("=" * 50)
    print("🌐 Сервер будет доступен по адресу: http://0.0.0.0:8086")
    print("📱 Веб-интерфейс: http://localhost:8086")
    print("💡 Для остановки сервера нажмите Ctrl+C")
    print("=" * 50)
    
    # Проверяем, что мы в правильной директории
    if not Path("app.py").exists():
        print("❌ Ошибка: app.py не найден в текущей директории")
        print("💡 Убедитесь, что вы находитесь в директории video_transcriber_service")
        sys.exit(1)
    
    # Создаем директорию для транскрипций
    transcriptions_dir = Path("transcriptions")
    transcriptions_dir.mkdir(exist_ok=True)
    print(f"📁 Директория транскрипций: {transcriptions_dir.absolute()}")
    
    try:
        # Запускаем сервер
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8086,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
