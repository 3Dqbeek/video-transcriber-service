# Примеры использования Video Transcriber Service

## 🎯 Базовые примеры

### 1. Транскрибация видео по URL

```python
from streaming_video_transcriber import StreamingVideoTranscriber

# Создание экземпляра транскрибатора
transcriber = StreamingVideoTranscriber()

# Инициализация пайплайна
transcriber.init_pipeline()

# Транскрибация Rutube видео
rutube_url = "https://rutube.ru/video/private/82e26b17b3fe39300a3264ca3b2d34cc/"
transcript_data, output_file = transcriber.transcribe_video(rutube_url, "txt")

print(f"Транскрипция завершена: {len(transcript_data)} фраз")
print(f"Результат сохранен в: {output_file}")
```

### 2. Транскрибация локального видео файла

```python
from streaming_video_transcriber import StreamingVideoTranscriber

transcriber = StreamingVideoTranscriber()
transcriber.init_pipeline()

# Транскрибация локального файла
video_path = "/path/to/your/video.mp4"
transcript_data, output_file = transcriber.transcribe_video(video_path, "json")

# Вывод результатов
for phrase in transcript_data[:5]:  # Первые 5 фраз
    print(f"[{phrase['role']}] {phrase['text']}")
    print(f"Время: {phrase['start']:.2f}s - {phrase['end']:.2f}s")
```

### 3. Использование веб-API

```python
import requests
import json

# Запуск транскрибации через API
response = requests.post('http://localhost:8086/api/transcribe-url', 
                        json={
                            'video_url': 'https://rutube.ru/video/...',
                            'output_format': 'txt'
                        })

task_id = response.json()['task_id']
print(f"Задача создана: {task_id}")

# Проверка статуса
while True:
    status_response = requests.get(f'http://localhost:8086/api/status/{task_id}')
    status = status_response.json()
    
    print(f"Статус: {status['status']} - {status['message']}")
    print(f"Прогресс: {status['progress']}%")
    
    if status['status'] == 'completed':
        # Скачивание результата
        download_response = requests.get(f'http://localhost:8086/api/download/{task_id}')
        with open('result.txt', 'wb') as f:
            f.write(download_response.content)
        print("Результат скачан!")
        break
    elif status['status'] == 'error':
        print(f"Ошибка: {status['message']}")
        break
    
    time.sleep(2)
```

## 🔧 Продвинутые примеры

### 4. Batch обработка множества видео

```python
import os
from pathlib import Path
from streaming_video_transcriber import StreamingVideoTranscriber

def batch_transcribe_videos(video_directory, output_directory):
    """Обработка всех видео в директории"""
    transcriber = StreamingVideoTranscriber(output_dir=output_directory)
    transcriber.init_pipeline()
    
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    video_files = []
    
    # Поиск видео файлов
    for ext in video_extensions:
        video_files.extend(Path(video_directory).glob(f'*{ext}'))
    
    results = []
    for video_file in video_files:
        try:
            print(f"Обработка: {video_file.name}")
            transcript_data, output_file = transcriber.transcribe_video(
                str(video_file), "txt"
            )
            results.append({
                'input': str(video_file),
                'output': str(output_file),
                'phrases_count': len(transcript_data)
            })
            print(f"✅ Завершено: {len(transcript_data)} фраз")
        except Exception as e:
            print(f"❌ Ошибка при обработке {video_file.name}: {e}")
            results.append({
                'input': str(video_file),
                'error': str(e)
            })
    
    return results

# Использование
results = batch_transcribe_videos('/path/to/videos', '/path/to/output')
for result in results:
    if 'error' in result:
        print(f"❌ {result['input']}: {result['error']}")
    else:
        print(f"✅ {result['input']}: {result['phrases_count']} фраз")
```

### 5. Кастомная обработка результатов

```python
from streaming_video_transcriber import StreamingVideoTranscriber
import json

def analyze_transcript(transcript_data):
    """Анализ транскрипции"""
    analysis = {
        'total_phrases': len(transcript_data),
        'roles': {},
        'total_duration': 0,
        'average_phrase_length': 0,
        'longest_phrase': '',
        'shortest_phrase': ''
    }
    
    phrase_lengths = []
    longest_text = ''
    shortest_text = 'x' * 1000  # Большое значение для сравнения
    
    for phrase in transcript_data:
        # Подсчет ролей
        role = phrase['role']
        analysis['roles'][role] = analysis['roles'].get(role, 0) + 1
        
        # Длительность
        duration = phrase['end'] - phrase['start']
        analysis['total_duration'] += duration
        
        # Длина фраз
        text_length = len(phrase['text'])
        phrase_lengths.append(text_length)
        
        if text_length > len(longest_text):
            longest_text = phrase['text']
        if text_length < len(shortest_text) and text_length > 0:
            shortest_text = phrase['text']
    
    analysis['average_phrase_length'] = sum(phrase_lengths) / len(phrase_lengths)
    analysis['longest_phrase'] = longest_text
    analysis['shortest_phrase'] = shortest_text
    
    return analysis

# Использование
transcriber = StreamingVideoTranscriber()
transcriber.init_pipeline()

transcript_data, output_file = transcriber.transcribe_video(
    "https://rutube.ru/video/...", "json"
)

analysis = analyze_transcript(transcript_data)
print("📊 Анализ транскрипции:")
print(f"Всего фраз: {analysis['total_phrases']}")
print(f"Роли: {analysis['roles']}")
print(f"Общая длительность: {analysis['total_duration']:.2f} секунд")
print(f"Средняя длина фразы: {analysis['average_phrase_length']:.1f} символов")
print(f"Самая длинная фраза: {analysis['longest_phrase'][:50]}...")
print(f"Самая короткая фраза: {analysis['shortest_phrase']}")
```

