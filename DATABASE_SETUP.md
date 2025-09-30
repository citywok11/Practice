# Database Container for Destinations (Postgres)

This change moves the destinations data out of in-memory storage and into a simple Postgres database container, without modifying `src/main.py`.

## What changed

- Added a minimal Docker Compose file to run Postgres locally:
  - File: `docker-compose.yml`
  - Service name: `db`
  - Image: `postgres:16-alpine`
  - Credentials and database: `travel`/`travel` on DB `travel`
  - Port: `5432` exposed to host
  - Persistent volume: `pgdata` so your data survives container restarts
  - Healthcheck to wait for DB readiness

- Refactored `src/models.py` to back the `destinations` data with Postgres:
  - It now exposes `destinations` as a list-like object that works with existing code paths in `main.py` (iteration, `len()`, indexing, and `append`).
  - On import, it connects to the DB, ensures the `destinations` table exists, seeds initial rows if empty, and caches results for efficient reads.
  - Writes via `append()` are inserted into the DB and the in-memory cache is refreshed.

- Added Python dependencies in `requirements.txt`:
  - `psycopg2-binary` to connect to Postgres
  - `Flask` (already used by your app)

## Why Postgres (and not MySQL)

- Both MySQL and Postgres are fine for this scale. Postgres is chosen here for the smallest surface area and speed to value:
  - Official lightweight image (`postgres:16-alpine`)
  - Built-in `JSONB` type for storing the `attractions` list as-is
  - Very simple schema and queries
  - Excellent local dev ergonomics with Docker Compose

If you prefer MySQL, we can swap the container and use `mysqlclient` or `aiomysql` accordingly. Postgres provided the cleanest path for the existing Python data shape (JSON for `attractions`).

## How it works (contract)

- `src/main.py` remains unchanged. It imports `from models import destinations`.
- `src/models.py` now defines `destinations` as a list-like wrapper around the database:
  - Supports: iteration, `len(destinations)`, indexing (`destinations[0]`), `append(dict)`
  - `append()` inserts into the DB and updates cache
  - Data shape per item:
    ```json
    {
      "id": int,
      "name": str,
      "country": str,
      "attractions": list[str]
    }
    ```

## Run it

1) Start the database container

```bash
docker compose up -d
```

This launches Postgres at `localhost:5432` with DB `travel`, user `travel`, password `travel`.

2) Install Python dependencies (inside your virtualenv)

```bash
pip install -r requirements.txt
```

3) Run your Flask app as you do today (unchanged)

```bash
python -m flask --app src.main run --host 0.0.0.0 --port 5001 --debug
```

Or run `src/main.py` directly if you have that workflow.

The app will import `models`, which auto-creates the table and seeds three initial destinations if the table is empty.

## Configuration

You can override connection settings using environment variables:

- `DB_HOST` (default `127.0.0.1`)
- `DB_PORT` (default `5432`)
- `POSTGRES_DB` or `DB_NAME` (default `travel`)
- `POSTGRES_USER` or `DB_USER` (default `travel`)
- `POSTGRES_PASSWORD` or `DB_PASSWORD` (default `travel`)

The defaults line up with `docker-compose.yml`.

## Schema

A single table with a primary key on `id` and a JSONB column for `attractions`:

```sql
CREATE TABLE IF NOT EXISTS destinations (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  country TEXT NOT NULL,
  attractions JSONB NOT NULL DEFAULT '[]'::jsonb
);
```

## Notes and trade-offs

- Simplicity first: no ORM, just the minimal `psycopg2-binary` driver and a tiny list-like wrapper.
- Reads are cached on import. After `append`, the cache is refreshed. If you need live-updating reads across multiple app instances, we can add explicit `refresh()` calls or lighter-weight query patterns.
- `id` generation remains in `main.py` (as before) using `max(id)+1`. In a multi-writer scenario, we would switch to `SERIAL`/`GENERATED ALWAYS AS IDENTITY` and return the inserted `id` from the DB to avoid conflicts.

## Testing quickly

With the container running, a quick Python check:

```python
from src.models import destinations
print(len(destinations))
print(destinations[0])
new_id = max(d['id'] for d in destinations) + 1
destinations.append({
    'id': new_id,
    'name': 'Berlin',
    'country': 'Germany',
    'attractions': ['Brandenburg Gate']
})
print(len(destinations))
print(destinations[-1])
```

You should see the length increase and the last item reflect the new row.

## Next steps (optional)

- Switch to DB-side auto-incremented IDs and update `main.py` to stop computing `max(id)`
- Add basic integration tests exercising GET and POST against the running API with a temporary DB
- Add migrations (e.g., Alembic) if the schema grows
