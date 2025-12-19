# Caching Microservice

This is a small FastAPI service that takes two lists of strings, transforms them, interleaves the results, and caches everything so repeated requests don’t redo the work.

Think of it like this:
you give it two lists, it uppercases each string, mixes them together, and remembers the result so the same input always gives the same output.



## What it does

- Generates payloads from two string lists by transforming and interleaving them
- Caches transformations so the same string isn’t processed twice
- Deduplicates payloads so identical inputs always return the same payload ID
- Built async-first using FastAPI and async SQLAlchemy



## Quick example

Request payload:

{
  "list1": ["first", "second"],
  "list2": ["hello", "world"]
}

What happens:
- Each string is uppercased
- Results are interleaved

Final output:

FIRST, HELLO, SECOND, WORLD

If you send the exact same input again, you’ll get the same payload ID instead of creating a new one.



## Running it

### With Docker (recommended)

docker-compose up --build

API runs at:
http://localhost:8000

Swagger docs:
http://localhost:8000/docs



### Local setup

python -m venv venv  
source venv/bin/activate  
pip install -r requirements.txt  

cp .env.example .env  

docker run -d --name postgres-dev  
-e POSTGRES_USER=postgres  
-e POSTGRES_PASSWORD=postgres  
-e POSTGRES_DB=caching_service  
-p 5432:5432  
postgres:15-alpine  

alembic upgrade head  
uvicorn app.main:app --reload  



## API

### Create a payload

POST /payload

Request body:

{
  "list1": ["first", "second"],
  "list2": ["hello", "world"]
}

Response:

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "cached": false
}

id is the payload identifier  
cached tells you if this input was already processed before



### Get a payload

GET /payload/{id}

Response:

{
  "output": "FIRST, HELLO, SECOND, WORLD"
}



### Health check

GET /health

Response:

{
  "status": "healthy"
}



## How it works (high level)

1. Validates both lists (same length, not empty)
2. Hashes the input to see if it already exists
3. Transforms strings to uppercase using a cache
4. Interleaves results like a1, b1, a2, b2
5. Stores the payload and returns its ID




## Tests

Run all tests:

pytest

Tests cover:
- transformation caching
- payload generation logic
- API behavior

They use an in-memory SQLite database so tests are fast and isolated.


