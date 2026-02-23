from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.events import router as event_router
from app.api.stats import router as stats_router

app = FastAPI(title="LifeOS")

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(event_router)
app.include_router(stats_router)

@app.get("/health")
def health():
    return {"status": "ok"}