from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import random
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

# Модели
class AuthRequest(BaseModel):
    name: str
    password: str  # ← ОЖИДАЕТ "password"

class BetRequest(BaseModel):
    amount: float

class PromoRequest(BaseModel):
    code: str

# Хранилище
DATA_FILE = "crash_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "users": {},
        "promo_codes": {
            "2026": {"amount": 500, "used": []},
            "2025": {"amount": 500, "used": []},
            "6.12": {"amount": 250, "used": []},
            "+10": {"amount": 250, "used": []},
            "250": {"amount": 250, "used": []},
        },
        "top_x": [],
        "x_history": [],
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
        # Глобальное состояние раунда (упрощённое, без цикла)
current_round = {
    "status": "bet",
    "multiplier": 1.0,
    "bet_time": 6,
    "bets": [],
    "crash_at": None,
}

@app.get("/api/round")
def get_round():
    return {
        "status": current_round["status"],
        "multiplier": current_round["multiplier"],
        "bet_time": current_round["bet_time"],
        "bets": current_round["bets"],
        "crashX": current_round["crash_at"],
        "xHistory": load_data().get("x_history", []),
    }

# Авторизация
@app.post("/api/auth/register")
def register(auth: AuthRequest):
    if not auth.name or not auth.password:
        raise HTTPException(400, "Введите имя и пароль")
    data = load_data()
    if auth.name in data["users"]:
        raise HTTPException(400, "Игрок существует")
    data["users"][auth.name] = {
        "pass": auth.password,
        "balance": 500,
        "total_win": 0,
        "level": 0,
        "history": [],
        "achievements": {},
        "cases": []
    }
    save_data(data)
    return {"status": "ok"}

@app.post("/api/auth/login")
def login(auth: AuthRequest, response: Response):
    data = load_data()
    if auth.name not in data["users"]:
        raise HTTPException(400, "Игрок не найден")
    if data["users"][auth.name]["pass"] != auth.password:
        raise HTTPException(400, "Неверный пароль")
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

# Ставка
@app.post("/api/round/bet")
def place_bet(request: Request, bet: BetRequest):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(401, "Не авторизован")
    data = load_data()
    if session not in data["users"]:
        raise HTTPException(401, "Сессия устарела")
    if bet.amount < 10:
        raise HTTPException(400, "Минимум 10")
    if bet.amount > data["users"][session]["balance"]:
        raise HTTPException(400, "Недостаточно средств")
    data["users"][session]["balance"] -= bet.amount
    current_round["bets"].append({"name": session, "amount": bet.amount, "cashed": False})
    save_data(data)
    return {"status": "ok"}

# Вывод
@app.post("/api/round/cashout")
def cash_out(request: Request):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(401, "Не авторизован")
    for bet in current_round["bets"]:
        if bet["name"] == session and not bet["cashed"]:
            win = bet["amount"] * current_round["multiplier"]
            bet["cashed"] = True
            data = load_data()
            data["users"][session]["balance"] += win
            save_data(data)
            return {"win": win, "multiplier": current_round["multiplier"]}
    raise HTTPException(400, "Нет активной ставки")

# Промокод
@app.post("/api/promo")
def use_promo(request: Request, promo: PromoRequest):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(401, "Не авторизован")
    data = load_data()
    code = promo.code.strip().upper()
    if code not in data["promo_codes"]:
        raise HTTPException(400, "Неверный промокод")
    if session in data["promo_codes"][code]["used"]:
        raise HTTPException(400, "Уже использован")
    data["promo_codes"][code]["used"].append(session)
    data["users"][session]["balance"] += data["promo_codes"][code]["amount"]
    save_data(data)
    return {"amount": data["promo_codes"][code]["amount"]}

# ТОПы
@app.get("/api/top/x")
def top_x():
    data = load_data()
    return sorted(data.get("top_x", []), key=lambda x: x["x"], reverse=True)[:20]

@app.get("/api/top/balance")
def top_balance():
    data = load_data()
    return sorted(
        [{"name": n, "balance": u["balance"]} for n, u in data["users"].items()],
        key=lambda x: x["balance"],
        reverse=True
    )[:20]

# Health check
@app.get("/health")
def health():
    return {"status": "ok", "message": "Server is running"}
