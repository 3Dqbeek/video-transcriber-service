#!/usr/bin/env python3
"""
Скрипт проверки установки Video Transcriber Service
"""

import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    print("🐍 Проверка Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - требуется 3.8+")
        return False

def check_system_dependencies():
    """Проверка системных зависимостей"""
    print("\n🔧 Проверка системных зависимостей...")
    
    dependencies = {
        'git': 'git --version',
        'ffmpeg': 'ffmpeg -version'
    }
    
    all_ok = True
    for name, command in dependencies.items():
        try:
            result = subprocess.run(command.split(), capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {name} - OK")
            else:
                print(f"❌ {name} - не найден")
                all_ok = False
        except FileNotFoundError:
            print(f"❌ {name} - не найден")
            all_ok = False
    
    return all_ok

def check_tone_framework():
    """Проверка T-one framework"""
    print("\n🎤 Проверка T-one framework...")
    
    try:
        import tone
        print("✅ T-one framework - OK")
        return True
    except ImportError:
        print("❌ T-one framework - не найден")
        print("💡 Установите: git clone https://github.com/voicekit-team/T-one.git && cd T-one && pip install -e .")
        return False

def check_python_dependencies():
    """Проверка Python зависимостей"""
    print("\n📦 Проверка Python зависимостей...")
    
    dependencies = [
        'fastapi',
        'uvicorn',
        'yt_dlp',
        'moviepy',
        'librosa',
        'soundfile',
        'numpy'
    ]
    
    all_ok = True
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep} - OK")
        except ImportError:
            print(f"❌ {dep} - не найден")
            all_ok = False
    
    return all_ok

def check_service_files():
    """Проверка файлов сервиса"""
    print("\n📁 Проверка файлов сервиса...")
    
    required_files = [
        'app.py',
        'streaming_video_transcriber.py',
        'run_service.py',
        'requirements.txt',
        'README.md'
    ]
    
    all_ok = True
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file} - OK")
        else:
            print(f"❌ {file} - не найден")
            all_ok = False
    
    return all_ok

def main():
    print("🔍 Video Transcriber Service - Проверка установки")
    print("=" * 60)
    
    checks = [
        check_python_version(),
        check_system_dependencies(),
        check_tone_framework(),
        check_python_dependencies(),
        check_service_files()
    ]
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ")
    print("=" * 60)
    
    if all(checks):
        print("🎉 Все проверки пройдены успешно!")
        print("🚀 Сервис готов к запуску:")
        print("   python3 run_service.py")
        print("🌐 Веб-интерфейс: http://localhost:8086")
    else:
        print("❌ Обнаружены проблемы с установкой")
        print("💡 Следуйте инструкциям в README.md для устранения проблем")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
