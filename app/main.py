from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.models import User, Habit, HabitLog, Challenge
from app.routers import auth, habits, habit_logs, challenges, stats
from app.routers.pages import router as pages_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Habit Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(habit_logs.router)
app.include_router(challenges.router)
app.include_router(stats.router)
app.include_router(pages_router)


@app.get("/")
async def root():
    return {"message": "Habit Tracker API"}
