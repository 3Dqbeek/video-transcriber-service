#!/usr/bin/env python3
"""
Потоковый транскрибатор видео для веб-сервиса
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import yt_dlp
import subprocess
import threading
import queue
import numpy as np
import librosa
import soundfile as sf

from tone.pipeline import StreamingCTCPipeline, TextPhrase
from tone.demo.enhanced_website import RoleDetector, DialogLogger

logger = logging.getLogger(__name__)

class StreamingVideoTranscriber:
    """Потоковый транскрибатор видео с поддержкой различных источников"""
    
    def __init__(self, output_dir: str = "transcriptions"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline: Optional[StreamingCTCPipeline] = None
        self.role_detector: Optional[RoleDetector] = None
        self.dialog_logger: Optional[DialogLogger] = None
        self.temp_dir = Path(tempfile.mkdtemp(prefix="video_transcriber_"))
        
        logger.info(f"StreamingVideoTranscriber инициализирован. Выходная директория: {self.output_dir}")
    
    def init_pipeline(self, use_gpu: bool = False):
        """Инициализация пайплайна T-one"""
        if self.pipeline is not None:
            return True
        
        try:
            logger.info("Инициализация пайплайна T-one...")
            self.pipeline = StreamingCTCPipeline.from_hugging_face()
            self.role_detector = RoleDetector()
            self.dialog_logger = DialogLogger(self.output_dir)
            
            logger.info("✅ Пайплайн T-one инициализирован!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации пайплайна: {e}")
            return False
    
    def download_video_audio(self, video_url: str) -> Optional[str]:
        """Скачивание аудио из видео URL"""
        logger.info(f"📥 Скачивание аудио из: {video_url}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.temp_dir / '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'noplaylist': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=True)
                # Находим скачанный файл
                downloaded_files = list(self.temp_dir.glob(f"{info_dict['title']}*.wav"))
                if downloaded_files:
                    audio_path = str(downloaded_files[0])
                    logger.info(f"✅ Аудио скачано: {audio_path}")
                    return audio_path
                else:
                    logger.error(f"❌ Не удалось найти скачанный аудиофайл")
                    return None
        except Exception as e:
            logger.error(f"❌ Ошибка скачивания: {e}")
            return None
    
    def extract_audio_from_video(self, video_path: str) -> Optional[str]:
        """Извлечение аудио из локального видео файла"""
        logger.info(f"🎵 Извлечение аудио из: {video_path}")
        
        try:
            # Используем ffmpeg для извлечения аудио
            audio_path = self.temp_dir / f"extracted_audio_{int(time.time())}.wav"
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ar', '8000',  # 8kHz sample rate
                '-ac', '1',     # mono
                '-y',           # overwrite output file
                str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and audio_path.exists():
                logger.info(f"✅ Аудио извлечено: {audio_path}")
                return str(audio_path)
            else:
                logger.error(f"❌ Ошибка извлечения аудио: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения аудио: {e}")
            return None
    
    def transcribe_audio_file(self, audio_path: str, output_format: str = "txt") -> tuple[List[Dict[str, Any]], Path]:
        """Транскрибирует аудиофайл и возвращает результат"""
        if not self.pipeline or not self.role_detector:
            raise Exception("Пайплайн T-one не инициализирован.")
        
        logger.info(f"🎤 Транскрибация аудио: {audio_path}")
        
        try:
            # Загрузка аудио
            audio_data, sample_rate = librosa.load(audio_path, sr=8000)  # 8kHz для T-one
            # Нормализуем аудио и конвертируем в int32 в диапазоне [-32768, 32767]
            audio_data = np.clip(audio_data, -1.0, 1.0)  # Ограничиваем диапазон
            audio_data = (audio_data * 32767).astype(np.int32)
            logger.info(f"📊 Аудио: {len(audio_data)} сэмплов, {sample_rate} Hz")
            logger.info(f"⏱️ Длительность: {len(audio_data) / sample_rate:.2f} сек")
            
            # Обработка аудио по чанкам
            chunk_size = self.pipeline.CHUNK_SIZE
            total_chunks = (len(audio_data) + chunk_size - 1) // chunk_size
            
            dialogue_log = []
            state = None  # Инициализируем состояние для потоковой обработки
            
            for i in range(total_chunks):
                start_idx = i * chunk_size
                end_idx = min((i + 1) * chunk_size, len(audio_data))
                chunk = audio_data[start_idx:end_idx]
                is_last_chunk = (i == total_chunks - 1)
                
                # Проверяем размер чанка и дополняем до нужного размера если необходимо
                if len(chunk) < chunk_size:
                    # Дополняем последний чанк нулями до нужного размера
                    padding = np.zeros(chunk_size - len(chunk), dtype=np.int32)
                    chunk = np.concatenate([chunk, padding])
                
                # Обработка чанка
                phrases, state = self.pipeline.forward(chunk, state, is_last=is_last_chunk)
                
                for phrase in phrases:
                    role = self.role_detector.detect_role(phrase.text)
                    dialogue_log.append({
                        "role": role.value,
                        "text": phrase.text,
                        "start": phrase.start_time,
                        "end": phrase.end_time,
                    })
                    
                    logger.info(f"📝 [{role.value}] {phrase.text}")
            
            logger.info(f"✅ Транскрибация завершена: {len(dialogue_log)} фраз")
            
            # Сохранение результата
            video_title = Path(audio_path).stem
            output_file_path = self._save_transcript(dialogue_log, video_title, output_format)
            
            logger.info(f"✅ Транскрипция сохранена: {output_file_path}")
            return dialogue_log, output_file_path
            
        except Exception as e:
            logger.error(f"❌ Ошибка транскрибации аудио: {e}")
            raise
    
    def _save_transcript(self, dialogue_log: List[Dict[str, Any]], video_title: str, output_format: str) -> Path:
        """Сохраняет транскрипцию в указанном формате"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format == "txt":
            filename = f"{video_title}_transcription_{timestamp}.txt"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Транскрипция видео: {video_title}\n")
                f.write("=" * 50 + "\n\n")
                
                for entry in dialogue_log:
                    time_str = f"{entry['start']:.2f}s - {entry['end']:.2f}s"
                    f.write(f"[{time_str}] [{entry['role']}] {entry['text']}\n")
            
            return filepath
            
        elif output_format == "json":
            filename = f"{video_title}_transcription_{timestamp}.json"
            filepath = self.output_dir / filename
            
            transcript_data = {
                "video_title": video_title,
                "timestamp": timestamp,
                "total_phrases": len(dialogue_log),
                "phrases": dialogue_log
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            
            return filepath
            
        else:
            raise ValueError(f"Неподдерживаемый формат: {output_format}")
    
    def transcribe_video(self, video_input: str, output_format: str = "txt") -> tuple[List[Dict[str, Any]], Path]:
        """Основной метод для транскрибации видео (URL или локальный файл)"""
        if not self.init_pipeline():
            raise Exception("Не удалось инициализировать пайплайн T-one.")
        
        # Определяем тип входа
        if video_input.startswith(('http://', 'https://')):
            # Это URL - скачиваем видео
            audio_path = self.download_video_audio(video_input)
        else:
            # Это локальный файл - извлекаем аудио
            audio_path = self.extract_audio_from_video(video_input)
        
        if not audio_path:
            raise Exception("Не удалось получить аудио из видео.")
        
        try:
            return self.transcribe_audio_file(audio_path, output_format)
        finally:
            # Очищаем временные файлы
            if Path(audio_path).exists():
                os.remove(audio_path)
    
    def cleanup(self):
        """Очистка временных файлов"""
        if self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"🧹 Временная директория очищена: {self.temp_dir}")

if __name__ == "__main__":
    # Тестирование
    transcriber = StreamingVideoTranscriber()
    
    try:
        # Пример использования
        print("🎬 Тестирование транскрибатора...")
        # Здесь можно добавить тестовый код
    finally:
        transcriber.cleanup()
