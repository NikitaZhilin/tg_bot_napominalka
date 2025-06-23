#!/bin/bash
echo "📦 Добавляем файлы..."
git add README.md app.py

echo "📝 Коммитим..."
git commit -m '✅ Автообновление: README и app.py'

echo "🚀 Пушим в GitHub..."
git push origin main
