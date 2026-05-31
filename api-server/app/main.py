from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, classes, courses, dashboard, evaluation, homework, reports, reviews, tasks, users
from app.core.bootstrap import bootstrap_database
from app.core.config import settings

@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_database()
    yield


app = FastAPI(title="Smart Calligraphy API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


if settings.secure_static:

    @app.middleware("http")
    async def protect_uploads(request: Request, call_next):
        if request.url.path.startswith("/uploads/"):
            auth_header = request.headers.get("authorization", "")
            token = auth_header.replace("Bearer ", "").strip()
            if not token.startswith("dev-token-"):
                return JSONResponse(status_code=403, content={"code": 1, "message": "无权访问静态资源，请先登录。", "data": None})
        return await call_next(request)


storage_dir = Path(settings.storage_root)
if not storage_dir.is_absolute():
    storage_dir = Path(__file__).resolve().parents[1] / settings.storage_root
storage_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=storage_dir), name="uploads")


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["courses"])
app.include_router(classes.router, prefix="/api/v1/classes", tags=["classes"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(homework.router, prefix="/api/v1/homework", tags=["homework"])
app.include_router(evaluation.router, prefix="/api/v1/evaluation", tags=["evaluation"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])


@app.get("/")
def root():
    return {"code": 0, "message": "ok", "data": {"service": "api-server"}}
