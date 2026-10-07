FROM python:3.11-slim

# Install system dependencies required for geospatial libraries (GDAL, Geos, Proj)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    gdal-bin \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:main", "--host", "0.0.0.0", "--port", "8000"]