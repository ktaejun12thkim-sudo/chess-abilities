# ============================================================
#  Chess Abilities — WebSocket 서버 (server.py)
#  Replit 배포용
# ============================================================

import asyncio
import websockets
import json
import random
import string
import hashlib
import os
import time

PORT = int(os.environ.get("PORT", 8765))

# ── Elo 레이팅 계산 ──
def calc_elo(winner, loser, k=32):
    exp = 1 / (1 + 10 ** ((loser - winner) / 400))
    return int(winner + k * (1 - exp)), int(loser + k * (0 - (1 - exp)))

# ── 방 코드 생성 ──
def make_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ── 플레이어 DB (players.json) ──
DB_FILE = "players.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ── 전역 상태 ──
rooms = {}    # code → Room
clients = {}  # ws → ClientState

class ClientState:
    def __init__(self, ws):
        self.ws       = ws
        self.nickname = None
        self.room     = None
        self.color    = None  # "white" | "black"

class Room:
    def __init__(self, code, host: ClientState, time_limit):
        self.code       = code
        self.time_limit = time_limit
        self.players    = [host]
        self.started    = False

    def is_full(self):
        return len(self.players) >= 2

    def other(self, ws):
        for p in self.players:
            if p.ws != ws:
                return p
        return None

    async def broadcast(self, msg, exclude=None):
        data = json.dumps(msg)
        for p in self.players:
            if p.ws != exclude:
                try:
                    await p.ws.send(data)
                except:
                    pass

    async def send_to_color(self, color, msg):
        for p in self.players:
            if p.color == color:
                try:
                    await p.ws.send(json.dumps(msg))
                except:
                    pass

# ── 메시지 송신 ──
async def send(ws, msg):
    try:
        await ws.send(json.dumps(msg))
    except:
        pass

# ── 레이팅 업데이트 ──
async def update_ratings(room, winner_color, reason):
    if len(room.players) < 2:
        return
    db = load_db()
    p0 = room.players[0]  # white
    p1 = room.players[1]  # black

    k0 = p0.nickname.lower() if p0.nickname else None
    k1 = p1.nickname.lower() if p1.nickname else None

    if not k0 or not k1 or k0 not in db or k1 not in db:
        return

    d0, d1 = db[k0], db[k1]

    if winner_color == "white":
        d0["rating"], d1["rating"] = calc_elo(d0["rating"], d1["rating"])
        d0["wins"] += 1; d1["losses"] += 1
    elif winner_color == "black":
        d1["rating"], d0["rating"] = calc_elo(d1["rating"], d0["rating"])
        d1["wins"] += 1; d0["losses"] += 1
    else:
        avg = (d0["rating"] + d1["rating"]) // 2
        d0["rating"] = d1["rating"] = avg
        d0["draws"] += 1; d1["draws"] += 1

    db[k0], db[k1] = d0, d1
    save_db(db)

    await room.send_to_color("white", {
        "type": "rating_update",
        "rating": d0["rating"], "wins": d0["wins"],
        "losses": d0["losses"], "draws": d0["draws"]
    })
    await room.send_to_color("black", {
        "type": "rating_update",
        "rating": d1["rating"], "wins": d1["wins"],
        "losses": d1["losses"], "draws": d1["draws"]
    })

