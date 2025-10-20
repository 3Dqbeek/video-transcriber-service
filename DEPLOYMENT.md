# Инструкции по развертыванию Video Transcriber Service

## 🚀 Развертывание в продакшене

### 1. Подготовка сервера

#### Системные требования:
- **OS:** Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM:** Минимум 4GB, рекомендуется 8GB+
- **CPU:** Минимум 2 ядра, рекомендуется 4+
- **Диск:** Минимум 20GB свободного места
- **Сеть:** Стабильное интернет-соединение

#### Установка системных зависимостей:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git ffmpeg nginx supervisor
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 python3-pip git
sudo yum install -y epel-release
sudo yum install -y ffmpeg nginx supervisor
```

### 2. Установка T-one framework

```bash
# Создание пользователя для сервиса
sudo useradd -m -s /bin/bash transcriber
sudo su - transcriber

# Клонирование T-one
git clone https://github.com/voicekit-team/T-one.git
cd T-one

# Создание виртуального окружения
python3 -m venv .venv
source .venv/bin/activate

# Установка T-one
pip install -e .
```

### 3. Установка Video Transcriber Service

```bash
# Клонирование сервиса
git clone https://github.com/your-username/video-transcriber-service.git
cd video-transcriber-service

# Активация виртуального окружения T-one
source ../T-one/.venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Проверка установки
python3 check_installation.py
```

### 4. Настройка Nginx (обратный прокси)

Создайте конфигурацию Nginx:

```bash
sudo nano /etc/nginx/sites-available/video-transcriber
```

Содержимое файла:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Замените на ваш домен

    location / {
        proxy_pass http://127.0.0.1:8086;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Для WebSocket поддержки
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Статические файлы
    location /static/ {
        alias /home/transcriber/video-transcriber-service/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Активация конфигурации:
```bash
sudo ln -s /etc/nginx/sites-available/video-transcriber /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Настройка Supervisor (управление процессами)

Создайте конфигурацию Supervisor:

```bash
sudo nano /etc/supervisor/conf.d/video-transcriber.conf
```

Содержимое файла:
```ini
[program:video-transcriber]
command=/home/transcriber/T-one/.venv/bin/python3 /home/transcriber/video-transcriber-service/run_service.py
directory=/home/transcriber/video-transcriber-service
user=transcriber
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/video-transcriber.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/home/transcriber/T-one/.venv/bin"
```

Перезапуск Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start video-transcriber
```

### 6. Настройка SSL (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение SSL сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавьте строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 7. Настройка файрвола

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 🐳 Docker развертывание

### 1. Создание Dockerfile

```dockerfile
FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Клонирование и установка T-one
WORKDIR /app
RUN git clone https://github.com/voicekit-team/T-one.git
WORKDIR /app/T-one
RUN pip install -e .

# Установка Video Transcriber Service
WORKDIR /app
COPY video-transcriber-service/ .
RUN pip install -r requirements.txt

# Создание директорий
RUN mkdir -p transcriptions static templates

# Создание пользователя
RUN useradd -m transcriber && chown -R transcriber:transcriber /app
USER transcriber

# Открытие порта
EXPOSE 8086

# Запуск сервиса
CMD ["python3", "run_service.py"]
```

### 2. Docker Compose

```yaml
version: '3.8'

services:
  video-transcriber:
    build: .
    ports:
      - "8086:8086"
    volumes:
      - ./transcriptions:/app/transcriptions
      - ./logs:/app/logs
    environment:
      - HOST=0.0.0.0
      - PORT=8086
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8086/api/tasks"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - video-transcriber
    restart: unless-stopped
```

### 3. Запуск с Docker

```bash
# Сборка образа
docker build -t video-transcriber-service .

# Запуск контейнера
docker run -d \
  --name video-transcriber \
  -p 8086:8086 \
  -v $(pwd)/transcriptions:/app/transcriptions \
  video-transcriber-service

# Или с Docker Compose
docker-compose up -d
```

## ☁️ Облачное развертывание

### AWS EC2

1. **Создание EC2 инстанса:**
   - Тип: t3.medium или больше
   - OS: Ubuntu 20.04 LTS
   - Security Group: HTTP (80), HTTPS (443), SSH (22)

2. **Подключение и установка:**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   # Следуйте инструкциям выше для Ubuntu
   ```

3. **Настройка Elastic IP:**
   - Выделите Elastic IP
   - Свяжите с инстансом
   - Обновите DNS записи

### Google Cloud Platform

1. **Создание VM инстанса:**
   ```bash
   gcloud compute instances create video-transcriber \
     --image-family=ubuntu-2004-lts \
     --image-project=ubuntu-os-cloud \
     --machine-type=e2-medium \
     --zone=us-central1-a
   ```

2. **Установка сервиса:**
   ```bash
   gcloud compute ssh video-transcriber
   # Следуйте инструкциям выше
   ```

### Azure

1. **Создание VM:**
   ```bash
   az vm create \
     --resource-group myResourceGroup \
     --name video-transcriber \
     --image UbuntuLTS \
     --size Standard_B2s \
     --admin-username azureuser
   ```

2. **Установка сервиса:**
   ```bash
   az vm run-command invoke \
     --resource-group myResourceGroup \
     --name video-transcriber \
     --command-id RunShellScript \
     --scripts "sudo apt update && sudo apt install -y python3 python3-pip git ffmpeg"
   ```

## 📊 Мониторинг и логирование

### 1. Настройка логирования

```python
# В app.py добавьте:
import logging
from logging.handlers import RotatingFileHandler

# Настройка логирования
if not app.debug:
    file_handler = RotatingFileHandler('logs/video-transcriber.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

### 2. Мониторинг с Prometheus

```python
# Добавьте в requirements.txt:
# prometheus-client

# В app.py:
from prometheus_client import Counter, Histogram, generate_latest

# Метрики
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(process_time)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 3. Health Check

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

## 🔧 Настройка производительности

### 1. Оптимизация Nginx

```nginx
# В /etc/nginx/nginx.conf:
worker_processes auto;
worker_connections 1024;

http {
    # Кэширование
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m;
    
    # Сжатие
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    
    # Таймауты
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

### 2. Оптимизация Python

```python
# В run_service.py:
uvicorn.run(
    "app:app",
    host="0.0.0.0",
    port=8086,
    workers=4,  # Количество воркеров
    loop="uvloop",  # Быстрый event loop
    http="httptools",  # Быстрый HTTP парсер
)
```

## 🚨 Безопасность

### 1. Настройка файрвола

```bash
# UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. Настройка SSL

```bash
# Автоматическое обновление SSL
sudo crontab -e
# Добавьте:
0 12 * * * /usr/bin/certbot renew --quiet --reload-hook "systemctl reload nginx"
```

### 3. Ограничение доступа

```nginx
# В nginx конфигурации:
location /admin {
    allow 192.168.1.0/24;  # Только локальная сеть
    deny all;
    proxy_pass http://127.0.0.1:8086;
}
```

## 📈 Масштабирование

### 1. Горизонтальное масштабирование

```yaml
# docker-compose.yml
version: '3.8'
services:
  video-transcriber:
    build: .
    deploy:
      replicas: 3
    ports:
      - "8086:8086"
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### 2. Load Balancer конфигурация

```nginx
upstream video_transcriber {
    server 127.0.0.1:8086;
    server 127.0.0.1:8087;
    server 127.0.0.1:8088;
}

server {
    location / {
        proxy_pass http://video_transcriber;
    }
}
```

---

**Примечание:** Всегда тестируйте развертывание в тестовой среде перед продакшеном!
