#!/bin/bash

echo "🔧 Настройка Video Transcriber Service для PyCharm"
echo "=================================================="

# Проверяем, что мы в правильной директории
if [ ! -f "app.py" ]; then
    echo "❌ Ошибка: Запустите скрипт из директории video-transcriber-service"
    exit 1
fi

echo "✅ Директория проекта найдена"

# Проверяем Git репозиторий
if [ ! -d ".git" ]; then
    echo "❌ Ошибка: Git репозиторий не найден"
    exit 1
fi

echo "✅ Git репозиторий найден"

# Проверяем статус Git
git_status=$(git status --porcelain)
if [ -n "$git_status" ]; then
    echo "⚠️  Есть незакоммиченные изменения:"
    echo "$git_status"
    echo "Хотите закоммитить их? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        git add .
        git commit -m "Update project configuration"
        echo "✅ Изменения закоммичены"
    fi
fi

echo "✅ Git репозиторий чистый"

echo ""
echo "📋 ИНСТРУКЦИИ ДЛЯ PYCHARM:"
echo "=========================="
echo "1. Закройте PyCharm полностью"
echo "2. Очистите кэш:"
echo "   rm -rf ~/.cache/JetBrains/PyCharm*"
echo "   rm -rf ~/.config/JetBrains/PyCharm*"
echo ""
echo "3. Откройте PyCharm и создайте новый проект:"
echo "   File -> New Project"
echo "   Location: $(pwd)"
echo "   Interpreter: Existing interpreter (Python 3.10)"
echo "   НЕ создавайте новый Git репозиторий"
echo ""
echo "4. Настройте VCS:"
echo "   VCS -> Enable Version Control Integration -> Git"
echo ""
echo "5. Добавьте remote origin:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/video-transcriber-service.git"
echo ""
echo "6. Проверьте статус Git в PyCharm:"
echo "   VCS -> Git -> Show Git Log"
echo ""
echo "🎉 Проект готов для загрузки на GitHub!"
echo "=================================================="
