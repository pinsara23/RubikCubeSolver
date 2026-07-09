FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System libs required by OpenCV + build tools for packages with C extensions (kociemba)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY Color_Extraction_With_Video.py /app/
COPY tables.json /app/

RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    opencv-python-headless \
    numpy \
    kociemba \
    twophase

EXPOSE 5000

CMD ["python", "Color_Extraction_With_Video.py"]
