FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsodium-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY pyproject.toml uv.lock* ./

# Sincronizar dependencias (uv ya está instalado)
RUN uv sync --frozen --no-dev

# Copiar código
COPY . .

# Variables de entorno para usar el venv
ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "bot.main"]