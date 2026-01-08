from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os

app = Fast API()  # ← ОШИБКА! Должно быть FastAPI(), но это опечатка — исправьте!

# Исправьте на:
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://crash-finerx.netlify.app", "https://web.telegram.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuthRequest(BaseModel):
    name: str
    password: str

DATA_FILE = "crash_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"users": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

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
        raise HTTPException(400, "Ошибка")
    response.set_cookie("session", auth.name, httponly=True, max_age=86400)
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
    del user["pass"]
    return user

@app.get("/health")
def health():
    return {"status": "ok"}
