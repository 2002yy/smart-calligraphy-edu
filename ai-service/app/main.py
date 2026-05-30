from fastapi import FastAPI

from app.api.routes import preprocess, qa, recommend, score, segment

app = FastAPI(title="Smart Calligraphy AI Service", version="0.1.0")

app.include_router(preprocess.router, prefix="/ai/v1/preprocess", tags=["preprocess"])
app.include_router(segment.router, prefix="/ai/v1/segment", tags=["segment"])
app.include_router(score.router, prefix="/ai/v1/score", tags=["score"])
app.include_router(recommend.router, prefix="/ai/v1/recommend", tags=["recommend"])
app.include_router(qa.router, prefix="/ai/v1/qa", tags=["qa"])


@app.get("/")
def root():
    return {"code": 0, "message": "ok", "data": {"service": "ai-service"}}

