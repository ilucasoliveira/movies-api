# Movies API

REST API for managing watched movies and TV series, built with FastAPI, PostgreSQL, Redis and Docker.

Each movie can be linked to multiple genres through a many-to-many relationship, and list endpoints are served from a Redis cache that is invalidated on every write.

## Stack

| Layer        | Technology                     |
| ------------ | ------------------------------ |
| Language     | Python 3.14                    |
| Framework    | FastAPI                        |
| ORM          | SQLAlchemy 2.0 (async)         |
| Database     | PostgreSQL 18 (asyncpg driver) |
| Cache        | Redis 8                        |
| Validation   | Pydantic v2                    |
| Dependencies | Poetry                         |
| Runtime      | Docker + Docker Compose        |

## Features

- Full async stack, from the HTTP layer down to the database driver
- Many-to-many relationship between movies and genres, with an association table
- Cache-aside strategy backed by Redis, with a 30 second TTL
- Cache invalidation on create, update and delete
- Closed genre list: movies can only reference genres that already exist
- HTTP Basic authentication on every resource endpoint
- Partial updates via PATCH, so clients only send the fields they want to change

## Running the project

You need Docker and Docker Compose installed.

```bash
git clone https://github.com/ilucasoliveira/movies-api.git
cd movies-api
cp .env.example .env
docker compose up --build
```

Fill in the credentials in `.env` before starting. Note that `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` must match the values inside `DATABASE_URL`.

Once the containers are up:

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs

Tables are created automatically on startup.

## Environment variables

| Variable            | Description                                                                                     |
| ------------------- | ----------------------------------------------------------------------------------------------- |
| `DATABASE_URL`      | Full async connection string, e.g. `postgresql+asyncpg://user:password@db:5432/movies_database` |
| `POSTGRES_USER`     | Database user, must match `DATABASE_URL`                                                        |
| `POSTGRES_PASSWORD` | Database password, must match `DATABASE_URL`                                                    |
| `POSTGRES_DB`       | Database name, must match `DATABASE_URL`                                                        |
| `APP_USERNAME`      | Username for HTTP Basic authentication                                                          |
| `APP_PASSWORD`      | Password for HTTP Basic authentication                                                          |
| `REDIS_HOST`        | Redis hostname, `redis` inside Docker Compose                                                   |
| `REDIS_PORT`        | Redis port, defaults to `6379`                                                                  |

## Endpoints

All endpoints except the health check require HTTP Basic authentication.

| Method   | Path           | Description                      | Success |
| -------- | -------------- | -------------------------------- | ------- |
| `GET`    | `/`            | Health check                     | 200     |
| `POST`   | `/genres`      | Create a genre                   | 201     |
| `GET`    | `/genres`      | List all genres                  | 200     |
| `POST`   | `/movies`      | Create a movie                   | 201     |
| `GET`    | `/movies`      | List all movies (cached)         | 200     |
| `GET`    | `/movies/{id}` | Retrieve a single movie (cached) | 200     |
| `PATCH`  | `/movies/{id}` | Partially update a movie         | 200     |
| `DELETE` | `/movies/{id}` | Delete a movie                   | 204     |

### Error responses

| Code | When                                 |
| ---- | ------------------------------------ |
| 400  | One or more genre names do not exist |
| 401  | Missing or invalid credentials       |
| 404  | Movie not found                      |
| 409  | Duplicate movie title or genre name  |

### Example: creating a movie

Genres must be created first, since the API rejects unknown genre names.

```bash
curl -X POST http://localhost:8000/movies \
  -u "$APP_USERNAME:$APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Dune: Part Two",
    "year": 2024,
    "genres": ["fiction", "drama"],
    "rating": 9.5,
    "status": "watched",
    "watched_at": "2026-08-19"
  }'
```

Response:

```json
{
  "title": "Dune: Part Two",
  "year": 2024,
  "genres": ["fiction", "drama"],
  "rating": 9.5,
  "status": "watched",
  "watched_at": "2026-08-19",
  "id": 1
}
```

### Movie fields

| Field        | Type            | Required | Notes                                                                 |
| ------------ | --------------- | -------- | --------------------------------------------------------------------- |
| `title`      | string          | yes      | 2 to 100 characters, unique                                           |
| `year`       | integer         | yes      | 1900 or later                                                         |
| `genres`     | list of strings | yes      | Names must already exist                                              |
| `rating`     | float           | no       | 0 to 10                                                               |
| `status`     | enum            | no       | `want to watch`, `watching` or `watched`. Defaults to `want to watch` |
| `watched_at` | date            | no       | Format `YYYY-MM-DD`                                                   |

## How the cache works

The API follows the cache-aside pattern:

1. The endpoint asks Redis for the key first
2. On a hit, the cached payload is returned and PostgreSQL is never touched
3. On a miss, PostgreSQL is queried, the result is written to Redis and then returned

Two key shapes are used:

- `movies` holds the full listing
- `movie:{id}` holds a single movie

Any write operation deletes both keys, so the next read repopulates them from the database. The 30 second TTL is a safety net, not the primary invalidation mechanism.

## Project structure

```
.
├── main.py              # FastAPI app, lifespan and endpoints
├── models.py            # SQLAlchemy models and the association table
├── schemas.py           # Pydantic schemas for input and output
├── database.py          # Async engine, session factory and table creation
├── cache.py             # Redis client and generic cache helpers
├── auth.py              # HTTP Basic authentication dependency
├── docker-compose.yml   # API, PostgreSQL and Redis services
└── Dockerfile           # API image
```

## Roadmap

- [ ] Automated tests with pytest
- [ ] Database migrations with Alembic
- [ ] Replace debug prints with structured logging
- [ ] Filtering and pagination on the movie listing

## Author

Lucas de Oliveira Pimentel
[GitHub](https://github.com/ilucasoliveira)
