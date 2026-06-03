# ProfilingService (scaffold)

Minimal demo service used as an example to show CI/CICD + containerization.

Run locally:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Build Docker image:

```bash
docker build -t profiling-service:local .
```

Run tests:

```bash
pip install -r requirements.txt
pytest -q
```
