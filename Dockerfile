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
# --timeout 60: headroom above /team/chat's NARA_TIME_BUDGET_SECONDS (default
# 20s) — that budget is the real ceiling, this is a second line of defense.
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 60 --access-logfile - wsgi:app
