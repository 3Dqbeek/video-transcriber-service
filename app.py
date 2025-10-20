#!/usr/bin/env python3
"""
Веб-сервис для транскрибации видео
"""

from fastapi import FastAPI, Request, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import os
import time
import uuid
from pathlib import Path
from typing import Dict, Any
import logging

from streaming_video_transcriber import StreamingVideoTranscriber

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Video Transcriber Service", version="1.0.0")

# Глобальное хранилище задач
tasks: Dict[str, Dict[str, Any]] = {}

# Инициализация транскрибатора
transcriber = StreamingVideoTranscriber()

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Запуск Video Transcriber Service")
    logger.info("=" * 50)
    logger.info("Функциональность:")
    logger.info("✅ Транскрибация видео из URL и локальных файлов")
    logger.info("✅ Определение ролей говорящих")
    logger.info("✅ Экспорт в TXT и JSON форматах")
    logger.info("✅ Веб-интерфейс для удобного использования")
    logger.info("=" * 50)
    logger.info("🌐 Сервер будет доступен по адресу: http://0.0.0.0:8086")
    logger.info("📱 Веб-интерфейс: http://localhost:8086")
    logger.info("💡 Для остановки сервера нажмите Ctrl+C")
    logger.info("=" * 50)
    
    # Инициализация пайплайна T-one
    transcriber.init_pipeline(use_gpu=False)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Video Transcriber Service</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            
            .container {
                background: rgba(255, 255, 255, 0.95);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                width: 100%;
                max-width: 800px;
                backdrop-filter: blur(10px);
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .header h1 {
                color: #4a5568;
                margin-bottom: 10px;
                font-size: 2.5em;
                font-weight: 700;
            }
            
            .header p {
                color: #718096;
                font-size: 1.2em;
            }
            
            .tabs {
                display: flex;
                margin-bottom: 30px;
                border-bottom: 2px solid #e2e8f0;
            }
            
            .tab {
                flex: 1;
                padding: 15px 20px;
                background: none;
                border: none;
                cursor: pointer;
                font-size: 1.1em;
                font-weight: 600;
                color: #718096;
                transition: all 0.3s ease;
                border-bottom: 3px solid transparent;
            }
            
            .tab.active {
                color: #667eea;
                border-bottom-color: #667eea;
            }
            
            .tab-content {
                display: none;
            }
            
            .tab-content.active {
                display: block;
            }
            
            .form-group {
                margin-bottom: 25px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #4a5568;
            }
            
            input[type="url"], input[type="file"], select {
                width: 100%;
                padding: 15px;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                font-size: 1em;
                transition: border-color 0.3s ease;
            }
            
            input[type="url"]:focus, input[type="file"]:focus, select:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .file-upload-area {
                border: 2px dashed #cbd5e0;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                background: #f7fafc;
            }
            
            .file-upload-area:hover {
                border-color: #667eea;
                background: #edf2f7;
            }
            
            .file-upload-area.dragover {
                border-color: #667eea;
                background: #e6fffa;
            }
            
            button {
                width: 100%;
                padding: 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 1.2em;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            button:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            
            button:disabled {
                background: #a0aec0;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            .status-section {
                margin-top: 30px;
                padding: 25px;
                border-radius: 15px;
                background: #f7fafc;
                border: 1px solid #e2e8f0;
                display: none;
            }
            
            .status-section.active {
                display: block;
            }
            
            .status-message {
                font-size: 1.1em;
                margin-bottom: 15px;
                padding: 15px;
                border-radius: 10px;
                word-wrap: break-word;
            }
            
            .status-message.processing {
                background: #e6fffa;
                color: #234e52;
                border: 1px solid #81e6d9;
            }
            
            .status-message.completed {
                background: #f0fff4;
                color: #22543d;
                border: 1px solid #9ae6b4;
            }
            
            .status-message.error {
                background: #fed7d7;
                color: #742a2a;
                border: 1px solid #feb2b2;
            }
            
            .progress-bar-container {
                width: 100%;
                background: #e2e8f0;
                border-radius: 10px;
                margin-top: 15px;
                height: 30px;
                overflow: hidden;
            }
            
            .progress-bar {
                height: 100%;
                width: 0%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                text-align: center;
                line-height: 30px;
                color: white;
                font-weight: 600;
                border-radius: 10px;
                transition: width 0.5s ease-in-out;
            }
            
            .download-link {
                display: inline-block;
                margin-top: 20px;
                padding: 15px 30px;
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: 600;
                transition: transform 0.3s ease;
            }
            
            .download-link:hover {
                transform: translateY(-2px);
            }
            
            .task-list {
                margin-top: 30px;
            }
            
            .task-item {
                background: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 15px;
            }
            
            .task-item h3 {
                color: #4a5568;
                margin-bottom: 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .task-info {
                font-size: 0.9em;
                color: #718096;
                margin-bottom: 10px;
            }
            
            .task-status {
                font-size: 1em;
                margin-bottom: 10px;
                padding: 10px;
                border-radius: 8px;
            }
            
            .task-status.processing {
                background: #e6fffa;
                color: #234e52;
            }
            
            .task-status.completed {
                background: #f0fff4;
                color: #22543d;
            }
            
            .task-status.error {
                background: #fed7d7;
                color: #742a2a;
            }
            
            .task-progress {
                width: 100%;
                background: #e2e8f0;
                border-radius: 8px;
                height: 20px;
                overflow: hidden;
                margin-top: 10px;
            }
            
            .task-progress-bar {
                height: 100%;
                width: 0%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                transition: width 0.5s ease-in-out;
            }
            
            .task-actions {
                margin-top: 15px;
            }
            
            .task-actions a {
                display: inline-block;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                margin-right: 10px;
            }
            
            .task-actions a:hover {
                background: #5a67d8;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            
            .stat-card {
                background: #f7fafc;
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                border: 1px solid #e2e8f0;
            }
            
            .stat-number {
                font-size: 2em;
                font-weight: 700;
                color: #667eea;
                margin-bottom: 5px;
            }
            
            .stat-label {
                color: #718096;
                font-weight: 600;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎬 Video Transcriber</h1>
                <p>Транскрибация видео в текст с определением ролей говорящих</p>
            </div>
            
            <div class="tabs">
                <button class="tab active" onclick="switchTab('url')">📺 Из URL</button>
                <button class="tab" onclick="switchTab('file')">📁 Из файла</button>
                <button class="tab" onclick="switchTab('tasks')">📋 Задачи</button>
            </div>
            
            <!-- URL Tab -->
            <div id="url-tab" class="tab-content active">
                <form id="urlForm">
                    <div class="form-group">
                        <label for="videoUrl">Ссылка на видео:</label>
                        <input type="url" id="videoUrl" name="video_url" 
                               placeholder="https://rutube.ru/video/... или https://youtube.com/watch?v=..." required>
                    </div>
                    <div class="form-group">
                        <label for="outputFormat">Формат вывода:</label>
                        <select id="outputFormat" name="output_format">
                            <option value="txt">TXT (Текст)</option>
                            <option value="json">JSON (Данные)</option>
                        </select>
                    </div>
                    <button type="submit" id="urlSubmitBtn">🚀 Начать транскрибацию</button>
                </form>
            </div>
            
            <!-- File Tab -->
            <div id="file-tab" class="tab-content">
                <form id="fileForm">
                    <div class="form-group">
                        <label for="videoFile">Выберите видео файл:</label>
                        <div class="file-upload-area" id="fileUploadArea">
                            <p>📁 Перетащите видео файл сюда или нажмите для выбора</p>
                            <p style="font-size: 0.9em; color: #718096; margin-top: 10px;">
                                Поддерживаемые форматы: MP4, AVI, MOV, MKV, WEBM
                            </p>
                            <input type="file" id="videoFile" name="video_file" 
                                   accept="video/*" style="display: none;">
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="fileOutputFormat">Формат вывода:</label>
                        <select id="fileOutputFormat" name="output_format">
                            <option value="txt">TXT (Текст)</option>
                            <option value="json">JSON (Данные)</option>
                        </select>
                    </div>
                    <button type="submit" id="fileSubmitBtn">🚀 Начать транскрибацию</button>
                </form>
            </div>
            
            <!-- Tasks Tab -->
            <div id="tasks-tab" class="tab-content">
                <div class="task-list" id="taskList">
                    <h2>Активные и завершенные задачи</h2>
                    <div id="tasksContainer">
                        <!-- Задачи будут добавляться сюда -->
                    </div>
                </div>
                
                <div class="stats" id="statsContainer">
                    <!-- Статистика будет добавляться сюда -->
                </div>
            </div>
            
            <!-- Status Section -->
            <div class="status-section" id="statusSection">
                <h2>Статус транскрибации</h2>
                <div id="statusMessage" class="status-message"></div>
                <div class="progress-bar-container">
                    <div class="progress-bar" id="progressBar">0%</div>
                </div>
                <div id="downloadLinkContainer"></div>
            </div>
        </div>

        <script>
            let currentTaskId = null;
            
            // Tab switching
            function switchTab(tabName) {
                // Hide all tab contents
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // Remove active class from all tabs
                document.querySelectorAll('.tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show selected tab content
                document.getElementById(tabName + '-tab').classList.add('active');
                
                // Add active class to clicked tab
                event.target.classList.add('active');
                
                // Load tasks if tasks tab is selected
                if (tabName === 'tasks') {
                    loadTasks();
                }
            }
            
            // File upload handling
            const fileUploadArea = document.getElementById('fileUploadArea');
            const videoFileInput = document.getElementById('videoFile');
            
            fileUploadArea.addEventListener('click', () => videoFileInput.click());
            
            fileUploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                fileUploadArea.classList.add('dragover');
            });
            
            fileUploadArea.addEventListener('dragleave', () => {
                fileUploadArea.classList.remove('dragover');
            });
            
            fileUploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                fileUploadArea.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    videoFileInput.files = files;
                    updateFileDisplay(files[0]);
                }
            });
            
            videoFileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    updateFileDisplay(e.target.files[0]);
                }
            });
            
            function updateFileDisplay(file) {
                fileUploadArea.innerHTML = `
                    <p>✅ Выбран файл: <strong>${file.name}</strong></p>
                    <p style="font-size: 0.9em; color: #718096; margin-top: 10px;">
                        Размер: ${(file.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                `;
            }
            
            // URL form submission
            document.getElementById('urlForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                await startTranscription('url');
            });
            
            // File form submission
            document.getElementById('fileForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                await startTranscription('file');
            });
            
            async function startTranscription(type) {
                const submitBtn = type === 'url' ? document.getElementById('urlSubmitBtn') : document.getElementById('fileSubmitBtn');
                submitBtn.disabled = true;
                
                showStatus('processing', '🚀 Запускаем транскрибацию...', 0);
                
                try {
                    let response;
                    
                    if (type === 'url') {
                        const videoUrl = document.getElementById('videoUrl').value;
                        const outputFormat = document.getElementById('outputFormat').value;
                        
                        response = await fetch('/api/transcribe-url', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ video_url: videoUrl, output_format: outputFormat })
                        });
                    } else {
                        const formData = new FormData();
                        formData.append('video_file', document.getElementById('videoFile').files[0]);
                        formData.append('output_format', document.getElementById('fileOutputFormat').value);
                        
                        response = await fetch('/api/transcribe-file', {
                            method: 'POST',
                            body: formData
                        });
                    }
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        currentTaskId = data.task_id;
                        pollStatus(currentTaskId);
                    } else {
                        showStatus('error', `Ошибка: ${data.message || 'Неизвестная ошибка'}`, 0);
                    }
                } catch (error) {
                    showStatus('error', `Ошибка при отправке запроса: ${error.message}`, 0);
                } finally {
                    submitBtn.disabled = false;
                }
            }
            
            function showStatus(type, message, progress) {
                const statusSection = document.getElementById('statusSection');
                const statusMessage = document.getElementById('statusMessage');
                const progressBar = document.getElementById('progressBar');
                
                statusSection.classList.add('active');
                statusMessage.className = `status-message ${type}`;
                statusMessage.textContent = message;
                progressBar.style.width = `${progress}%`;
                progressBar.textContent = `${Math.round(progress)}%`;
            }
            
            async function pollStatus(taskId) {
                try {
                    const response = await fetch(`/api/status/${taskId}`);
                    const taskStatus = await response.json();
                    
                    if (taskStatus.status === 'processing') {
                        showStatus('processing', taskStatus.message, taskStatus.progress);
                        setTimeout(() => pollStatus(taskId), 2000);
                    } else if (taskStatus.status === 'completed') {
                        showStatus('completed', 'Транскрибация завершена!', 100);
                        
                        if (taskStatus.result && taskStatus.result.output_path) {
                            const downloadLink = document.createElement('a');
                            downloadLink.href = `/api/download/${taskId}`;
                            downloadLink.className = 'download-link';
                            downloadLink.textContent = '📥 Скачать результат';
                            downloadLink.download = '';
                            document.getElementById('downloadLinkContainer').appendChild(downloadLink);
                        }
                        
                        // Switch to tasks tab to show the completed task
                        switchTab('tasks');
                        loadTasks();
                    } else if (taskStatus.status === 'error') {
                        showStatus('error', `Ошибка: ${taskStatus.message}`, 0);
                    }
                } catch (error) {
                    showStatus('error', `Ошибка проверки статуса: ${error.message}`, 0);
                }
            }
            
            async function loadTasks() {
                try {
                    const response = await fetch('/api/tasks');
                    const tasks = await response.json();
                    
                    const tasksContainer = document.getElementById('tasksContainer');
                    const statsContainer = document.getElementById('statsContainer');
                    
                    // Clear containers
                    tasksContainer.innerHTML = '';
                    statsContainer.innerHTML = '';
                    
                    if (Object.keys(tasks).length === 0) {
                        tasksContainer.innerHTML = '<p style="text-align: center; color: #718096;">Нет активных задач</p>';
                        return;
                    }
                    
                    // Display tasks
                    Object.values(tasks).forEach(task => {
                        const taskElement = createTaskElement(task);
                        tasksContainer.appendChild(taskElement);
                    });
                    
                    // Display stats
                    const stats = calculateStats(tasks);
                    statsContainer.innerHTML = `
                        <div class="stat-card">
                            <div class="stat-number">${stats.total}</div>
                            <div class="stat-label">Всего задач</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.completed}</div>
                            <div class="stat-label">Завершено</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.processing}</div>
                            <div class="stat-label">В обработке</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.error}</div>
                            <div class="stat-label">Ошибок</div>
                        </div>
                    `;
                } catch (error) {
                    console.error('Ошибка загрузки задач:', error);
                }
            }
            
            function createTaskElement(task) {
                const taskDiv = document.createElement('div');
                taskDiv.className = 'task-item';
                
                const progress = Math.round(task.progress || 0);
                const duration = task.start_time ? Math.round((Date.now() / 1000) - task.start_time) : 0;
                const durationText = duration > 0 ? ` (${formatDuration(duration)})` : '';
                
                taskDiv.innerHTML = `
                    <h3>
                        <span>${task.video_input ? task.video_input.substring(0, 50) + '...' : 'Задача'}</span>
                        <span style="font-size: 0.8em; color: #718096;">ID: ${task.id.substring(0, 8)}</span>
                    </h3>
                    <div class="task-info">Формат: ${task.output_format?.toUpperCase() || 'TXT'}</div>
                    <div class="task-status ${task.status}">${task.message}${durationText}</div>
                    <div class="task-progress">
                        <div class="task-progress-bar" style="width: ${progress}%"></div>
                    </div>
                    <div class="task-actions" id="task-actions-${task.id}"></div>
                `;
                
                const taskActions = taskDiv.querySelector(`#task-actions-${task.id}`);
                
                if (task.status === 'completed' && task.result && task.result.output_path) {
                    const downloadLink = document.createElement('a');
                    downloadLink.href = `/api/download/${task.id}`;
                    downloadLink.textContent = '📥 Скачать';
                    taskActions.appendChild(downloadLink);
                }
                
                return taskDiv;
            }
            
            function calculateStats(tasks) {
                const taskList = Object.values(tasks);
                return {
                    total: taskList.length,
                    completed: taskList.filter(t => t.status === 'completed').length,
                    processing: taskList.filter(t => t.status === 'processing').length,
                    error: taskList.filter(t => t.status === 'error').length
                };
            }
            
            function formatDuration(seconds) {
                const h = Math.floor(seconds / 3600);
                const m = Math.floor((seconds % 3600) / 60);
                const s = Math.floor(seconds % 60);
                return [h, m, s]
                    .map(v => v < 10 ? "0" + v : v)
                    .filter((v, i) => v !== "00" || i > 0)
                    .join(":");
            }
            
            // Auto-refresh tasks every 30 seconds
            setInterval(() => {
                if (document.getElementById('tasks-tab').classList.contains('active')) {
                    loadTasks();
                }
            }, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/transcribe-url")
async def transcribe_video_url(
    video_data: dict,
    background_tasks: BackgroundTasks
):
    """API endpoint для транскрибации видео по URL"""
    video_url = video_data.get("video_url")
    output_format = video_data.get("output_format", "txt")
    
    if not video_url:
        raise HTTPException(status_code=400, detail="URL видео не предоставлен")
    
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "id": task_id,
        "video_input": video_url,
        "output_format": output_format,
        "status": "processing",
        "message": "Начало транскрибации...",
        "progress": 0,
        "result": None,
        "start_time": time.time()
    }
    
    background_tasks.add_task(
        process_transcription_task,
        task_id,
        video_url,
        output_format
    )
    
    return JSONResponse(content={"message": "Транскрибация запущена", "task_id": task_id})

