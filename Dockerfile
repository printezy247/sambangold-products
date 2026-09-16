FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite lives on the Railway volume mounted at /data.
RUN mkdir -p /data
EXPOSE 8080

# Shell form so ${PORT} expands — Railway assigns its own port at runtime.
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --access-logfile - wsgi:app
