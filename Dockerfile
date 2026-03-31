FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsodium-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Synchronize dependencies (uv is already installed)
RUN uv sync --frozen --no-dev

# Copy code
COPY . .

# Environment variables to use the venv
ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "bot.main"]