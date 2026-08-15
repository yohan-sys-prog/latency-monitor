FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir Flask>=3.0.0

EXPOSE 8000

CMD ["python3", "-m", "application.dashboard"]
