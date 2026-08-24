FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 RPG_DATA_DIR=/app/data
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python -m compileall -q backend
EXPOSE 5000
CMD ["gunicorn","-w","2","-b","0.0.0.0:5000","backend.app:app"]
