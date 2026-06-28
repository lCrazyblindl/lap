# pet-zoo

A small zoo management API built with FastAPI. CRUD for monkeys, lions, tigers and elephants, plus a combined `GET /animals` endpoint. Data is persisted to a local JSON file (`data/zoo.json`) — no real database.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the Swagger UI.

## Run with Docker

```bash
docker build -t pet-zoo .
docker run -p 8000:8000 pet-zoo
```

Data written inside the container is lost when the container is removed. To persist `data/zoo.json` across container restarts, bind-mount the data folder:

```powershell
# PowerShell
docker run -p 8000:8000 -v "${PWD}\data:/app/data" pet-zoo
```

```bash
# macOS/Linux shell
docker run -p 8000:8000 -v "$(pwd)/data:/app/data" pet-zoo
```

> Git Bash on Windows mangles the `:/app/data` part of `-v` arguments (MSYS auto path-conversion). Use the PowerShell command above, or prefix the Git Bash command with `MSYS_NO_PATHCONV=1`.

## Endpoints

- `/monkeys`, `/lions`, `/tigers`, `/elephants` — full CRUD (`GET`, `GET /{id}`, `POST`, `PUT /{id}`, `DELETE /{id}`)
- `/animals` — `GET` only, returns all animals across every species
- `/docs` — Swagger UI
- `/redoc` — ReDoc
