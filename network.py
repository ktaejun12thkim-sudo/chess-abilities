# ============================================================
#  Chess Abilities — WebSocket 클라이언트 (network.py)
# ============================================================

import threading
import json
import queue

try:
    import websocket  # websocket-client 라이브러리
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

class NetworkClient:
    def __init__(self):
        self.ws         = None
        self.connected  = False
        self.recv_queue = queue.Queue()
        self.my_color   = None
        self.my_nick    = None
        self.my_rating  = 1200

    def connect(self, url: str, timeout: float = 8.0) -> bool:
        """wss://... 또는 ws://... URL로 연결"""
        if not WS_AVAILABLE:
            print("[오류] websocket-client 미설치: pip install websocket-client")
            return False
        try:
            self.ws = websocket.WebSocketApp(
                url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open,
            )
            import ssl
            sslopt = {"cert_reqs": ssl.CERT_NONE} if url.startswith("wss://") else {}
            t = threading.Thread(target=self.ws.run_forever, kwargs={"sslopt": sslopt}, daemon=True)
            t.start()
            import time
            for _ in range(int(timeout * 10)):
                if self.connected:
                    return True
                time.sleep(0.1)
            return False
        except Exception as e:
            print(f"[연결 실패] {e}")
            return False

    def _on_open(self, ws):
        self.connected = True
        print("[연결됨]")

    def _on_message(self, ws, raw):
        try:
            self.recv_queue.put(json.loads(raw))
        except:
            pass

    def _on_error(self, ws, error):
        print(f"[WS 오류] {error}")

    def _on_close(self, ws, code, msg):
        self.connected = False
        self.recv_queue.put({"type": "disconnected"})
        print("[연결 해제]")

    def disconnect(self):
        self.connected = False
        if self.ws:
            try: self.ws.close()
            except: pass

    def send(self, msg: dict):
        if not self.connected or not self.ws:
            return
        try:
            self.ws.send(json.dumps(msg))
        except Exception as e:
            print(f"[송신 오류] {e}")
            self.connected = False

    def poll(self) -> list:
        msgs = []
        while not self.recv_queue.empty():
            msgs.append(self.recv_queue.get_nowait())
        return msgs

    # ── 편의 메서드 ──
    def login(self, nickname: str, password: str = ""):
        self.my_nick = nickname
        self.send({"type": "login", "nickname": nickname, "password": password})

    def register(self, nickname: str, password: str):
        self.send({"type": "register", "nickname": nickname, "password": password})

    def create_room(self, time_limit: int = 0):
        self.send({"type": "create_room", "time_limit": time_limit})

    def join_room(self, code: str):
        self.send({"type": "join_room", "code": code.upper()})

    def send_move(self, from_pos, to_pos, promotion=None):
        self.send({
            "type": "move",
            "from": [from_pos.row, from_pos.col],
            "to":   [to_pos.row,   to_pos.col],
            "promotion": promotion,
        })

    def send_game_over(self, winner_color, reason):
        self.send({"type": "game_over", "winner": winner_color, "reason": reason})

    def offer_draw(self):
        self.send({"type": "draw_offer"})

    def send_chat(self, msg: str):
        self.send({"type": "chat", "msg": msg})

    def send_ability(self, ability: str, data: dict = None):
        """능력 사용 전송"""
        msg = {"type": "ability", "ability": ability}
        if data:
            msg.update(data)
        self.send(msg)

    def get_leaderboard(self):
        self.send({"type": "leaderboard"})
