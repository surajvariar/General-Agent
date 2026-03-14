FROM python:3.13-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock /app/

RUN pip install uv

RUN uv sync --frozen

# Stage 2: Runtime Stage
FROM python:3.13-slim

WORKDIR /app

# Copy the environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Security: Create and switch to a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# Copy application code (do this last to maximize cache)
COPY src/ .

# Expose Streamlit's default port
EXPOSE 8501

# Healthcheck using curl (standard for Streamlit)
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]