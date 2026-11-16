FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt requirements-dev.txt ./

# Par defaut, garder pytest pour les tests Docker locaux.
# INSTALL_DEV_DEPS=0 permet une image sans dependances de test.
ARG INSTALL_DEV_DEPS=1

RUN if [ "$INSTALL_DEV_DEPS" = "1" ]; then \
      python -m pip install --no-cache-dir -r requirements-dev.txt; \
    else \
      python -m pip install --no-cache-dir -r requirements.txt; \
    fi

COPY . .

EXPOSE 8000

# Demarrage sans rechargement automatique.
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
