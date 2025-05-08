FROM python:3.11-slim

RUN useradd -m -u 1000 -s /bin/bash appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*
COPY . .
RUN chown -R appuser:appuser /app
RUN chmod +x entrypoint.sh
# Commenter USER appuser pour exécuter en tant que root
# USER appuser
EXPOSE 5000
ENTRYPOINT ["python", "app.py"]