# ============================================================
#  Chess Abilities — 계정 관리 (auth.py)
#  로컬 players.json 기반 로그인/회원가입
#  나중에 서버 연동 시 이 파일만 교체하면 됨
# ============================================================

import json
import os
import hashlib
import time

PLAYERS_FILE = "players.json"

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_db() -> dict:
    if os.path.exists(PLAYERS_FILE):
        try:
            with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_db(db: dict):
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def register(nickname: str, password: str) -> tuple[bool, str]:
    """회원가입. (성공여부, 메시지) 반환"""
    nickname = nickname.strip()
    if len(nickname) < 2:
        return False, "닉네임은 2자 이상이어야 해요."
    if len(nickname) > 16:
        return False, "닉네임은 16자 이하여야 해요."
    if len(password) < 4:
        return False, "비밀번호는 4자 이상이어야 해요."

    db = load_db()
    key = nickname.lower()
    if key in db:
        return False, "이미 사용 중인 닉네임이에요."

    db[key] = {
        "nickname": nickname,
        "password": _hash_pw(password),
        "rating":   1200,
        "wins":     0,
        "losses":   0,
        "draws":    0,
        "created":  time.time(),
    }
    save_db(db)
    return True, "회원가입 완료!"

def login(nickname: str, password: str) -> tuple[bool, str, dict]:
    """로그인. (성공여부, 메시지, 유저데이터) 반환"""
    nickname = nickname.strip()
    db = load_db()
    key = nickname.lower()
    if key not in db:
        return False, "닉네임을 찾을 수 없어요.", {}
    user = db[key]
    if user["password"] != _hash_pw(password):
        return False, "비밀번호가 틀렸어요.", {}
    return True, "로그인 성공!", user

def update_rating(nickname: str, result: str):
    """result: 'win' | 'loss' | 'draw'"""
    db = load_db()
    key = nickname.lower()
    if key not in db:
        return
    user = db[key]
    if result == "win":
        user["wins"]   += 1
        user["rating"] += 20
    elif result == "loss":
        user["losses"] += 1
        user["rating"]  = max(800, user["rating"] - 20)
    elif result == "draw":
        user["draws"]  += 1
        user["rating"] += 5
    db[key] = user
    save_db(db)

def get_leaderboard(top=10) -> list:
    db = load_db()
    users = [v for v in db.values()]
    users.sort(key=lambda u: u["rating"], reverse=True)
    return users[:top]