@app.post("/api/transcribe-file")
async def transcribe_video_file(
    video_file: UploadFile = File(...),
    output_format: str = "txt",
    background_tasks: BackgroundTasks = None
):
    """API endpoint для транскрибации загруженного видео файла"""
    if not video_file:
        raise HTTPException(status_code=400, detail="Видео файл не предоставлен")
    
    # Сохраняем загруженный файл во временную директорию
    temp_dir = Path(tempfile.mkdtemp(prefix="uploaded_video_"))
    temp_file_path = temp_dir / video_file.filename
    
    with open(temp_file_path, "wb") as buffer:
        content = await video_file.read()
        buffer.write(content)
    
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "id": task_id,
        "video_input": video_file.filename,
        "output_format": output_format,
        "status": "processing",
        "message": "Начало транскрибации...",
        "progress": 0,
        "result": None,
        "start_time": time.time(),
        "temp_file_path": str(temp_file_path)
    }
    
    background_tasks.add_task(
        process_file_transcription_task,
        task_id,
        str(temp_file_path),
        output_format
    )
    
    return JSONResponse(content={"message": "Транскрибация запущена", "task_id": task_id})

async def process_transcription_task(task_id: str, video_url: str, output_format: str):
    """Обработка задачи транскрибации по URL"""
    try:
        logger.info(f"🚀 Начало транскрибации URL: {video_url}")
        tasks[task_id]["message"] = "Инициализация пайплайна..."
        tasks[task_id]["progress"] = 5
        
        # Инициализация пайплайна
        if not transcriber.pipeline:
            transcriber.init_pipeline(use_gpu=False)
        
        tasks[task_id]["message"] = "Скачивание видео..."
        tasks[task_id]["progress"] = 10
        
        # Транскрибация
        transcript_data, output_file_path = await asyncio.to_thread(
            transcriber.transcribe_video,
            video_url,
            output_format
        )
        
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["message"] = "Транскрибация завершена!"
        tasks[task_id]["progress"] = 100
        tasks[task_id]["result"] = {
            "transcript": transcript_data,
            "output_path": str(output_file_path)
        }
        
        logger.info(f"✅ Транскрибация задачи {task_id} завершена. Результат: {output_file_path}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке задачи {task_id}: {e}")
        tasks[task_id]["status"] = "error"
        tasks[task_id]["message"] = f"Ошибка при транскрибации: {e}"
        tasks[task_id]["progress"] = 0

