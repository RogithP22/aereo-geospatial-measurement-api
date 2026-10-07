# Geospatial File Measurement API

A FastAPI-based backend application that accepts geospatial files in KML and Shapefile ZIP formats, processes their features, handles coordinate reference systems safely, and calculates measurements for supported geometries.

## Features

- Upload `.kml` files
- Upload Shapefile `.zip` archives
- Extract and process geospatial features
- Store file metadata and feature properties
- Detect geometry types
- Calculate polygon area
- Calculate LineString length
- Handle Point geometries without measurement
- Transform geographic CRS to a suitable projected CRS before metric calculations
- Validate required Shapefile companion files
- Secure ZIP extraction against path traversal / Zip Slip attacks
- Graceful error handling
- UUID-based file identification
- SQLite database for development
- Automated API tests
- Docker support
- Interactive Swagger API documentation

## Technology Stack

- **Python 3.11**
- **FastAPI** - REST API framework
- **SQLAlchemy** - Database ORM
- **Pydantic** - Data validation
- **GeoPandas** - Geospatial data processing
- **Shapely** - Geometry operations
- **PyProj** - Coordinate reference system transformation
- **Pyogrio** - Geospatial file I/O
- **SQLite** - Development database
- **Pytest** - Testing
- **Docker** - Containerization

## Project Structure

```text
aereo-geospatial-measurement-api/
│
├── app/
│   ├── api/
│   │   └── files.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── database.py
│   │   └── models.py
│   ├── schemas/
│   │   └── file.py
│   ├── services/
│   │   ├── file_service.py
│   │   ├── geospatial_service.py
│   │   ├── crs_service.py
│   │   └── measurement_service.py
│   ├── utils/
│   │   └── file_utils.py
│   └── main.py
│
├── sample_data/
│   ├── sample.kml
│   └── sample_shapefile.zip
│
├── tests/
│
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
├── README.md
└── .gitignore