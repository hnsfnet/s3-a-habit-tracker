from fastapi import APIRouter, Request, Form, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date, timedelta
from jose import JWTError, jwt

from app.database import get_db
from app.services.auth_service import (
    create_user,
    authenticate_user,
    create_access_token,
    get_user_by_username,
    SECRET_KEY,
    ALGORITHM,
)
from app.services.habit_service import get_habits_with_stats, calculate_current_streak, get_habits_by_user
from app.services.habit_log_service import get_weekly_completion, get_user_logs_for_date
from app.services.challenge_service import get_challenges_with_stats
from app.services.stats_service import get_overall_stats
from app.schemas import UserCreate
from app.models import User

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="app/templates")


def get_token_from_cookie(request: Request) -> str | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    if token.startswith("Bearer "):
        return token[7:]
    return token


def get_current_user_from_cookie(request: Request, db: Session) -> User | None:
    token = get_token_from_cookie(request)
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    return get_user_by_username(db, username=username)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "user": None, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "user": None, "error": "用户名或密码错误"},
        )
    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60 * 24 * 7,
    )
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "user": None, "error": None})


@router.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "user": None, "error": "两次输入的密码不一致"},
        )
    if len(password) < 6:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "user": None, "error": "密码长度不能少于6位"},
        )
    existing = get_user_by_username(db, username)
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "user": None, "error": "用户名已被注册"},
        )
    user_create = UserCreate(username=username, password=password)
    user = create_user(db, user_create)
    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60 * 24 * 7,
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    token = get_token_from_cookie(request)
    
    habits = get_habits_with_stats(db, user.id)
    total_habits = len(habits)
    
    today = date.today()
    today_logs = get_user_logs_for_date(db, user.id, today)
    today_completed = len(today_logs)
    
    weekly_data = get_weekly_completion(db, user.id)
    week_total = sum(weekly_data.values())
    
    max_streak = 0
    for habit in habits:
        if habit.current_streak > max_streak:
            max_streak = habit.current_streak
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "access_token": token,
            "habits": habits,
            "total_habits": total_habits,
            "today_completed": today_completed,
            "week_total": week_total,
            "max_streak": max_streak,
        },
    )


@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    token = get_token_from_cookie(request)
    habits = get_habits_by_user(db, user.id)
    
    return templates.TemplateResponse(
        "calendar.html",
        {"request": request, "user": user, "access_token": token, "habits": habits},
    )


@router.get("/challenges", response_class=HTMLResponse)
async def challenges_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    token = get_token_from_cookie(request)
    habits = get_habits_by_user(db, user.id)
    
    return templates.TemplateResponse(
        "challenges.html",
        {"request": request, "user": user, "access_token": token, "habits": habits},
    )


@router.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    token = get_token_from_cookie(request)
    habits = get_habits_by_user(db, user.id)
    
    return templates.TemplateResponse(
        "stats.html",
        {"request": request, "user": user, "access_token": token, "habits": habits},
    )
