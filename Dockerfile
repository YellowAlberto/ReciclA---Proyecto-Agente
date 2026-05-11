FROM python:3.10-slim

# Instalamos las dependencias actualizadas para OpenCV y ONNX
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p imagenes_subidas && chmod 777 imagenes_subidas
RUN chmod +x run.sh
EXPOSE 7860
CMD ["./run.sh"]