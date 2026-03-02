# ============================================================
#  Chess Abilities — 시작 화면 (start_screen.py)
#  main.py 와 같은 폴더에 두세요
# ============================================================

import pygame
import sys
import math
from localization import locale
import auth

# ──────────────────────────────────────────────
# 색상 & 상수
# ──────────────────────────────────────────────

C_BG          = (8,   8,  12)
C_BG2         = (14,  14, 20)
C_GOLD        = (201, 168,  76)
C_GOLD_DIM    = (140, 110,  45)
C_GOLD_BRIGHT = (255, 215, 100)
C_WHITE       = (230, 224, 210)
C_MUTED       = ( 90,  85,  72)
C_PANEL       = ( 18,  18,  24)
C_PANEL_BORDER= ( 50,  45,  30)
C_RED         = (180,  50,  50)
C_GREEN       = ( 50, 160,  80)

def get_ability_info():
    return [
        ("♔ King",   locale.t("ability_royal"),    "Q",  locale.t("desc_royal"),    C_GOLD),
        ("♕ Queen",  locale.t("ability_aura"),     "W",  locale.t("desc_aura"),     (180, 130, 220)),
        ("♖ Rook",   locale.t("ability_fortress"), "E",  locale.t("desc_fortress"), (100, 160, 220)),
        ("♘ Knight", locale.t("ability_leap"),     "F",  locale.t("desc_leap"),     (100, 200, 140)),
        ("♗ Bishop", locale.t("ability_shadows"),  "S",  locale.t("desc_shadows"),  (160, 100, 220)),
        ("♙ Pawn",   locale.t("ability_advance"),  "D",  locale.t("desc_advance"),  (200, 160,  80)),
    ]