async def process_file_transcription_task(task_id: str, video_file_path: str, output_format: str):
    """Обработка задачи транскрибации загруженного файла"""
    try:
        logger.info(f"🚀 Начало транскрибации файла: {video_file_path}")
        tasks[task_id]["message"] = "Инициализация пайплайна..."
        tasks[task_id]["progress"] = 5
        
        # Инициализация пайплайна
        if not transcriber.pipeline:
            transcriber.init_pipeline(use_gpu=False)
        
        tasks[task_id]["message"] = "Обработка видео файла..."
        tasks[task_id]["progress"] = 10
        
        # Транскрибация
        transcript_data, output_file_path = await asyncio.to_thread(
            transcriber.transcribe_video,
            video_file_path,
            output_format
        )
        
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["message"] = "Транскрибация завершена!"
        tasks[task_id]["progress"] = 100
        tasks[task_id]["result"] = {
            "transcript": transcript_data,
            "output_path": str(output_file_path)
        }
        
        logger.info(f"✅ Транскрибация задачи {task_id} завершена. Результат: {output_file_path}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке задачи {task_id}: {e}")
        tasks[task_id]["status"] = "error"
        tasks[task_id]["message"] = f"Ошибка при транскрибации: {e}"
        tasks[task_id]["progress"] = 0
    finally:
        # Очистка временного файла
        if Path(video_file_path).exists():
            os.remove(video_file_path)
            logger.info(f"🧹 Временный файл удален: {video_file_path}")

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """Получение статуса задачи"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    return JSONResponse(content=tasks[task_id])

@app.get("/api/download/{task_id}")
async def download_transcript(task_id: str):
    """Скачивание результата транскрибации"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    task = tasks[task_id]
    if task["status"] != "completed" or not task["result"] or not task["result"]["output_path"]:
        raise HTTPException(status_code=404, detail="Файл не найден или задача не завершена")
    
    file_path = Path(task["result"]["output_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл результата не найден на сервере")
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )

@app.get("/api/tasks")
async def get_all_tasks():
    """Получение всех задач"""
    return JSONResponse(content=tasks)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086, reload=True)
