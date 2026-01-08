from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import random
import asyncio
import time

app = FastAPI()

# CORS — только Netlify (для Telegram добавите позже)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://crash-finerx.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели
class AuthRequest(BaseModel):
    name: str
    password: str

class BetRequest(BaseModel):
    amount: float

class PromoRequest(BaseModel):
    code: str

class CaseRequest(BaseModel):
    caseId: str

class AdminAction(BaseModel):
    target: str
    amount: float

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
        "admin_password": "supersecret"  # ← СМЕНИТЕ!
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
    "started_at": None,  # ← КЛЮЧЕВОЕ: изначально None
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
                    current_round["started_at"] = time.time()  # ← УСТАНАВЛИВАЕТСЯ ТОЛЬКО ЗДЕСЬ
                    current_round["multiplier"] = 1.0

            elif current_round["status"] == "flight":
                if current_round["started_at"] is None:
                    current_round["started_at"] = time.time()  # ← Защита от бага
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
                        "started_at": None,  # ← СБРОС
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
        "crashX": current_round.get("crash_at"),
        "xHistory": data.get("x_history", []),
    }

@app.post("/api/round/bet")
def place_bet(request: Request, bet: BetRequest):
    session = request.cookies.get("session")
    if not session or session not in load_data()["users"]:
        raise HTTPException(401, "Не авторизован")
    if current_round["status"] != "bet":
        raise HTTPException(400, "Ставки не принимаются")
    data = load_data()
    user = data["users"][session]
    if bet.amount > user["balance"] or bet.amount < 10:
        raise HTTPException(400, "Неверная сумма")
    user["balance"] -= bet.amount
    current_round["bets"].append({"name": session, "amount": bet.amount, "cashed": False})
    save_data(data)
    return {"status": "ok"}

@app.post("/api/round/cashout")  # ← POST, а не GET!
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
        secure=True,        # ← обязательно для HTTPS
        samesite="none",    # ← разрешает куки между доменами
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

@app.post("/api/case")
def open_case(request: Request, case: CaseRequest):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(401, "Не авторизован")
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
        raise HTTPException(400, "Нельзя открыть")
    user.setdefault("cases", []).append(case.caseId)
    user["balance"] += reward
    save_data(data)
    return {"reward": reward}

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

@app.get("/api/top/level")
def top_level():
    data = load_data()
    return sorted(
        [{"name": n, "level": u.get("level", 0)} for n, u in data["users"].items()],
        key=lambda x: x["level"],
        reverse=True
    )[:20]

# АДМИНКА
@app.post("/api/admin/login")
def admin_login(auth: AuthRequest):
    if auth.password == "supersecret":
        return {"token": "admin_token_123"}
    raise HTTPException(401, "Неверный пароль")

@app.get("/api/admin/players")
def admin_players(token: str):
    if token != "admin_token_123":
        raise HTTPException(401, "Нет доступа")
    data = load_data()
    return [
        {"name": n, "balance": u["balance"], "level": u.get("level", 0), "total_win": u.get("total_win", 0)}
        for n, u in data["users"].items()
    ]

@app.post("/api/admin/give")
def admin_give(token: str, action: AdminAction):
    if token != "admin_token_123":
        raise HTTPException(401, "Нет доступа")
    data = load_data()
    if action.target not in data["users"]:
        raise HTTPException(404, "Игрок не найден")
    data["users"][action.target]["balance"] += action.amount
    save_data(data)
    return {"status": "ok"}

@app.post("/api/admin/take")
def admin_take(token: str, action: AdminAction):
    if token != "admin_token_123":
        raise HTTPException(401, "Нет доступа")
    data = load_data()
    if action.target not in data["users"]:
        raise HTTPException(404, "Игрок не найден")
    data["users"][action.target]["balance"] = max(0, data["users"][action.target]["balance"] - action.amount)
    save_data(data)
    return {"status": "ok"}

@app.get("/api/admin/stats")
def admin_stats(token: str):
    if token != "admin_token_123":
        raise HTTPException(401, "Нет доступа")
    data = load_data()
    return {
        "total_players": len(data["users"]),
        "promo_usage": {k: len(v["used"]) for k, v in data["promo_codes"].items()}
    }

# Health-check
@app.get("/health")
def health():
    return {"status": "ok", "message": "Crash bot is running"}
