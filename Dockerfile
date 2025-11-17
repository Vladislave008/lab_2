# Используем alpine образ для уменьшения размера
FROM python:3.11-alpine

# Метаданные
LABEL maintainer="vayashnov@mai.education"
LABEL version="1.0.0"
LABEL description="Bash shell simulator in Python"

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только requirements.txt сначала для лучшего кэширования
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Переменная среды для корректной работы импортов
ENV PYTHONPATH=/app/src

# Создаем не-root пользователя для безопасности
RUN adduser -D -s /bin/sh user && \
    chown -R user:user /app
USER user

# HEALTHCHECK для мониторинга
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Указываем команду запуска
CMD ["python", "-m", "main"]
