#!/bin/bash

echo "🚀 Публикация Video Transcriber Service на GitHub"
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
        echo "Введите сообщение коммита:"
        read -r commit_message
        git commit -m "$commit_message"
        echo "✅ Изменения закоммичены"
    fi
fi

echo "✅ Git репозиторий чистый"

# Проверяем наличие remote
if ! git remote | grep -q origin; then
    echo ""
    echo "📋 НАСТРОЙКА REMOTE REPOSITORY:"
    echo "================================"
    echo "1. Создайте новый репозиторий на GitHub:"
    echo "   - Перейдите на https://github.com/new"
    echo "   - Repository name: video-transcriber-service"
    echo "   - Description: Modern web service for video transcription with speaker role detection"
    echo "   - Visibility: Public"
    echo "   - НЕ добавляйте README, LICENSE или .gitignore (уже есть)"
    echo "   - Нажмите 'Create repository'"
    echo ""
    echo "2. После создания репозитория выполните:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/video-transcriber-service.git"
    echo "   (Замените YOUR_USERNAME на ваш GitHub username)"
    echo ""
    echo "3. Затем запустите этот скрипт снова"
    exit 0
fi

# Проверяем remote URL
remote_url=$(git remote get-url origin)
echo "✅ Remote origin настроен: $remote_url"

# Проверяем наличие тега v1.0.0
if ! git tag | grep -q "v1.0.0"; then
    echo "📌 Создание тега v1.0.0..."
    git tag -a v1.0.0 -m "Release version 1.0.0 - Initial release with full features"
    echo "✅ Тег v1.0.0 создан"
fi

echo ""
echo "📤 ПУБЛИКАЦИЯ НА GITHUB:"
echo "========================="
echo "Выполняются команды для публикации..."
echo ""

# Push основной ветки
echo "1. Отправка основной ветки (main)..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ Основная ветка отправлена"
else
    echo "❌ Ошибка при отправке основной ветки"
    exit 1
fi

# Push тегов
echo "2. Отправка тегов..."
git push origin --tags

if [ $? -eq 0 ]; then
    echo "✅ Теги отправлены"
else
    echo "❌ Ошибка при отправке тегов"
    exit 1
fi

echo ""
echo "🎉 ПРОЕКТ УСПЕШНО ОПУБЛИКОВАН НА GITHUB!"
echo "=========================================="
echo "Репозиторий: $remote_url"
echo "Версия: v1.0.0"
echo "Автор: Vasiliy Dautov"
echo "Лицензия: MIT License"
echo ""
echo "📋 Следующие шаги:"
echo "1. Перейдите на GitHub и проверьте репозиторий"
echo "2. Создайте Release на GitHub:"
echo "   - Перейдите в раздел Releases"
echo "   - Нажмите 'Create a new release'"
echo "   - Выберите тег v1.0.0"
echo "   - Заголовок: Video Transcriber Service v1.0.0"
echo "   - Описание: Скопируйте из CHANGELOG.md"
echo "   - Нажмите 'Publish release'"
echo ""
echo "🎊 Поздравляем! Ваш проект теперь публичен на GitHub!"