class StartScreen:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        self.screen = screen
        self.clock  = clock
        self.W, self.H = screen.get_size()
        self.t = 0  # 애니메이션 타이머
        self.fullscreen = False

        # 현재 페이지
        self.page = "auth"  # 시작은 항상 로그인 화면
        self.auth_mode = "login"  # "login" | "register"
        self.logged_in_user = None  # 로그인된 유저 데이터
        self._auth_inputs = {"nick": "", "pw": "", "pw2": ""}
        self._auth_field = "nick"
        self._auth_msg = ""
        self._auth_msg_ok = False

        # 설정값
        self.volume     = 70
        self.fullscreen = False

        self._load_fonts()
        self._build_buttons()
        self._build_particles()
        try:
            pygame.scrap.init()
        except:
            pass

    # ── 폰트 ──
    def _get_korean_font(self, size, bold=False):
        """한국어 지원 폰트 반환"""
        korean_fonts = ["malgun gothic", "gulim", "dotum", "batang", "nanum gothic"]
        for name in korean_fonts:
            try:
                f = pygame.font.SysFont(name, size, bold=bold)
                test = f.render("가", True, (0, 0, 0))
                if test.get_width() > 3:
                    return f
            except:
                pass
        return pygame.font.SysFont("segoeui", size, bold=bold)

    def _load_fonts(self):
        self.font_title   = self._get_korean_font(72, bold=True)
        self.font_sub     = self._get_korean_font(20)
        self.font_btn     = self._get_korean_font(18, bold=True)
        self.font_piece   = pygame.font.SysFont("segoeuisymbol", 36)
        self.font_ability = self._get_korean_font(14, bold=True)
        self.font_desc    = self._get_korean_font(13)
        self.font_key     = self._get_korean_font(13, bold=True)
        self.font_label   = self._get_korean_font(15)
        self.font_setting = self._get_korean_font(17)

    # ── 버튼 ──
    def _build_buttons(self):
        cx = self.W // 2
        self.buttons = {
            "play":      pygame.Rect(cx - 120, 300, 240, 48),
            "online":    pygame.Rect(cx - 120, 358, 240, 48),
            "abilities": pygame.Rect(cx - 120, 416, 240, 48),
            "settings":  pygame.Rect(cx - 120, 474, 240, 48),
            "quit":      pygame.Rect(cx - 120, 532, 240, 48),
            "back":      pygame.Rect(40, 40, 100, 38),
        }
        # 설정 슬라이더
        self.vol_rect   = pygame.Rect(cx - 150, 320, 300, 8)
        self.vol_handle = pygame.Rect(0, 0, 16, 24)
        self._update_vol_handle()

        self.hovered = None

    def _update_vol_handle(self):
        cx = self.W // 2
        x = int((cx - 150) + (self.volume / 100) * 300)
        self.vol_handle = pygame.Rect(x - 8, 312, 16, 24)

    # ── 파티클 배경 ──
    def _build_particles(self):
        import random
        random.seed(42)
        self.particles = []
        for _ in range(60):
            self.particles.append({
                "x": random.uniform(0, self.W),
                "y": random.uniform(0, self.H),
                "speed": random.uniform(0.1, 0.4),
                "size":  random.uniform(1, 2.5),
                "alpha": random.uniform(40, 120),
                "phase": random.uniform(0, math.pi * 2),
            })

    # ── 그리기 유틸 ──
    def _draw_text_centered(self, surf, text, font, color, y):
        s = font.render(text, True, color)
        surf.blit(s, (self.W // 2 - s.get_width() // 2, y))

    def _draw_text(self, surf, text, font, color, x, y):
        s = font.render(text, True, color)
        surf.blit(s, (x, y))

    def _lerp_color(self, c1, c2, t):
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

    # ── 배경 ──
    def _draw_background(self):
        self.screen.fill(C_BG)

        # 중앙 방사형 그라디언트 효과
        glow = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        pulse = 0.5 + 0.5 * math.sin(self.t * 0.02)
        radius = int(280 + pulse * 30)
        for r in range(radius, 0, -8):
            alpha = int(18 * (r / radius) * pulse)
            color = (*C_GOLD_DIM, alpha)
            pygame.draw.circle(glow, color, (self.W // 2, self.H // 2 - 60), r)
        self.screen.blit(glow, (0, 0))

        # 파티클 (떠다니는 금빛 점)
        for p in self.particles:
            p["y"] -= p["speed"]
            if p["y"] < -5:
                p["y"] = self.H + 5
            flicker = 0.5 + 0.5 * math.sin(self.t * 0.03 + p["phase"])
            alpha = int(p["alpha"] * flicker)
            s = pygame.Surface((int(p["size"]*2), int(p["size"]*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_GOLD, alpha), (int(p["size"]), int(p["size"])), int(p["size"]))
            self.screen.blit(s, (int(p["x"]), int(p["y"])))

        # 장식 가로선
        for y_off, alpha in [(180, 60), (620, 40)]:
            line_surf = pygame.Surface((self.W, 1), pygame.SRCALPHA)
            for x in range(self.W):
                a = int(alpha * math.sin(math.pi * x / self.W))
                pygame.draw.line(line_surf, (*C_GOLD, a), (x, 0), (x, 0))
            self.screen.blit(line_surf, (0, y_off))

    # ── 체스판 장식 타일 ──
    def _draw_chess_deco(self):
        tile = 28
        cols = self.W // tile + 1
        rows = 4
        surf = pygame.Surface((self.W, rows * tile), pygame.SRCALPHA)
        for r in range(rows):
            for c in range(cols):
                is_light = (r + c) % 2 == 0
                alpha = 18 if is_light else 8
                pygame.draw.rect(surf, (*C_GOLD, alpha),
                                 (c * tile, r * tile, tile, tile))
        self.screen.blit(surf, (0, self.H - rows * tile))

    # ── 버튼 그리기 ──
    def _draw_button(self, rect, label, hovered=False, danger=False):
        pulse = 0.5 + 0.5 * math.sin(self.t * 0.05)

        if danger:
            base_color = (60, 20, 20)
            border_color = C_RED
            text_color = (220, 100, 100)
        elif hovered:
            base_color = (35, 28, 12)
            border_color = C_GOLD_BRIGHT
            text_color = C_GOLD_BRIGHT
        else:
            base_color = (20, 18, 10)
            border_color = C_GOLD_DIM
            text_color = C_GOLD

        # 배경
        pygame.draw.rect(self.screen, base_color, rect, border_radius=4)

        # 테두리
        border_alpha = int(180 + 75 * pulse) if hovered else 120
        border_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(border_surf, (*border_color, border_alpha),
                         (0, 0, rect.width, rect.height), 2, border_radius=4)
        self.screen.blit(border_surf, rect.topleft)

        # 호버 시 내부 글로우
        if hovered:
            glow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*C_GOLD, 15),
                             (0, 0, rect.width, rect.height), border_radius=4)
            self.screen.blit(glow_surf, rect.topleft)

        # 텍스트
        txt = self.font_btn.render(label, True, text_color)
        self.screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                               rect.centery - txt.get_height() // 2))

    # ══════════════════════════════════════════
    # 메인 페이지
    # ══════════════════════════════════════════
    def _draw_main(self):
        self._draw_background()
        self._draw_chess_deco()

        # 왕관 장식
        crown_y = 90
        crown = self.font_piece.render("♚  ♔", True, C_GOLD_DIM)
        self.screen.blit(crown, (self.W // 2 - crown.get_width() // 2, crown_y))

        # 타이틀
        pulse = 0.5 + 0.5 * math.sin(self.t * 0.025)
        title_color = self._lerp_color(C_GOLD, C_GOLD_BRIGHT, pulse * 0.6)
        title = self.font_title.render(locale.t("title"), True, title_color)
        self.screen.blit(title, (self.W // 2 - title.get_width() // 2, 140))

        # 서브타이틀
        sub = self.font_sub.render(locale.t("subtitle"), True, C_MUTED)
        self.screen.blit(sub, (self.W // 2 - sub.get_width() // 2, 228))

        # 구분선
        for dx in range(-200, 201):
            a = int(80 * math.sin(math.pi * (dx + 200) / 400))
            pygame.draw.line(self.screen, (*C_GOLD, a),
                             (self.W // 2 + dx, 268),
                             (self.W // 2 + dx, 269))

        # 버튼
        mx, my = pygame.mouse.get_pos()
        for key, label, danger in [
            ("play",      locale.t("btn_play"),        False),
            ("online",    "🌐  ONLINE",                False),
            ("abilities", locale.t("btn_abilities"),   False),
            ("settings",  locale.t("btn_settings"),    False),
            ("quit",      locale.t("btn_quit"),         True),
        ]:
            rect = self.buttons[key]
            hovered = rect.collidepoint(mx, my)
            self._draw_button(rect, label, hovered, danger)

        # 버전
        ver = self.font_desc.render("v0.1 Alpha", True, C_MUTED)
        self.screen.blit(ver, (self.W - ver.get_width() - 16, self.H - 24))

    # ══════════════════════════════════════════
    # 능력 설명 페이지
    # ══════════════════════════════════════════
    def _draw_abilities(self):
        self.screen.fill(C_BG)
        self._draw_chess_deco()

        # 타이틀
        self._draw_text_centered(self.screen, "Abilities", self.font_title, C_GOLD, 40)
        self._draw_text_centered(self.screen,
            "Each piece has a unique power. Press the key to activate.",
            self.font_sub, C_MUTED, 120)

        # 능력 카드 (2열 3행)
        card_w, card_h = 340, 130
        gap_x, gap_y   = 30, 20
        start_x = self.W // 2 - (card_w * 2 + gap_x) // 2 + 30
        start_y = 165

        mx, my = pygame.mouse.get_pos()

        for i, (piece, name, key, desc, color) in enumerate(get_ability_info()):
            col = i % 2
            row = i // 2
            x = start_x + col * (card_w + gap_x) - 30
            y = start_y + row * (card_h + gap_y)
            rect = pygame.Rect(x, y, card_w, card_h)
            hovered = rect.collidepoint(mx, my)

            # 카드 배경
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            bg_alpha = 180 if hovered else 140
            pygame.draw.rect(card_surf, (*C_PANEL, bg_alpha),
                             (0, 0, card_w, card_h), border_radius=6)
            border_alpha = 200 if hovered else 100
            pygame.draw.rect(card_surf, (*color, border_alpha),
                             (0, 0, card_w, card_h), 1, border_radius=6)
            # 왼쪽 색상 바
            pygame.draw.rect(card_surf, (*color, 180),
                             (0, 0, 4, card_h), border_radius=3)
            self.screen.blit(card_surf, (x, y))

            # 기물 기호
            piece_surf = self.font_piece.render(piece.split()[0], True, color)
            self.screen.blit(piece_surf, (x + 14, y + card_h // 2 - piece_surf.get_height() // 2))

            # 능력 이름
            name_surf = self.font_ability.render(name, True, color)
            self.screen.blit(name_surf, (x + 58, y + 18))

            # 기물 이름
            piece_name = self.font_desc.render(piece, True, C_MUTED)
            self.screen.blit(piece_name, (x + 58, y + 38))

            # 설명
            for j, line in enumerate(desc.split("\n")):
                d_surf = self.font_desc.render(line, True, C_GOLD)
                self.screen.blit(d_surf, (x + 58, y + 60 + j * 18))

            # 키 배지
            key_bg = pygame.Surface((30, 24), pygame.SRCALPHA)
            pygame.draw.rect(key_bg, (*color, 60), (0, 0, 30, 24), border_radius=4)
            pygame.draw.rect(key_bg, (*color, 180), (0, 0, 30, 24), 1, border_radius=4)
            self.screen.blit(key_bg, (x + card_w - 44, y + 14))
            k_surf = self.font_key.render(key, True, color)
            self.screen.blit(k_surf, (x + card_w - 44 + 15 - k_surf.get_width() // 2,
                                      y + 14 + 12 - k_surf.get_height() // 2))

        # 뒤로 버튼
        back_rect = self.buttons["back"]
        hovered_back = back_rect.collidepoint(mx, my)
        self._draw_button(back_rect, "← Back", hovered_back)

    # ══════════════════════════════════════════
    # 설정 페이지
    # ══════════════════════════════════════════


    def _draw_online(self):
        """온라인 멀티플레이어 페이지"""
        self.screen.fill(C_BG)
        self._draw_chess_deco()

        title = "온라인 대전" if locale.lang == "ko" else "Online Multiplayer"
        self._draw_text_centered(self.screen, title, self.font_title, C_GOLD, 50)

        cx = self.W // 2
        mx, my = pygame.mouse.get_pos()
        y = 150

        # ── 서버 URL ──
        url_label = "서버 주소 (WSS URL)" if locale.lang == "ko" else "Server URL (WSS)"
        self._draw_text(self.screen, url_label + ":", self.font_label, C_GOLD, cx - 220, y)
        y += 26
        url_rect = pygame.Rect(cx - 220, y, 440, 36)
        active_u = self._input_field == "url"
        pygame.draw.rect(self.screen, (30, 25, 10) if active_u else (18, 16, 8), url_rect, border_radius=4)
        pygame.draw.rect(self.screen, C_GOLD if active_u else C_GOLD_DIM, url_rect, 2, border_radius=4)
        url_val = self._input_texts.get("url", "")
        ut = url_val + ("|" if active_u and self.t % 60 < 30 else "")
        us = self.font_desc.render(ut or "wss://...", True, C_GOLD if url_val else C_MUTED)
        self.screen.blit(us, (url_rect.x + 10, url_rect.y + 10))
        self._url_rect = url_rect
        y += 56

        pygame.draw.line(self.screen, C_PANEL_BORDER, (cx - 220, y), (cx + 220, y))
        y += 20

        # ── 방 코드 입력 (참가용) ──
        code_label = "방 코드 (참가시 입력)" if locale.lang == "ko" else "Room Code (to join)"
        self._draw_text(self.screen, code_label + ":", self.font_label, C_GOLD, cx - 220, y)
        y += 26
        code_rect = pygame.Rect(cx - 220, y, 200, 36)
        active_c = self._input_field == "code"
        pygame.draw.rect(self.screen, (30, 25, 10) if active_c else (18, 16, 8), code_rect, border_radius=4)
        pygame.draw.rect(self.screen, C_GOLD if active_c else C_GOLD_DIM, code_rect, 2, border_radius=4)
        ct = self._input_texts.get("code", "").upper() + ("|" if active_c and self.t % 60 < 30 else "")
        cs = self.font_btn.render(ct or "XXXXXX", True, C_GOLD if self._input_texts.get("code") else C_MUTED)
        self.screen.blit(cs, (code_rect.x + 10, code_rect.y + 8))
        self._code_rect = code_rect
        y += 56

        # ── 버튼 ──
        host_btn = pygame.Rect(cx - 220, y, 200, 46)
        join_btn = pygame.Rect(cx + 20,  y, 200, 46)
        self._host_btn = host_btn
        self._join_btn = join_btn

        for btn, label, color in [
            (host_btn, "🏠 " + ("방 만들기" if locale.lang=="ko" else "Create Room"), (100, 200, 140)),
            (join_btn, "🚪 " + ("방 참가"   if locale.lang=="ko" else "Join Room"),   (100, 160, 220)),
        ]:
            hov = btn.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (20, 35, 20) if hov else (12, 20, 12), btn, border_radius=4)
            pygame.draw.rect(self.screen, color, btn, 2, border_radius=4)
            bs = self.font_btn.render(label, True, color)
            self.screen.blit(bs, (btn.centerx - bs.get_width()//2, btn.centery - bs.get_height()//2))

        # ── 상태 메시지 ──
        if hasattr(self, '_online_msg') and self._online_msg:
            msg_color = (220, 80, 80) if "오류" in self._online_msg or "Error" in self._online_msg else (100, 220, 100)
            ms = self.font_label.render(self._online_msg, True, msg_color)
            self.screen.blit(ms, (cx - ms.get_width()//2, y + 60))


        # 뒤로 버튼
        back_rect = self.buttons["back"]
        self._draw_button(back_rect, locale.t("btn_back"), back_rect.collidepoint(mx, my))


    def _draw_auth(self):
        """로그인 / 회원가입 페이지"""
        import math
        self.screen.fill(C_BG)
        self._draw_chess_deco()

        cx = self.W // 2
        mx, my = pygame.mouse.get_pos()

        # 타이틀
        self._draw_text_centered(self.screen, "Chess Abilities", self.font_title, C_GOLD, 55)

        # 탭 버튼
        tab_w, tab_h = 160, 38
        login_tab  = pygame.Rect(cx - tab_w - 4, 130, tab_w, tab_h)
        reg_tab    = pygame.Rect(cx + 4,          130, tab_w, tab_h)
        self._login_tab = login_tab
        self._reg_tab   = reg_tab

        for tab, label, mode in [(login_tab, "로그인" if locale.lang=="ko" else "Login", "login"),
                                  (reg_tab,  "회원가입" if locale.lang=="ko" else "Register", "register")]:
            active = self.auth_mode == mode
            pygame.draw.rect(self.screen, C_GOLD if active else C_BG2, tab, border_radius=5)
            col = (10,8,4) if active else C_MUTED
            ts = self.font_btn.render(label, True, col)
            self.screen.blit(ts, (tab.centerx - ts.get_width()//2, tab.centery - ts.get_height()//2))

        y = 188

        # 입력 필드
        fields = [
            ("nick", "닉네임" if locale.lang=="ko" else "Nickname"),
            ("pw",   "비밀번호" if locale.lang=="ko" else "Password"),
        ]
        if self.auth_mode == "register":
            fields.append(("pw2", "비밀번호 확인" if locale.lang=="ko" else "Confirm Password"))

        self._auth_rects = {}
        for field, label in fields:
            ls = self.font_label.render(label, True, C_MUTED)
            self.screen.blit(ls, (cx - 180, y))
            y += 22

            rect = pygame.Rect(cx - 180, y, 360, 38)
            self._auth_rects[field] = rect
            active = self._auth_field == field
            pygame.draw.rect(self.screen, (30,25,10) if active else (18,16,8), rect, border_radius=5)
            pygame.draw.rect(self.screen, C_GOLD if active else C_GOLD_DIM, rect, 2, border_radius=5)

            # 비밀번호 마스킹
            val = self._auth_inputs[field]
            display = ("*" * len(val)) if field in ("pw","pw2") else val
            cursor = "|" if active and self.t % 60 < 30 else ""
            ts = self.font_btn.render(display + cursor, True, C_GOLD)
            self.screen.blit(ts, (rect.x + 12, rect.y + 9))
            y += 50

        # 메시지
        if self._auth_msg:
            col = (100,220,100) if self._auth_msg_ok else (220,80,80)
            ms = self.font_label.render(self._auth_msg, True, col)
            self.screen.blit(ms, (cx - ms.get_width()//2, y))
        y += 30

        # 확인 버튼
        btn = pygame.Rect(cx - 120, y, 240, 44)
        self._auth_btn = btn
        hov = btn.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (40,30,10) if hov else (25,20,8), btn, border_radius=5)
        pygame.draw.rect(self.screen, C_GOLD, btn, 2, border_radius=5)
        label = ("로그인" if self.auth_mode=="login" else "회원가입") if locale.lang=="ko" else ("Login" if self.auth_mode=="login" else "Register")
        bs = self.font_btn.render(label, True, C_GOLD)
        self.screen.blit(bs, (btn.centerx - bs.get_width()//2, btn.centery - bs.get_height()//2))

    def _do_auth(self):
        """로그인/회원가입 처리"""
        nick = self._auth_inputs["nick"].strip()
        pw   = self._auth_inputs["pw"]
        pw2  = self._auth_inputs["pw2"]

        if self.auth_mode == "login":
            ok, msg, user = auth.login(nick, pw)
            self._auth_msg = msg
            self._auth_msg_ok = ok
            if ok:
                self.logged_in_user = user
                self.page = "main"
        else:
            if pw != pw2:
                self._auth_msg = "비밀번호가 일치하지 않아요." if locale.lang=="ko" else "Passwords don't match."
                self._auth_msg_ok = False
                return
            ok, msg = auth.register(nick, pw)
            self._auth_msg = msg
            self._auth_msg_ok = ok
            if ok:
                _, _, user = auth.login(nick, pw)
                self.logged_in_user = user
                self.page = "main"

    def _draw_mode_buttons(self, options, start_y):
        """공통 버튼 그리기 헬퍼"""
        import math
        cx = self.W // 2
        mx, my = pygame.mouse.get_pos()
        btn_w, btn_h = 360, 68
        btns = {}
        for i, (key, label, desc, color) in enumerate(options):
            bx = cx - btn_w // 2
            by = start_y + i * (btn_h + 12)
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            btns[key] = rect
            hov = rect.collidepoint(mx, my)
            pulse = 0.5 + 0.5 * math.sin(self.t * 0.05 + i)
            bg = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            bg_alpha = 210 if hov else 140
            pygame.draw.rect(bg, (*C_BG2, bg_alpha), (0, 0, btn_w, btn_h), border_radius=6)
            border_alpha = int(200 + 55 * pulse) if hov else 100
            pygame.draw.rect(bg, (*color, border_alpha), (0, 0, btn_w, btn_h), 2, border_radius=6)
            pygame.draw.rect(bg, (*color, 200), (0, 0, 4, btn_h), border_radius=3)
            self.screen.blit(bg, (bx, by))
            lbl = self.font_btn.render(label, True, color)
            self.screen.blit(lbl, (bx + 20, by + 12))
            dsc = self.font_desc.render(desc, True, C_MUTED)
            self.screen.blit(dsc, (bx + 20, by + 38))
        return btns

    def _draw_mode(self):
        """게임 모드 선택 페이지"""
        self.screen.fill(C_BG)
        self._draw_chess_deco()

        mode_step = getattr(self, '_mode_step', 'mode')

        if mode_step == 'mode':
            self._draw_text_centered(self.screen, locale.t("select_mode"), self.font_title, C_GOLD, 55)
            self._draw_text_centered(self.screen, locale.t("select_mode_sub"), self.font_sub, C_MUTED, 128)
            options = [
                ("2p",     locale.t("mode_2p"),     locale.t("mode_2p_desc"),     C_GOLD),
                ("easy",   locale.t("mode_easy"),   locale.t("mode_easy_desc"),   (100, 200, 140)),
                ("medium", locale.t("mode_medium"), locale.t("mode_medium_desc"), (100, 160, 220)),
                ("hard",   locale.t("mode_hard"),   locale.t("mode_hard_desc"),   (220, 100, 100)),
            ]
            self._mode_btns = self._draw_mode_buttons(options, 175)

        else:  # time 선택
            title = "시간 선택" if locale.lang == "ko" else "Select Time"
            sub   = "제한 시간을 선택하세요" if locale.lang == "ko" else "Choose time control per player"
            self._draw_text_centered(self.screen, title, self.font_title, C_GOLD, 55)
            self._draw_text_centered(self.screen, sub, self.font_sub, C_MUTED, 128)
            options = [
                ("0",   ("무제한" if locale.lang=="ko" else "No Limit"),  ("시간 제한 없음" if locale.lang=="ko" else "Play without time limit"), C_GOLD),
                ("600", ("10분"   if locale.lang=="ko" else "10 Minutes"), ("각 10분" if locale.lang=="ko" else "10 min per player"),             (100, 200, 140)),
                ("180", ("3분"    if locale.lang=="ko" else "3 Minutes"),  ("각 3분"  if locale.lang=="ko" else "3 min per player"),              (100, 160, 220)),
                ("60",  ("1분"    if locale.lang=="ko" else "1 Minute"),   ("각 1분"  if locale.lang=="ko" else "1 min per player"),              (220, 100, 100)),
            ]
            self._mode_btns = self._draw_mode_buttons(options, 175)

        back_rect = self.buttons["back"]
        mx, my = pygame.mouse.get_pos()
        self._draw_button(back_rect, locale.t("btn_back"), back_rect.collidepoint(mx, my))

    def _draw_settings(self):
        self.screen.fill(C_BG)
        self._draw_chess_deco()

        self._draw_text_centered(self.screen, "Settings", self.font_title, C_GOLD, 60)

        cx = self.W // 2
        mx, my = pygame.mouse.get_pos()

        # ── 음량 슬라이더 ──
        vol_label = self.font_setting.render(f"Volume:  {self.volume}%", True, C_GOLD)
        self.screen.blit(vol_label, (cx - 150, 280))

        # 슬라이더 트랙
        pygame.draw.rect(self.screen, C_PANEL_BORDER, self.vol_rect, border_radius=4)
        filled = pygame.Rect(self.vol_rect.x, self.vol_rect.y,
                             int(self.volume / 100 * 300), 8)
        pygame.draw.rect(self.screen, C_GOLD_DIM, filled, border_radius=4)

        # 슬라이더 핸들
        handle_hover = self.vol_handle.collidepoint(mx, my)
        handle_color = C_GOLD_BRIGHT if handle_hover else C_GOLD
        pygame.draw.rect(self.screen, handle_color, self.vol_handle, border_radius=3)

        # ── 구분선 ──
        pygame.draw.line(self.screen, C_PANEL_BORDER,
                         (cx - 150, 370), (cx + 150, 370))

        # ── 언어 선택 ──
        lang_y = 450
        for lang, label in [("en", "English"), ("ko", "한국어")]:
            lang_rect = pygame.Rect(cx - 150 + (0 if lang == "en" else 160), lang_y, 140, 36)
            selected = locale.lang == lang
            hov = lang_rect.collidepoint(mx, my)
            bg_col = (50, 40, 15) if selected else ((35, 28, 12) if hov else (20, 18, 10))
            border_col = C_GOLD_BRIGHT if selected else (C_GOLD if hov else C_GOLD_DIM)
            pygame.draw.rect(self.screen, bg_col, lang_rect, border_radius=4)
            pygame.draw.rect(self.screen, border_col, lang_rect, 2, border_radius=4)
            lbl = self.font_setting.render(label, True, C_GOLD if selected else C_MUTED)
            self.screen.blit(lbl, (lang_rect.centerx - lbl.get_width() // 2,
                                   lang_rect.centery - lbl.get_height() // 2))
            if not hasattr(self, '_lang_rects'):
                self._lang_rects = {}
            self._lang_rects[lang] = lang_rect

        lang_label = self.font_setting.render(locale.t("language") + ":", True, C_WHITE)
        self.screen.blit(lang_label, (cx - 150, lang_y - 28))

        # ── 전체화면 토글 ──
        fs_rect = pygame.Rect(cx - 150, 390, 300, 36)
        fs_hov = fs_rect.collidepoint(mx, my)
        fs_label = "Fullscreen:  ON  [F11]" if self.fullscreen else "Fullscreen:  OFF  [F11]"
        pygame.draw.rect(self.screen, (35, 28, 12) if fs_hov else (20, 18, 10), fs_rect, border_radius=4)
        pygame.draw.rect(self.screen, C_GOLD if fs_hov else C_GOLD_DIM, fs_rect, 1, border_radius=4)
        fs_surf = self.font_setting.render(fs_label, True, C_GOLD if self.fullscreen else C_MUTED)
        self.screen.blit(fs_surf, (cx - 140, 400))
        self.fs_rect = fs_rect



        # 뒤로 버튼
        back_rect = self.buttons["back"]
        hovered_back = back_rect.collidepoint(mx, my)
        self._draw_button(back_rect, "← Back", hovered_back)

    # ══════════════════════════════════════════
    # 이벤트 처리
    # ══════════════════════════════════════════
    def _handle_event(self, event) -> str:
        """'play' 반환 시 게임 시작, 'quit' 시 종료, '' 계속"""
        mx, my = pygame.mouse.get_pos()

        if event.type == pygame.QUIT:
            return "quit"

        # 인증 페이지 입력
        if self.page == "auth":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                # 탭 전환
                if hasattr(self, '_login_tab') and self._login_tab.collidepoint(mx, my):
                    self.auth_mode = "login"
                    self._auth_msg = ""
                elif hasattr(self, '_reg_tab') and self._reg_tab.collidepoint(mx, my):
                    self.auth_mode = "register"
                    self._auth_msg = ""
                # 입력 필드 포커스
                elif hasattr(self, '_auth_rects'):
                    clicked = False
                    for field, rect in self._auth_rects.items():
                        if rect.collidepoint(mx, my):
                            self._auth_field = field
                            clicked = True
                    if not clicked and hasattr(self, '_auth_btn') and self._auth_btn.collidepoint(mx, my):
                        self._do_auth()

            if event.type == pygame.KEYDOWN:
                field = self._auth_field
                if event.key == pygame.K_TAB:
                    order = ["nick", "pw", "pw2"] if self.auth_mode == "register" else ["nick", "pw"]
                    idx = order.index(field) if field in order else 0
                    self._auth_field = order[(idx + 1) % len(order)]
                elif event.key == pygame.K_RETURN:
                    # 마지막 필드거나 로그인 모드면 바로 처리
                    self._do_auth()
                elif event.key == pygame.K_BACKSPACE:
                    self._auth_inputs[field] = self._auth_inputs[field][:-1]
                elif event.unicode and len(self._auth_inputs.get(field,"")) < 40:
                    self._auth_inputs[field] = self._auth_inputs.get(field,"") + event.unicode

        # 온라인 페이지 텍스트 입력
        if self.page == "online":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                self._online_msg = ""
                if hasattr(self, '_url_rect') and self._url_rect.collidepoint(mx, my):
                    self._input_field = "url"
                elif hasattr(self, '_code_rect') and self._code_rect.collidepoint(mx, my):
                    self._input_field = "code"
                elif hasattr(self, '_host_btn') and self._host_btn.collidepoint(mx, my):
                    url = self._input_texts.get("url", "").strip()
                    if not url:
                        self._online_msg = "서버 주소를 입력하세요!" if locale.lang=="ko" else "Enter server URL!"
                    else:
                        self.server_host = url
                        self.online_action = "host"
                        return "online"
                elif hasattr(self, '_join_btn') and self._join_btn.collidepoint(mx, my):
                    url  = self._input_texts.get("url", "").strip()
                    code = self._input_texts.get("code", "").strip()
                    if not url:
                        self._online_msg = "서버 주소를 입력하세요!" if locale.lang=="ko" else "Enter server URL!"
                    elif not code:
                        self._online_msg = "방 코드를 입력하세요!" if locale.lang=="ko" else "Enter room code!"
                    else:
                        self.server_host = url
                        self.room_code   = code.upper()
                        self.online_action = "join"
                        return "online"
                else:
                    self._input_field = None

            if event.type == pygame.KEYDOWN and self._input_field:
                field = self._input_field
                ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL
                if ctrl and event.key == pygame.K_v:
                    # 클립보드 붙여넣기
                    try:
                        clip = pygame.scrap.get(pygame.SCRAP_TEXT)
                        if clip:
                            text = clip.decode("utf-8", errors="ignore").replace("\x00","").strip()
                            self._input_texts[field] = self._input_texts.get(field, "") + text
                    except:
                        pass
                elif ctrl and event.key == pygame.K_a:
                    # 전체 선택 (내용 유지, 커서만 표시)
                    pass
                elif ctrl and event.key == pygame.K_c:
                    try:
                        pygame.scrap.put(pygame.SCRAP_TEXT, self._input_texts.get(field, "").encode("utf-8"))
                    except:
                        pass
                elif event.key == pygame.K_BACKSPACE:
                    if ctrl:
                        self._input_texts[field] = ""
                    else:
                        self._input_texts[field] = self._input_texts.get(field, "")[:-1]
                elif event.key == pygame.K_TAB:
                    order = ["url", "code"]
                    idx = order.index(field) if field in order else 0
                    self._input_field = order[(idx + 1) % len(order)]
                elif event.key == pygame.K_RETURN:
                    self._input_field = None
                elif event.unicode and not ctrl and len(self._input_texts.get(field, "")) < 200:
                    self._input_texts[field] = self._input_texts.get(field, "") + event.unicode

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.page != "main":
                    self.page = "main"
                else:
                    return "quit"
            if event.key == pygame.K_RETURN and self.page == "main":
                self.page = "mode"
            if event.key == pygame.K_F11:
                self.fullscreen = not self.fullscreen
                if self.fullscreen:
                    self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.page == "main":
                if self.buttons["play"].collidepoint(mx, my):
                    self.page = "mode"
                if self.buttons["online"].collidepoint(mx, my):
                    self.page = "online"
                if self.buttons["abilities"].collidepoint(mx, my):
                    self.page = "abilities"
                if self.buttons["settings"].collidepoint(mx, my):
                    self.page = "settings"
                if self.buttons["quit"].collidepoint(mx, my):
                    return "quit"
            elif self.page == "mode":
                for key, val in getattr(self, '_mode_btns', {}).items():
                    if val.collidepoint(mx, my):
                        step = getattr(self, '_mode_step', 'mode')
                        if step == 'mode':
                            # 모드 선택 완료 → 시간 선택으로
                            if key == '2p':
                                self.game_mode = '2p'
                            else:
                                self.game_mode = 'ai'
                                self.ai_difficulty = key
                            self._mode_step = 'time'
                        else:
                            # 시간 선택 완료 → 게임 시작
                            self.time_limit = int(key)
                            self._mode_step = 'mode'
                            return "play"
                if self.buttons["back"].collidepoint(mx, my):
                    step = getattr(self, '_mode_step', 'mode')
                    if step == 'time':
                        self._mode_step = 'mode'
                    else:
                        self.page = "main"
                        self._mode_step = 'mode' 
            else:
                if self.buttons["back"].collidepoint(mx, my):
                    self.page = "main"

        # 볼륨 슬라이더 드래그
        if self.page == "settings":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for lang, rect in getattr(self, '_lang_rects', {}).items():
                    if rect.collidepoint(mx, my):
                        locale.set_lang(lang)
                if hasattr(self, 'fs_rect') and self.fs_rect.collidepoint(mx, my):
                    self.fullscreen = not self.fullscreen
                    if self.fullscreen:
                        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
                if self.vol_rect.collidepoint(mx, my) or self.vol_handle.collidepoint(mx, my):
                    self._dragging_vol = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._dragging_vol = False
            if event.type == pygame.MOUSEMOTION and getattr(self, '_dragging_vol', False):
                rel_x = mx - self.vol_rect.x
                self.volume = max(0, min(100, int(rel_x / self.vol_rect.width * 100)))
                self._update_vol_handle()

        return ""

    # ══════════════════════════════════════════
    # 메인 루프
    # ══════════════════════════════════════════
    def run(self) -> dict:
        """시작 화면 실행. {'action': 'play'|'quit', 'volume': int, 'mode': str, 'difficulty': str} 반환"""
        self.game_mode = "2p"        # 기본값
        self.ai_difficulty = "medium"
        self.time_limit = 0            # 0=무제한, 180=3분, 600=10분, 60=1분
        self.online_action = None      # 'host' | 'join'
        self.nickname = ""             # 닉네임
        self.room_code = ""            # 방 코드
        self.server_host = ""          # 서버 주소
        self.server_port = ""          # 서버 포트
        self._input_field = None       # 현재 입력 중인 필드
        self._input_texts = {"nick": "", "code": "", "url": "wss://chess-abilities-production.up.railway.app"}
        self._dragging_vol = False

        while True:
            for event in pygame.event.get():
                result = self._handle_event(event)
                if result == "online":
                    return {"action": "online", "volume": self.volume,
                            "online_action": self.online_action,
                            "nickname": self.nickname,
                            "server_host": self.server_host,
                            "server_port": self.server_port,
                            "room_code": self.room_code,
                            "time_limit": self.time_limit}
                if result == "play":
                    return {"action": "play", "volume": self.volume, "mode": self.game_mode, "difficulty": self.ai_difficulty, "time_limit": self.time_limit}
                if result == "quit":
                    pygame.quit()
                    sys.exit()

            self.t += 1

            if self.page == "auth":
                self._draw_auth()
            elif self.page == "main":
                self._draw_main()
            elif self.page == "online":
                self._draw_online()
            elif self.page == "mode":
                self._draw_mode()
            elif self.page == "abilities":
                self._draw_abilities()
            elif self.page == "settings":
                self._draw_settings()

            pygame.display.flip()
            self.clock.tick(60)