### 6. Интеграция с внешними системами

```python
import requests
from streaming_video_transcriber import StreamingVideoTranscriber

class TranscriberAPI:
    """Класс для интеграции с внешними API"""
    
    def __init__(self, base_url="http://localhost:8086"):
        self.base_url = base_url
        self.transcriber = StreamingVideoTranscriber()
        self.transcriber.init_pipeline()
    
    def transcribe_and_send_to_api(self, video_url, external_api_url):
        """Транскрибация и отправка результата во внешний API"""
        # Транскрибация
        transcript_data, output_file = self.transcriber.transcribe_video(video_url, "json")
        
        # Подготовка данных для отправки
        payload = {
            'video_url': video_url,
            'transcript': transcript_data,
            'metadata': {
                'total_phrases': len(transcript_data),
                'roles': self._count_roles(transcript_data),
                'duration': self._calculate_duration(transcript_data)
            }
        }
        
        # Отправка во внешний API
        try:
            response = requests.post(external_api_url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка отправки в API: {e}")
            return None
    
    def _count_roles(self, transcript_data):
        """Подсчет ролей"""
        roles = {}
        for phrase in transcript_data:
            role = phrase['role']
            roles[role] = roles.get(role, 0) + 1
        return roles
    
    def _calculate_duration(self, transcript_data):
        """Расчет общей длительности"""
        if not transcript_data:
            return 0
        return transcript_data[-1]['end'] - transcript_data[0]['start']

# Использование
api = TranscriberAPI()
result = api.transcribe_and_send_to_api(
    "https://rutube.ru/video/...",
    "https://your-external-api.com/transcripts"
)
```

## 🚀 Примеры для продакшена

### 7. Docker контейнеризация

```dockerfile
# Dockerfile
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

# Создание директории для транскрипций
RUN mkdir -p transcriptions

# Открытие порта
EXPOSE 8086

# Запуск сервиса
CMD ["python3", "run_service.py"]
```

### 8. Мониторинг и логирование

```python
import logging
import time
from datetime import datetime
from streaming_video_transcriber import StreamingVideoTranscriber

class MonitoredTranscriber(StreamingVideoTranscriber):
    """Транскрибатор с мониторингом"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_logging()
        self.stats = {
            'total_videos': 0,
            'successful_transcriptions': 0,
            'failed_transcriptions': 0,
            'total_processing_time': 0
        }
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('transcriber.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def transcribe_video(self, video_input, output_format="txt"):
        """Транскрибация с мониторингом"""
        start_time = time.time()
        self.stats['total_videos'] += 1
        
        try:
            self.logger.info(f"Начало транскрибации: {video_input}")
            result = super().transcribe_video(video_input, output_format)
            
            processing_time = time.time() - start_time
            self.stats['successful_transcriptions'] += 1
            self.stats['total_processing_time'] += processing_time
            
            self.logger.info(f"Транскрибация завершена за {processing_time:.2f}с")
            return result
            
        except Exception as e:
            self.stats['failed_transcriptions'] += 1
            self.logger.error(f"Ошибка транскрибации: {e}")
            raise
    
    def get_stats(self):
        """Получение статистики"""
        avg_time = 0
        if self.stats['successful_transcriptions'] > 0:
            avg_time = self.stats['total_processing_time'] / self.stats['successful_transcriptions']
        
        return {
            **self.stats,
            'average_processing_time': avg_time,
            'success_rate': self.stats['successful_transcriptions'] / self.stats['total_videos'] * 100
        }

# Использование
monitored_transcriber = MonitoredTranscriber()

# Транскрибация с мониторингом
transcript_data, output_file = monitored_transcriber.transcribe_video(
    "https://rutube.ru/video/...", "txt"
)

# Получение статистики
stats = monitored_transcriber.get_stats()
print(f"Статистика: {stats}")
```

## 📚 Дополнительные ресурсы

- [T-one Framework](https://github.com/voicekit-team/T-one) - основная библиотека
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - веб-фреймворк
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp) - скачивание видео
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html) - обработка медиа

---

**Примечание:** Убедитесь, что все зависимости установлены и T-one framework настроен перед запуском примеров.
