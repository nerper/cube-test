# Caching Microservice

A FastAPI microservice that caches transformer function results and generates interleaved payloads from string lists.

## Features

- **Payload Generation**: Transform and interleave two lists of strings
- **Transformation Caching**: Cache individual string transformations to avoid redundant processing
- **Payload Deduplication**: Identical inputs return the same payload ID
- **Async Architecture**: Built with async SQLAlchemy for high-performance database operations

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start the application and PostgreSQL database
docker-compose up --build

# The API is available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

### Local Development

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy and modify as needed)
cp .env.example .env

# Start PostgreSQL (using Docker)
docker run -d --name postgres-dev \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=caching_service \
  -p 5432:5432 \
  postgres:15-alpine

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload
```

## API Endpoints

### Create Payload

**POST** `/payload`

Create a new payload by transforming and interleaving two string lists.

**Request Body:**
```json
{
  "list1": ["first string", "second string", "third string"],
  "list2": ["other string", "another string", "last string"]
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "cached": false
}
```

- `id`: Unique identifier for the generated payload
- `cached`: `true` if this exact payload was previously generated

### Get Payload

**GET** `/payload/{id}`

Retrieve a previously generated payload.

**Response (200 OK):**
```json
{
  "output": "FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING, THIRD STRING, LAST STRING"
}
```

### Health Check

**GET** `/health`

Check if the service is running.

**Response:**
```json
{
  "status": "healthy"
}
```

## Architecture

### Processing Flow

1. **Input Validation**: Both lists must be non-empty and have equal length
2. **Deduplication Check**: Compute hash of inputs and check for existing payload
3. **Transformation**: Each string is transformed to uppercase (with caching)
4. **Interleaving**: Results are interleaved: `[a1, b1, a2, b2, ...]`
5. **Storage**: Payload is stored with its unique identifier

### Database Schema

**transform_cache**: Caches individual string transformations
- `id`: UUID primary key
- `input_string`: Original string (unique, indexed)
- `transformed_string`: Transformed result
- `created_at`: Timestamp

**payloads**: Stores generated payloads
- `id`: UUID primary key (returned to client)
- `input_hash`: SHA256 hash of inputs (unique, indexed)
- `list1_json`, `list2_json`: Original inputs
- `output`: Generated interleaved string
- `created_at`: Timestamp

## Testing

```bash
# Install test dependencies (included in requirements.txt)
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

### Test Structure

- `tests/test_transformer.py`: Unit tests for transformation caching
- `tests/test_payload.py`: Unit tests for payload generation logic
- `tests/test_api.py`: Integration tests for API endpoints

Tests use SQLite in-memory database for isolation and speed.

## Configuration

Environment variables (can be set in `.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/caching_service` |
| `TRANSFORMER_DELAY` | Artificial delay for transformer (seconds) | `0.1` |

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Settings configuration
│   ├── database.py          # Async database session management
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic
│   │   ├── transformer.py   # String transformation with caching
│   │   └── payload.py       # Payload generation and storage
│   └── routers/             # API route definitions
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # App + PostgreSQL orchestration
└── requirements.txt         # Python dependencies
```

## Design Decisions

1. **Async SQLAlchemy**: Chosen over sync version for better performance with FastAPI's async nature

2. **SHA256 for deduplication**: Provides deterministic, collision-resistant hashing of inputs

3. **Separate transform cache**: Allows reuse of transformations across different payloads

4. **SQLite for tests**: Simplifies CI/CD without requiring containerized PostgreSQL for unit tests

5. **UUID for identifiers**: Provides globally unique, non-sequential IDs without central coordination

## Potential Improvements

- Add TTL (time-to-live) for cached transformations
- Implement batch transformation for better performance
- Add metrics/monitoring endpoints
- Support for different transformation strategies
- Rate limiting for the API endpoints

