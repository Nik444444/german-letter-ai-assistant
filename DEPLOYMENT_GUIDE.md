# 🚀 Полное руководство по развертыванию German Letter AI Assistant

## 📋 Обзор

Это приложение состоит из двух частей:
- **Frontend (React)** → развертывается на Netlify
- **Backend (FastAPI)** → развертывается на Render/Railway

## 🔑 Шаг 1: Получение API ключей

### Google Gemini API (ОБЯЗАТЕЛЬНО)
1. Перейдите на [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Войдите в аккаунт Google
3. Нажмите **"Create API Key"**
4. Выберите проект или создайте новый
5. Скопируйте ключ - он понадобится для бэкенда

⚠️ **Важно**: Без этого ключа приложение не будет работать!

## 🚀 Шаг 2: Развертывание бэкенда на Render

### 2.1 Создание аккаунта
1. Перейдите на [render.com](https://render.com)
2. Создайте аккаунт через GitHub

### 2.2 Развертывание
1. Нажмите **"New +"** → **"Web Service"**
2. Подключите ваш GitHub репозиторий
3. Настройки:
   - **Name**: `german-letter-ai-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`

### 2.3 Переменные окружения
В разделе **Environment** добавьте:
- **Key**: `GEMINI_API_KEY`
- **Value**: `ваш_ключ_от_gemini`

### 2.4 Дополнительные настройки
- **Instance Type**: Free (для начала)
- **Auto-Deploy**: Yes
- **Region**: Frankfurt (ближе к Европе)

## 🌐 Шаг 3: Развертывание фронтенда на Netlify

### 3.1 Создание аккаунта
1. Перейдите на [netlify.com](https://netlify.com)
2. Создайте аккаунт через GitHub

### 3.2 Развертывание
1. Нажмите **"New site from Git"**
2. Выберите GitHub и ваш репозиторий
3. Настройки:
   - **Branch**: `main`
   - **Build command**: `cd frontend && yarn install && yarn build`
   - **Publish directory**: `frontend/build`
4. Нажмите **"Deploy site"**

### 3.3 Переменные окружения
1. Перейдите в **Site settings** → **Environment variables**
2. Добавьте:
   - **Key**: `REACT_APP_BACKEND_URL`
   - **Value**: `https://your-backend-name.onrender.com` (URL из Render)

## 🔧 Шаг 4: Настройка системных зависимостей

### 4.1 Tesseract OCR на Render
Добавьте в корень проекта файл `aptfile`:
```
tesseract-ocr
tesseract-ocr-deu
tesseract-ocr-eng
```

### 4.2 Обновление requirements.txt
Убедитесь, что в `backend/requirements.txt` есть:
```
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
python-dotenv==1.0.0
google-generativeai==0.3.2
Pillow==10.1.0
pytesseract==0.3.10
PyPDF2==3.0.1
PyMuPDF==1.23.8
requests==2.31.0
```

## ✅ Шаг 5: Проверка работы

### 5.1 Тестирование бэкенда
1. Откройте `https://your-backend-url.onrender.com/docs`
2. Должна открыться документация FastAPI
3. Попробуйте эндпоинт `/api/health`

### 5.2 Тестирование фронтенда
1. Откройте ваш сайт на Netlify
2. Попробуйте загрузить тестовый файл
3. Проверьте консоль браузера на ошибки

## 🔍 Шаг 6: Устранение проблем

### Проблема: Ошибка CORS
**Решение**: Убедитесь, что в `backend/server.py` есть:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Проблема: Tesseract не найден
**Решение**: Создайте файл `aptfile` в корне проекта:
```
tesseract-ocr
tesseract-ocr-deu
tesseract-ocr-eng
```

### Проблема: Нет ответа от API
**Решение**: Проверьте:
1. Правильность Gemini API ключа
2. Лимиты API (возможно превышены)
3. Логи в Render Dashboard

### Проблема: Большие файлы
**Решение**: Добавьте ограничения в настройки Render:
- Max request size: 10MB
- Timeout: 30 секунд

## 📱 Шаг 7: Telegram Bot (опционально)

### 7.1 Создание бота
1. Найдите @BotFather в Telegram
2. Создайте нового бота командой `/newbot`
3. Получите token

### 7.2 Настройка Web App
1. Используйте команду `/newapp`
2. Укажите URL вашего Netlify сайта
3. Добавьте описание и фото

## 🎯 Производительность

### Оптимизация фронтенда
- Включите сжатие в Netlify
- Используйте CDN для статических файлов
- Минимизируйте размеры изображений

### Оптимизация бэкенда
- Используйте кеширование для часто используемых запросов
- Настройте пул соединений
- Добавьте rate limiting

## 📊 Мониторинг

### Netlify Analytics
- Включите в настройках сайта
- Отслеживайте трафик и ошибки

### Render Monitoring
- Используйте встроенные метрики
- Настройте уведомления

## 🔒 Безопасность

### API ключи
- Никогда не коммитьте ключи в репозиторий
- Используйте только переменные окружения
- Регулярно меняйте ключи

### CORS
- Для продакшена ограничьте домены
- Не используйте "*" в продакшене

## 💰 Стоимость

### Бесплатные лимиты
- **Netlify**: 100GB bandwidth/месяц
- **Render**: 750 часов/месяц
- **Gemini API**: см. актуальные лимиты Google

### Масштабирование
- При росте нагрузки переходите на платные планы
- Рассмотрите использование CDN
- Добавьте кеширование

## 🆘 Поддержка

### Логи
- **Netlify**: Deploy logs и Function logs
- **Render**: Runtime logs в dashboard
- **Browser**: Developer Tools → Console

### Сообщество
- GitHub Issues для багов
- Stack Overflow для вопросов
- Discord серверы для React/FastAPI

---

**🎉 Поздравляем! Ваш German Letter AI Assistant готов к использованию!**