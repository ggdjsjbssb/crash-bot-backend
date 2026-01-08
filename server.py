from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import random
import asyncio
import time

app = FastAPI()

# CORS — разрешаем только Netlify и Telegram Web
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
    password: str  # ← правильно, не "pass"

class BetRequest(BaseModel):
    amount: float

class PromoRequest(BaseModel):
    code: str

class CaseRequest(BaseModel):
    caseId: str

class AdminAction(BaseModel):
    target: str
    amount: float

# Хранилище данных
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
        "admin_password": "supersecret"  # ← СМЕНИТЕ НА СВОЙ!
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
    "status": "bet",      # bet / flight / crash
    "bets": [],
    "crash_at": None,
    "multiplier": 1.0,
    "started_at": None,
    "bet_time": 6,
}
# Генерация точки краша
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

# Фоновый игровой цикл
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
                    # Краш произошёл
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

# Эндпоинты игры
@app.get("/api/round")
async def get_round():
    data = load_data()
    return {
        "status": current_round["status"],
        "multiplier": current_round["multiplier"],
        "bet_time": current_round["bet_time"],
        "bets": current_round["bets"],
        "crashX": current_round.get("crash_at"),
        "xHistory": data.get("x_history", []),
    }

@app.post("/api/round/bet")
async def place_bet(request: Request, bet: BetRequest):
    session = request.cookies.get("session")
    if not session or session not in load_data()["users"]:
        raise HTTPException(status_code=401, detail="Не авторизован")
    if current_round["status"] != "bet":
        raise HTTPException(status_code=400, detail="Ставки не принимаются")
    data = load_data()
    user = data["users"][session]
    if bet.amount > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно средств")
    if bet.amount < 10:
        raise HTTPException(status_code=400, detail="Минимум 10")
    user["balance"] -= bet.amount
    current_round["bets"].append({
        "name": session,
        "amount": bet.amount,
        "cashed": False
    })
    save_data(data)
    return {"status": "ok"}

@app.post("/api/round/cashout")
async def cash_out(request: Request):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(status_code=401, detail="Не авторизован")
    if current_round["status"] != "flight":
        raise HTTPException(status_code=400, detail="Нельзя вывести")
    bet = next((b for b in current_round["bets"] if b["name"] == session and not b.get("cashed")), None)
    if not bet:
        raise HTTPException(status_code=400, detail="Нет активной ставки")
    win = bet["amount"] * current_round["multiplier"]
    bet["cashed"] = True
    data = load_data()
    user = data["users"][session]
    user["balance"] += win
    user["total_win"] = user.get("total_win", 0) + (win - bet["amount"])
    user["history"] = [f"✅ Вывел {win:.2f} при x{current_round['multiplier']:.2f}"] + user.get("history", [])[:99]
    save_data(data)
    return {"win": win, "multiplier": current_round["multiplier"]}

# Авторизация
@app.post("/api/auth/register")
async def register(auth: AuthRequest):
    if not auth.name or not auth.password:
        raise HTTPException(status_code=400, detail="Введите имя и пароль")
    data = load_data()
    if auth.name in data["users"]:
        raise HTTPException(status_code=400, detail="Игрок существует")
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
async def login(auth: AuthRequest, response: Response):
    data = load_data()
    if auth.name not in data["users"]:
        raise HTTPException(status_code=400, detail="Игрок не найден")
    if data["users"][auth.name]["pass"] != auth.password:
        raise HTTPException(status_code=400, detail="Неверный пароль")
    response.set_cookie(
        key="session",
        value=auth.name,
        httponly=True,
        secure=True,        # ← обязательно для HTTPS
        samesite="lax",     # ← обязательно для безопасности
        max_age=86400
    )
    return {"status": "ok"}

@app.get("/api/user")
async def get_user(request: Request):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(status_code=401, detail="Не авторизован")
    data = load_data()
    if session not in data["users"]:
        raise HTTPException(status_code=401, detail="Сессия устарела")
    user = data["users"][session].copy()
    del user["pass"]
    return user

