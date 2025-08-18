FROM python:3.11-slim

# Függőségek
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Könyvtár beállítás
WORKDIR /app

# Követelmények és fájlok másolása
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#COPY input.mp3 .

COPY . .

# Port, amit a FastAPI használ (csak dokumentációs céllal)
EXPOSE 8000

# Alkalmazás futtatása uvicorn-nal
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]