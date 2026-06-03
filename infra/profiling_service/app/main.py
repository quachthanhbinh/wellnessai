from fastapi import FastAPI

app = FastAPI(title="ProfilingService - scaffold")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    return {"status": "ready"}


@app.get("/v1/profile/ping")
async def ping():
    return {"message": "profiling service alive"}