# Промокоды
@app.post("/api/promo")
async def use_promo(request: Request, promo: PromoRequest):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(status_code=401, detail="Не авторизован")
    data = load_data()
    code = promo.code.strip().upper()
    if code not in data["promo_codes"]:
        raise HTTPException(status_code=400, detail="Неверный промокод")
    if session in data["promo_codes"][code]["used"]:
        raise HTTPException(status_code=400, detail="Уже использован")
    data["promo_codes"][code]["used"].append(session)
    data["users"][session]["balance"] += data["promo_codes"][code]["amount"]
    save_data(data)
    return {"amount": data["promo_codes"][code]["amount"]}

# Кейсы
@app.post("/api/case")
async def open_case(request: Request, case: CaseRequest):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(status_code=401, detail="Не авторизован")
    data = load_data()
    user = data["users"][session]
    achievements = user.get("achievements", {})
    completed = len(achievements)
    reward = 0
    if case.caseId == "case1" and completed >= 3 and case.caseId not in user.get("cases", []):
        reward = 500
    elif case.caseId == "case2" and completed >= 6 and case.caseId not in user.get("cases", []):
        reward = 1000
    else:
        raise HTTPException(status_code=400, detail="Нельзя открыть")
    user.setdefault("cases", []).append(case.caseId)
    user["balance"] += reward
    save_data(data)
    return {"reward": reward}

# ТОПы
@app.get("/api/top/x")
async def top_x():
    data = load_data()
    return sorted(data.get("top_x", []), key=lambda x: x["x"], reverse=True)[:20]

@app.get("/api/top/balance")
async def top_balance():
    data = load_data()
    players = [{"name": name, "balance": user["balance"]} for name, user in data["users"].items()]
    return sorted(players, key=lambda x: x["balance"], reverse=True)[:20]

@app.get("/api/top/level")
async def top_level():
    data = load_data()
    players = [{"name": name, "level": user.get("level", 0)} for name, user in data["users"].items()]
    return sorted(players, key=lambda x: x["level"], reverse=True)[:20]

# АДМИНКА
@app.post("/api/admin/login")
async def admin_login(auth: AuthRequest):
    if auth.password == "supersecret":  # ← СМЕНИТЕ!
        return {"token": "admin_token_123"}
    raise HTTPException(status_code=401, detail="Неверный пароль")

@app.get("/api/admin/players")
async def admin_players(token: str):
    if token != "admin_token_123":
        raise HTTPException(status_code=401, detail="Нет доступа")
    data = load_data()
    return [
        {
            "name": name,
            "balance": user["balance"],
            "level": user.get("level", 0),
            "total_win": user.get("total_win", 0)
        }
        for name, user in data["users"].items()
    ]

@app.post("/api/admin/give")
async def admin_give(token: str, action: AdminAction):
    if token != "admin_token_123":
        raise HTTPException(status_code=401, detail="Нет доступа")
    data = load_data()
    if action.target not in data["users"]:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    data["users"][action.target]["balance"] += action.amount
    save_data(data)
    return {"status": "ok"}

@app.post("/api/admin/take")
async def admin_take(token: str, action: AdminAction):
    if token != "admin_token_123":
        raise HTTPException(status_code=401, detail="Нет доступа")
    data = load_data()
    if action.target not in data["users"]:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    data["users"][action.target]["balance"] = max(0, data["users"][action.target]["balance"] - action.amount)
    save_data(data)
    return {"status": "ok"}

@app.get("/api/admin/stats")
async def admin_stats(token: str):
    if token != "admin_token_123":
        raise HTTPException(status_code=401, detail="Нет доступа")
    data = load_data()
    return {
        "total_players": len(data["users"]),
        "promo_usage": {k: len(v["used"]) for k, v in data["promo_codes"].items()},
        "total_promo_used": sum(len(v["used"]) for v in data["promo_codes"].values())
    }

# Health-check
@app.get("/health")
async def health():
    return {"status": "ok", "message": "Crash bot is running"}
