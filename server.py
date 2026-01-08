from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import random
import asyncio
import time

app = FastAPI()

# CORS — только ваши домены
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://crash-finerx.netlify.app",
        "https://web.telegram.org"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Простая модель
class AuthRequest(BaseModel):
    name: str
    password: str

# Хранилище
DATA_FILE = "crash_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "users": {},
        "promo_codes": {"2026": {"amount": 500, "used": []}},
        "top_x": [],
        "x_history": [],
    }

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("⚠️ Save error:", e)

# Игровое состояние
current_round = {"status": "bet", "multiplier": 1.0, "bet_time": 6, "bets": []}

# Упрощённый раунд (без фонового цикла — для отладки)
@app.get("/api/round")
def get_round():
    return current_round

# Простейшая авторизация — без game_loop!
@app.post("/api/auth/register")
def register(auth: AuthRequest):
    data = load_data()
    if auth.name in data["users"]:
        raise HTTPException(400, "Игрок существует")
    data["users"][auth.name] = {"pass": auth.password, "balance": 500}
    save_data(data)
    return {"status": "ok"}

@app.post("/api/auth/login")
def login(auth: AuthRequest, response: Response):
    data = load_data()
    if auth.name not in data["users"] or data["users"][auth.name]["pass"] != auth.password:
        raise HTTPException(400, "Ошибка входа")
    response.set_cookie(key="session", value=auth.name, httponly=True, max_age=86400)
    return {"status": "ok"}

@app.get("/api/user")
def get_user(request: Request):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(401, "Не авторизован")
    data = load_data()
    if session not in data["users"]:
        raise HTTPException(401, "Сессия устарела")
    user = data["users"][session].copy()
    user.pop("pass", None)
    return user

# Health check — для Render
@app.get("/health")
def health():
    return {"status": "ok", "message": "Server is running"}
