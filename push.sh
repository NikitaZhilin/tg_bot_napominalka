#!/bin/bash

# Проверка наличия изменений
if git diff --quiet && git diff --cached --quiet; then
  echo "🟢 Нет изменений для коммита. Всё актуально."
  exit 0
fi

echo "🔍 Добавляем все изменения..."
git add .

echo "📝 Коммитим изменения..."
git commit -m "🚀 deploy: финальные правки и деплой на Render"

echo "⬆️ Пушим в ветку main..."
git push origin main

echo "✅ Готово!"
