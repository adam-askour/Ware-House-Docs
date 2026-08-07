FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ghostscript pngquant qpdf tesseract-ocr \
       tesseract-ocr-ara tesseract-ocr-eng tesseract-ocr-fra unpaper \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system dms && useradd --system --gid dms --home-dir /nonexistent dms
COPY requirements/base.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY . /app
RUN mkdir -p /app/var/protected /app/var/quarantine /app/var/static \
    && chown -R dms:dms /app/var

USER dms
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "config.wsgi:application"]
