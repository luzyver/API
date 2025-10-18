from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import health, auth, projects, images, messages, comments, experiences, blog, stats

settings = get_settings()

app = FastAPI(
    title="Porto API",
    description="Portfolio API built with FastAPI",
    version="1.0.0",
    root_path="/porto",
    root_path_in_servers=False,
    servers=[
        {"url": "https://api.luzyver.dev/porto", "description": "Production"},
        {"url": "http://localhost:8000", "description": "Development (Local)"}
    ]
)

# Middleware to block api-porto.luzyver.dev
@app.middleware("http")
async def block_old_domain(request: Request, call_next):
    host = request.headers.get("host", "")
    if host.startswith("api-porto.luzyver.dev"):
        return Response(
            content='{"detail":"This domain is deprecated. Please use https://api.luzyver.dev/porto"}',
            status_code=403,
            media_type="application/json"
        )
    return await call_next(request)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers without prefix (gateway handles it)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(images.router)
app.include_router(messages.router)
app.include_router(comments.router)
app.include_router(experiences.router)
app.include_router(blog.router)
app.include_router(stats.router)


@app.get("/")
async def root():
    return {
        "message": "Porto API",
        "docs": "/docs",
        "version": "1.0.0"
    }
