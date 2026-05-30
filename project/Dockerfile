# CVE Severity Triage API — inference service.
# Host (for docker): pip install -r requirements.txt 
# Docker: docker compose up --build
#   First build installs deps inside the image (slow once).
#   Later rebuilds reuse the cached pip layer if requirements.txt unchanged.

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --retries 10 --timeout 0 -r requirements.txt

COPY configs/ configs/
COPY src/ src/
COPY artifacts/cve_model.joblib artifacts/cve_model.joblib

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["python", "-m", "src.service"]
