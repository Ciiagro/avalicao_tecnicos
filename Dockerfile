FROM python:3.12-slim

# Evita .pyc e garante que os logs apareçam em tempo real (sem buffer)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências de sistema (psycopg[binary] geralmente não precisa compilar,
# mas libpq-dev garante compatibilidade em qualquer ambiente)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia só o requirements primeiro, pra aproveitar cache do Docker
# (só reinstala as libs se o requirements.txt mudar)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