# ── 클라이언트 핸들러 ──
async def handler(ws):
    state = ClientState(ws)
    clients[ws] = state
    print(f"[연결] {ws.remote_address}")

    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except:
                continue

            t = msg.get("type")

            # ── 회원가입 ──
            if t == "register":
                nick = msg.get("nickname", "").strip()[:16]
                pw   = msg.get("password", "")
                if not nick or len(pw) < 4:
                    await send(ws, {"type": "register_fail", "msg": "닉네임/비밀번호를 확인하세요."})
                    continue
                db = load_db()
                key = nick.lower()
                if key in db:
                    await send(ws, {"type": "register_fail", "msg": "이미 사용 중인 닉네임이에요."})
                    continue
                db[key] = {
                    "nickname": nick, "password": hash_pw(pw),
                    "rating": 1200, "wins": 0, "losses": 0, "draws": 0,
                    "created": time.time()
                }
                save_db(db)
                await send(ws, {"type": "register_ok", "nickname": nick})

            # ── 로그인 ──
            elif t == "login":
                nick = msg.get("nickname", "").strip()
                pw   = msg.get("password", "")
                db   = load_db()
                key  = nick.lower()
                if key not in db:
                    await send(ws, {"type": "login_fail", "msg": "닉네임을 찾을 수 없어요."})
                    continue
                user = db[key]
                if user["password"] != hash_pw(pw):
                    await send(ws, {"type": "login_fail", "msg": "비밀번호가 틀렸어요."})
                    continue
                state.nickname = user["nickname"]
                await send(ws, {
                    "type": "login_ok",
                    "nickname": user["nickname"],
                    "rating":   user["rating"],
                    "wins":     user["wins"],
                    "losses":   user["losses"],
                    "draws":    user["draws"],
                })

            # ── 방 만들기 ──
            elif t == "create_room":
                code = make_code()
                tl   = msg.get("time_limit", 0)
                room = Room(code, state, tl)
                state.color = "white"
                state.room  = room
                rooms[code] = room
                await send(ws, {"type": "room_created", "code": code, "color": "white"})
                print(f"[방 생성] {code} by {state.nickname}")

            # ── 방 참가 ──
            elif t == "join_room":
                code = msg.get("code", "").upper()
                room = rooms.get(code)
                if not room:
                    await send(ws, {"type": "error", "msg": "방을 찾을 수 없어요."})
                elif room.is_full():
                    await send(ws, {"type": "error", "msg": "방이 가득 찼어요."})
                else:
                    room.players.append(state)
                    state.color = "black"
                    state.room  = room
                    await send(ws, {
                        "type": "room_joined", "code": code, "color": "black",
                        "opponent": room.players[0].nickname,
                        "time_limit": room.time_limit,
                    })
                    await room.broadcast({
                        "type": "opponent_joined",
                        "opponent": state.nickname,
                        "time_limit": room.time_limit,
                    }, exclude=ws)
                    print(f"[방 참가] {state.nickname} → {code}")

            # ── 이동 ──
            elif t == "move":
                if state.room:
                    await state.room.broadcast({
                        "type": "move",
                        "from": msg["from"],
                        "to":   msg["to"],
                        "promotion": msg.get("promotion"),
                    }, exclude=ws)

            # ── 게임 오버 ──
            elif t == "game_over":
                if state.room:
                    await state.room.broadcast(msg, exclude=ws)
                    await update_ratings(state.room, msg.get("winner"), msg.get("reason"))

            # ── 무승부 제안 ──
            elif t == "draw_offer":
                if state.room:
                    await state.room.broadcast({
                        "type": "draw_offer", "from": state.color
                    }, exclude=ws)

            # ── 능력 ──
            elif t == "ability":
                if state.room:
                    await state.room.broadcast(msg, exclude=ws)

            # ── 채팅 ──
            elif t == "chat":
                if state.room:
                    await state.room.broadcast({
                        "type": "chat",
                        "nick": state.nickname or "?",
                        "msg":  msg.get("msg", "")[:100],
                    }, exclude=ws)

            # ── 리더보드 ──
            elif t == "leaderboard":
                db = load_db()
                users = sorted(db.values(), key=lambda u: u["rating"], reverse=True)[:10]
                board = [{"nickname": u["nickname"], "rating": u["rating"],
                          "wins": u["wins"], "losses": u["losses"]} for u in users]
                await send(ws, {"type": "leaderboard", "data": board})

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"[오류] {e}")
    finally:
        print(f"[연결 해제] {state.nickname}")
        if state.room:
            await state.room.broadcast({"type": "opponent_disconnected"}, exclude=ws)
            state.room.players = [p for p in state.room.players if p.ws != ws]
            if not state.room.players:
                rooms.pop(state.room.code, None)
        clients.pop(ws, None)

# ── 메인 ──
async def main():
    print(f"[서버 시작] port {PORT}")
    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
