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

# Модели
class AuthRequest(BaseModel):
    name: str
    password: str  # ← правильно

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
        except Exception as e:
            print("⚠️ Load error:", e)
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
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("⚠️ Save error:", e)

# Глобальное состояние игры
current_round = {
    "id": 1,
    "status": "bet",
    "bets": [],
    "crash_at": None,
    "multiplier": 1.0,
    "started_at": None,
    "bet_time": 6,
}
# Игровая логика
def generate_crash_point():
    r = random.random()
    if r < 0.80:
        return round(1 + random.random() * 1.5, 2)
    elif r < 0.98:
        return round(2.5 + random.random() * 47.5, 2)
    else:
        return round(50 + random.random() * 250, 2)

def calculate_multiplier(elapsed):
    return round(1 + elapsed * 2, 2)

@app.on_event("startup")
async def startup():
    asyncio.create_task(game_loop())

async def game_loop():
    global current_round
    while True:
        try:
            if current_round["status"] == "bet":
                await asyncio.sleep(1)
                current_round["bet_time"] -= 1
                if current_round["bet_time"] <= 0:
                    current_round["status"] = "flight"
                    current_round["crash_at"] = generate_crash_point()
                    current_round["started_at"] = time.time()
                    current_round["multiplier"] = 1.0

            elif current_round["status"] == "flight":
                elapsed = time.time() - current_round["started_at"]
                current_round["multiplier"] = calculate_multiplier(elapsed)
                if current_round["multiplier"] >= current_round["crash_at"]:
                    crash_x = current_round["crash_at"]
                    data = load_data()
                    data["x_history"].insert(0, crash_x)
                    if len(data["x_history"]) > 20:
                        data["x_history"] = data["x_history"][:20]
                    for bet in current_round["bets"]:
                        if not bet.get("cashed"):
                            data["top_x"].append({"name": bet["name"], "x": crash_x})
                    if len(data["top_x"]) > 100:
                        data["top_x"] = data["top_x"][-100:]
                    save_data(data)
                    await asyncio.sleep(5)
                    current_round = {
                        "id": current_round["id"] + 1,
                        "status": "bet",
                        "bets": [],
                        "crash_at": None,
                        "multiplier": 1.0,
                        "started_at": None,
                        "bet_time": 6,
                    }
            await asyncio.sleep(0.5)
        except Exception as e:
            print("⚠️ Game loop error:", e)
            await asyncio.sleep(2)

# Эндпоинты
@app.get("/api/round")
def get_round():
    data = load_data()
    return {
        "status": current_round["status"],
        "multiplier": current_round["multiplier"],
        "bet_time": current_round["bet_time"],
        "bets": current_round["bets"],
        "crashX": current_round["crash_at"],
        "xHistory": data["x_history"],
    }

@app.post("/api/round/bet")
def place_bet(request: Request, bet: BetRequest):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(401, "Не авторизован")
    data = load_data()
    if session not in data["users"]:
        raise HTTPException(401, "Сессия устарела")
    user = data["users"][session]
    if bet.amount < 10:
        raise HTTPException(400, "Минимум 10")
    if bet.amount > user["balance"]:
        raise HTTPException(400, "Недостаточно средств")
    user["balance"] -= bet.amount
    current_round["bets"].append({"name": session, "amount": bet.amount, "cashed": False})
    save_data(data)
    return {"status": "ok"}

@app.post("/api/round/cashout")
def cash_out(request: Request):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(401, "Не авторизован")
    if current_round["status"] != "flight":
        raise HTTPException(400, "Вывод недоступен")
    for bet in current_round["bets"]:
        if bet["name"] == session and not bet.get("cashed"):
            win = bet["amount"] * current_round["multiplier"]
            bet["cashed"] = True
            data = load_data()
            data["users"][session]["balance"] += win
            save_data(data)
            return {"win": win, "multiplier": current_round["multiplier"]}
    raise HTTPException(400, "Нет активной ставки")

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
    response.set_cookie(
        key="session",
        value=auth.name,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400
    )
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

@app.get("/health")
def health():
    return {"status": "ok", "message": "Game server is running"}
