# ============================================================
#  Chess Abilities — pygame 렌더러 (main.py)
#  chess_engine.py 와 같은 폴더에 두고 실행하세요
#  실행: py main.py
# ============================================================

import pygame
import sys
from ability_system import AbilitySystem
from start_screen import StartScreen
from sound_manager import SoundManager
from ai_engine import ChessAI
from localization import locale
from network import NetworkClient
from chess_engine import (
    Game, Board, Color, PieceType, Position,
    MoveGenerator, parse_pos
)

# ──────────────────────────────────────────────
# 1. 설정값
# ──────────────────────────────────────────────

SQUARE_SIZE   = 80          # 칸 크기 (픽셀)
BOARD_SIZE    = SQUARE_SIZE * 8   # 640
PANEL_WIDTH   = 280         # 우측 정보 패널 너비
BOARD_OFFSET_X = 50         # 보드 X 여백
BOARD_OFFSET_Y = 100        # 보드 Y 여백
WINDOW_W      = BOARD_OFFSET_X + BOARD_SIZE + 20 + PANEL_WIDTH
WINDOW_H      = BOARD_OFFSET_Y + BOARD_SIZE + 100
ABILITY_BAR_Y = BOARD_OFFSET_Y + BOARD_SIZE + 10  # 능력 바 Y 위치
PANEL_X       = BOARD_OFFSET_X + BOARD_SIZE + 20                # 패널 X 시작
FPS           = 60

# 색상
C_LIGHT       = (120, 100,  45)   # 밝은 칸 (미디엄 골드)
C_DARK        = ( 45,  40,  25)   # 어두운 칸 (어두운 회색)
C_HIGHLIGHT   = (120, 100,  20)   # 선택된 기물 칸 (금빛)
C_MOVE        = (201, 168,  76)   # 이동 가능 칸 (금색 점)
C_CAPTURE     = (220,  60,  60)   # 잡을 수 있는 칸
C_CHECK       = (180,  30,  30)   # 체크 상태 킹
C_PANEL_BG    = (  8,   8,  12)   # 패널 배경 (시작화면과 동일)
C_PANEL_LINE  = ( 50,  45,  30)   # 패널 구분선 (금빛)
C_GOLD        = (201, 168,  76)   # 강조 텍스트
C_GOLD_DIM    = (140, 110,  45)   # 어두운 골드
C_WHITE_TEXT  = (201, 168,  76)
C_MUTED       = (100,  85,  45)
C_LAST_MOVE   = ( 80,  68,  20)   # 마지막 이동 하이라이트

# 기물 유니코드 기호
SYMBOLS = {
    (PieceType.KING,   Color.WHITE): "♔",
    (PieceType.QUEEN,  Color.WHITE): "♕",
    (PieceType.ROOK,   Color.WHITE): "♖",
    (PieceType.BISHOP, Color.WHITE): "♗",
    (PieceType.KNIGHT, Color.WHITE): "♘",
    (PieceType.PAWN,   Color.WHITE): "♙",
    (PieceType.KING,   Color.BLACK): "♚",
    (PieceType.QUEEN,  Color.BLACK): "♛",
    (PieceType.ROOK,   Color.BLACK): "♜",
    (PieceType.BISHOP, Color.BLACK): "♝",
    (PieceType.KNIGHT, Color.BLACK): "♞",
    (PieceType.PAWN,   Color.BLACK): "♟",
}


# ──────────────────────────────────────────────
# 2. 렌더러 클래스
# ──────────────────────────────────────────────

class ChessRenderer:
    def __init__(self, screen=None, clock=None, ai=None):
        if screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
            pygame.display.set_caption(locale.t("panel_title"))
            self.clock = pygame.time.Clock()
        else:
            self.screen = screen
            self.clock = clock

        # 폰트 로드 (유니코드 기물 기호를 위해 시스템 폰트 사용)
        self.piece_font  = self._load_piece_font(62)
        self.font_btn    = self._get_korean_font(17, bold=True)
        self.label_font  = self._get_korean_font(14)
        self.info_font   = self._get_korean_font(16)
        self.title_font  = self._get_korean_font(18, bold=True)
        self.status_font = self._get_korean_font(15)

        # 기물 이미지 로드
        self.piece_images = self._load_piece_images()

        self.game = Game()
        self.abilities = AbilitySystem(self.game)
        self.game.ability_system = self.abilities

        # UI 상태
        self.selected: Position | None = None      # 현재 선택된 칸
        self.legal_moves: list[Position] = []      # 선택된 기물의 이동 가능 칸
        self.last_from: Position | None = None     # 마지막 이동 출발
        self.last_to:   Position | None = None     # 마지막 이동 도착
        self.message: str = ""                     # 상태 메시지
        self.captured_white: list = []             # 백이 잡은 흑 기물
        self.captured_black: list = []             # 흑이 잡은 백 기물
        self.ability_mode: str = ""               # 현재 능력 모드
        self._go_to_menu: bool = False             # 메인 메뉴로 돌아가기 플래그
        self._fullscreen: bool = False             # 전체화면 모드
        self._render_surf = pygame.Surface((WINDOW_W, WINDOW_H))  # 오프스크린 렌더링
        self.sounds = SoundManager(volume=70)
        self.ai: ChessAI | None = ai       # AI 인스턴스 (None이면 2P)
        self.net: NetworkClient | None = None  # 온라인 클라이언트
        self.my_color: str = "white"           # 온라인에서 내 색
        self.opponent_nick: str = ""           # 상대 닉네임
        self.my_nick: str = ""                 # 내 닉네임
        self.my_rating: int = 1200             # 내 레이팅
        self.online_room_code: str = ""        # 방 코드
        self.waiting_opponent: bool = False    # 상대 대기 중
        self.chat_msgs: list = []              # 채팅 메시지
        self.chat_input: str = ""              # 채팅 입력
        self.chat_active: bool = False         # 채팅 입력 활성
        self.draw_offer_pending: bool = False      # 무승부 제안 대기 중
        self.draw_offer_by = None                  # 제안한 쪽
        self.decree_piece_pos = None               # 칙령 대상 기물 위치
        self.hidden_bishop_revealed = {}
        self._go_to_menu = False
        self.draw_offer_pending = False
        self.draw_offer_by = None
        # 타이머
        self.time_limit = 0
        self.white_time = 0
        self.black_time = 0
        self.last_tick = pygame.time.get_ticks()
        # AI 는 reset 시 유지           # {color: last_known_pos} 은신 해제 전 마지막 위치

    def _load_piece_images(self) -> dict:
        """pieces/ 폴더에서 기물 이미지 로드. 없으면 빈 dict 반환"""
        import os
        images = {}
        piece_map = {
            (PieceType.KING,   Color.WHITE): "wK",
            (PieceType.QUEEN,  Color.WHITE): "wQ",
            (PieceType.ROOK,   Color.WHITE): "wR",
            (PieceType.BISHOP, Color.WHITE): "wB",
            (PieceType.KNIGHT, Color.WHITE): "wN",
            (PieceType.PAWN,   Color.WHITE): "wP",
            (PieceType.KING,   Color.BLACK): "bK",
            (PieceType.QUEEN,  Color.BLACK): "bQ",
            (PieceType.ROOK,   Color.BLACK): "bR",
            (PieceType.BISHOP, Color.BLACK): "bB",
            (PieceType.KNIGHT, Color.BLACK): "bN",
            (PieceType.PAWN,   Color.BLACK): "bP",
        }
        pieces_dir = os.path.join(os.path.dirname(__file__), "pieces")
        if not os.path.isdir(pieces_dir):
            print("[경고] pieces/ 폴더를 찾을 수 없습니다. 유니코드 기호로 표시됩니다.")
            return {}
        for key, name in piece_map.items():
            # png, svg 순으로 시도
            for ext in [".png", ".PNG", ".svg"]:
                path = os.path.join(pieces_dir, name + ext)
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        img = pygame.transform.smoothscale(img, (SQUARE_SIZE - 8, SQUARE_SIZE - 8))
                        images[key] = img
                        break
                    except Exception as e:
                        print(f"[경고] {path} 로드 실패: {e}")
        if images:
            print(f"[정보] 기물 이미지 {len(images)}개 로드 완료")
        return images

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

    def _load_piece_font(self, size: int):
        """유니코드 체스 기호를 지원하는 폰트 로드"""
        for name in ["segoeuisymbol", "seguisym", "symbola", "unifont", "dejavusans"]:
            try:
                f = pygame.font.SysFont(name, size)
                # 실제로 기호가 렌더링되는지 테스트
                surf = f.render("♔", True, (0, 0, 0))
                if surf.get_width() > 5:
                    return f
            except:
                pass
        return pygame.font.SysFont(None, size)

    # ── 좌표 변환 ──

    @property
    def _flipped(self) -> bool:
        """흑 플레이어는 보드를 뒤집어서 봄"""
        return self.net is not None and self.my_color == "black"

    def pos_to_pixel(self, pos: Position) -> tuple[int, int]:
        """Position → 화면 픽셀 좌표 (칸의 좌상단)"""
        if self._flipped:
            col = 7 - pos.col
            row = 7 - pos.row
        else:
            col = pos.col
            row = pos.row
        x = BOARD_OFFSET_X + col * SQUARE_SIZE
        y = BOARD_OFFSET_Y + row * SQUARE_SIZE
        return x, y

    def pixel_to_pos(self, px: int, py: int) -> Position | None:
        """마우스 픽셀 좌표 → Position"""
        bx = px - BOARD_OFFSET_X
        by = py - BOARD_OFFSET_Y
        if bx < 0 or bx >= BOARD_SIZE or by < 0 or by >= BOARD_SIZE:
            return None
        col = bx // SQUARE_SIZE
        row = by // SQUARE_SIZE
        if self._flipped:
            col = 7 - col
            row = 7 - row
        return Position(row, col)

    # ── 그리기 메서드 ──

    def draw_board_border(self):
        """보드 테두리 금빛 글로우"""
        import math
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.001)
        alpha = int(80 + 40 * pulse)
        border_surf = pygame.Surface((BOARD_SIZE + 4, BOARD_SIZE + 4), pygame.SRCALPHA)
        pygame.draw.rect(border_surf, (201, 168, 76, alpha),
                         (0, 0, BOARD_SIZE + 4, BOARD_SIZE + 4), 2)
        self.screen.blit(border_surf, (BOARD_OFFSET_X - 2, BOARD_OFFSET_Y - 2))

    def draw_mines(self):
        """지뢰 위치 표시"""
        if not hasattr(self.abilities, 'mines'):
            return
        import math
        for mine in self.abilities.mines:
            pos = mine["pos"]
            x, y = self.pos_to_pixel(pos)
            cx = x + SQUARE_SIZE // 2
            cy = y + SQUARE_SIZE // 2
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.005)
            r = int(8 + 3 * pulse)
            surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(surf, (220, 60, 60, int(180 * pulse)), (SQUARE_SIZE//2, SQUARE_SIZE//2), r)
            pygame.draw.circle(surf, (255, 100, 100, 200), (SQUARE_SIZE//2, SQUARE_SIZE//2), r, 2)
            self.screen.blit(surf, (x, y))
            mine_font = pygame.font.SysFont("segoeuisymbol", 16)
            ms = mine_font.render("💣", True, (255, 100, 100))
            self.screen.blit(ms, (x + SQUARE_SIZE//2 - ms.get_width()//2, y + SQUARE_SIZE//2 - ms.get_height()//2))

    def draw_board(self):
        """체스판 배경 그리기"""
        # 전체 배경
        self.screen.fill((8, 8, 12))
        for row in range(8):
            for col in range(8):
                pos = Position(row, col)
                is_light = (row + col) % 2 == 0

                # 기본 색상 결정
                if pos == self.selected:
                    color = C_HIGHLIGHT
                elif pos in (self.last_from, self.last_to):
                    # 은신 중인 비숍의 이동은 상대방에게 하이라이트 숨김
                    from chess_engine import PieceType
                    piece_at_to = self.game.board.get(self.last_to) if self.last_to else None
                    is_hidden_move = (
                        piece_at_to and
                        piece_at_to.piece_type == PieceType.BISHOP and
                        piece_at_to.is_hidden and
                        piece_at_to.color != self.game.current_turn
                    )
                    if is_hidden_move:
                        color = C_LIGHT if is_light else C_DARK
                    else:
                        base = C_LIGHT if is_light else C_DARK
                        color = tuple(min(255, b + 30) for b in base)
                else:
                    color = C_LIGHT if is_light else C_DARK

                x, y = self.pos_to_pixel(pos)
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))
                # 칸 구분 테두리
                pygame.draw.rect(self.screen, (40, 34, 16),
                                 (x, y, SQUARE_SIZE, SQUARE_SIZE), 1)

    def draw_coordinates(self):
        """a~h, 1~8 좌표 레이블 — 보드 바깥쪽에 표시"""
        for i in range(8):
            # 파일 (a~h) — 보드 아래쪽 바깥
            letter = "abcdefgh"[i]
            surf = self.label_font.render(letter, True, C_GOLD)
            x = BOARD_OFFSET_X + i * SQUARE_SIZE + SQUARE_SIZE // 2 - surf.get_width() // 2
            y = BOARD_OFFSET_Y + BOARD_SIZE + 6
            self.screen.blit(surf, (x, y))

            # 랭크 (1~8) — 보드 왼쪽 바깥
            rank = str(8 - i)
            surf2 = self.label_font.render(rank, True, C_GOLD)
            x2 = BOARD_OFFSET_X - surf2.get_width() - 6
            y2 = BOARD_OFFSET_Y + i * SQUARE_SIZE + SQUARE_SIZE // 2 - surf2.get_height() // 2
            self.screen.blit(surf2, (x2, y2))

    def draw_move_hints(self):
        """이동 가능 칸 힌트 표시"""
        hint_list = self.legal_moves if self.legal_moves else []
        # 칙령 목적지 선택 중이면 decree_targets 표시
        if self.ability_mode == "decree_select_dest":
            hint_list = self.abilities.royal_decree_targets
        elif self.ability_mode == "aura_select":
            hint_list = self.abilities.aura_targets
        elif self.ability_mode == "leap_select":
            hint_list = self.abilities.leap_moves
        elif self.ability_mode == "advance_select":
            hint_list = self.abilities.advance_moves
        for pos in hint_list:
            x, y = self.pos_to_pixel(pos)
            cx = x + SQUARE_SIZE // 2
            cy = y + SQUARE_SIZE // 2

            target = self.game.board.get(pos)
            dot_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            if target:
                # 잡을 수 있는 기물 — 반투명 동그라미 테두리 (chess.com 스타일)
                pygame.draw.circle(dot_surf, (*C_CAPTURE, 140),
                                   (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE//2 - 3)
                pygame.draw.circle(dot_surf, (0, 0, 0, 0),
                                   (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE//2 - 10)
            else:
                # 빈 칸 — 중앙 반투명 점
                pygame.draw.circle(dot_surf, (*C_MOVE, 150),
                                   (SQUARE_SIZE//2, SQUARE_SIZE//2), 14)
            self.screen.blit(dot_surf, (x, y))

    def draw_check_highlight(self):
        """체크 상태일 때 킹 칸 빨간 테두리"""
        if self.game.board.is_in_check(self.game.current_turn):
            king_pos = self.game.board.find_king(self.game.current_turn)
            if king_pos:
                x, y = self.pos_to_pixel(king_pos)
                pygame.draw.rect(self.screen, C_CHECK,
                                 (x, y, SQUARE_SIZE, SQUARE_SIZE), 4)

    def draw_pieces(self):
        """기물 그리기 — 이미지 우선, 없으면 유니코드 기호로 폴백"""
        for row in range(8):
            for col in range(8):
                piece = self.game.board._grid[row][col]
                if piece is None:
                    continue

                pos = Position(row, col)
                x, y = self.pos_to_pixel(pos)
                offset_y = -6 if pos == self.selected else 0  # 선택 시 살짝 위로

                key = (piece.piece_type, piece.color)

                # 은신 중인 적 비숍은 표시 안 함 (상대방에게 위치 숨김)
                if piece.is_hidden and piece.color != self.game.current_turn:
                    continue

                if key in self.piece_images:
                    # ── 이미지 렌더링 ──
                    img = self.piece_images[key].copy()
                    # 은신 중인 아군 비숍은 반투명 + 보라빛으로 표시
                    if piece.is_hidden:
                        img.set_alpha(130)
                        tint = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                        tint.fill((100, 0, 200, 60))
                        img.blit(tint, (0, 0))
                    # 그림자
                    shadow_surf = pygame.Surface((SQUARE_SIZE - 8, SQUARE_SIZE - 8), pygame.SRCALPHA)
                    shadow_surf.fill((0, 0, 0, 0))
                    shadow_surf.blit(img, (0, 0))
                    shadow_surf.set_alpha(40)
                    self.screen.blit(shadow_surf, (x + 6, y + 8 + offset_y))
                    # 기물 이미지
                    self.screen.blit(img, (x + 4, y + 4 + offset_y))
                else:
                    # ── 유니코드 폴백 ──
                    symbol = SYMBOLS[key]
                    shadow = self.piece_font.render(symbol, True, (0, 0, 0))
                    self.screen.blit(shadow, (x + 9, y + 11 + offset_y))
                    piece_color = (255, 255, 255) if piece.color == Color.WHITE else (30, 30, 35)
                    outline_color = (50, 50, 50) if piece.color == Color.WHITE else (200, 200, 200)
                    for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        outline = self.piece_font.render(symbol, True, outline_color)
                        self.screen.blit(outline, (x + 8 + ox, y + 8 + oy + offset_y))
                    surf = self.piece_font.render(symbol, True, piece_color)
                    self.screen.blit(surf, (x + 8, y + 8 + offset_y))


    def draw_blockades(self):
        """봉쇄된 파일(열)을 반투명 파란 선으로 표시"""
        for b in self.abilities.blockades:
            col = b.get("col")
            if col is None:
                continue
            surf = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
            # 뒤집힌 보드 고려
            draw_col = (7 - col) if self._flipped else col
            pygame.draw.rect(surf, (80, 140, 255, 50),
                             (draw_col * SQUARE_SIZE, 0, SQUARE_SIZE, BOARD_SIZE))
            pygame.draw.line(surf, (80, 140, 255, 180),
                             (draw_col * SQUARE_SIZE, 0),
                             (draw_col * SQUARE_SIZE, BOARD_SIZE), 3)
            pygame.draw.line(surf, (80, 140, 255, 180),
                             ((draw_col + 1) * SQUARE_SIZE, 0),
                             ((draw_col + 1) * SQUARE_SIZE, BOARD_SIZE), 3)
            self.screen.blit(surf, (BOARD_OFFSET_X, BOARD_OFFSET_Y))


    def draw_paralyzed(self):
        """마비된 기물에 빨간 테두리 표시"""
        for r in range(8):
            for c in range(8):
                pos = Position(r, c)
                piece = self.game.board.get(pos)
                if piece and piece.is_paralyzed:
                    x, y = self.pos_to_pixel(pos)
                    surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    pygame.draw.rect(surf, (180, 40, 40, 80),
                                     (0, 0, SQUARE_SIZE, SQUARE_SIZE))
                    pygame.draw.rect(surf, (220, 60, 60, 200),
                                     (0, 0, SQUARE_SIZE, SQUARE_SIZE), 2)
                    self.screen.blit(surf, (x, y))


    def draw_promotion_popup(self):
        """승진 선택 팝업 — 보드 중앙에 표시"""
        import math
        from chess_engine import PieceType, Color

        # promotion_pending 위치의 기물 색으로 확인
        piece_at = self.game.board.get(self.game.promotion_pending)
        color = piece_at.color if piece_at else self.game.current_turn.opponent()
        choices = [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]

        # 팝업 크기
        popup_w, popup_h = 360, 160
        popup_x = BOARD_OFFSET_X + (BOARD_SIZE - popup_w) // 2
        popup_y = BOARD_OFFSET_Y + (BOARD_SIZE - popup_h) // 2

        # 배경 어둡게
        overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # 팝업 배경
        popup = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
        pygame.draw.rect(popup, (14, 14, 20, 240), (0, 0, popup_w, popup_h), border_radius=8)
        # 금빛 테두리
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.003)
        border_alpha = int(180 + 75 * pulse)
        pygame.draw.rect(popup, (201, 168, 76, border_alpha),
                         (0, 0, popup_w, popup_h), 2, border_radius=8)
        self.screen.blit(popup, (popup_x, popup_y))

        # 타이틀
        title = self.title_font.render(locale.t("promotion_title"), True, C_GOLD)
        self.screen.blit(title, (popup_x + popup_w // 2 - title.get_width() // 2,
                                  popup_y + 12))

        # 기물 선택 버튼 4개
        btn_size = 64
        gap = 12
        total_w = btn_size * 4 + gap * 3
        start_x = popup_x + (popup_w - total_w) // 2
        btn_y = popup_y + 70

        mx, my = pygame.mouse.get_pos()
        self.promo_rects = {}

        for i, pt in enumerate(choices):
            bx = start_x + i * (btn_size + gap)
            rect = pygame.Rect(bx, btn_y, btn_size, btn_size)
            self.promo_rects[pt] = rect
            hovered = rect.collidepoint(mx, my)

            # 버튼 배경
            btn_surf = pygame.Surface((btn_size, btn_size), pygame.SRCALPHA)
            bg_color = (50, 40, 15, 220) if hovered else (25, 22, 10, 200)
            pygame.draw.rect(btn_surf, bg_color, (0, 0, btn_size, btn_size), border_radius=6)
            border_col = (255, 215, 100, 220) if hovered else (140, 110, 45, 160)
            pygame.draw.rect(btn_surf, border_col, (0, 0, btn_size, btn_size), 2, border_radius=6)
            self.screen.blit(btn_surf, (bx, btn_y))

            key = (pt, color)
            if key in self.piece_images:
                img = pygame.transform.smoothscale(self.piece_images[key], (btn_size - 8, btn_size - 8))
                self.screen.blit(img, (bx + 4, btn_y + 4))
            else:
                sym = SYMBOLS[key]
                s = self.piece_font.render(sym, True,
                    (255, 255, 255) if color == Color.WHITE else (30, 30, 35))
                self.screen.blit(s, (bx + btn_size // 2 - s.get_width() // 2,
                                     btn_y + btn_size // 2 - s.get_height() // 2))



    def draw_resign_buttons(self, y: int, px: int, pad: int):
        """기권 / 무승부 제안 버튼"""
        import math
        mx, my = pygame.mouse.get_pos()

        # 기권 버튼
        resign_rect = pygame.Rect(px + pad, y, PANEL_WIDTH - pad * 2, 34)
        resign_hov = resign_rect.collidepoint(mx, my)
        bg = (50, 15, 15) if resign_hov else (28, 10, 10)
        pygame.draw.rect(self.screen, bg, resign_rect, border_radius=4)
        pygame.draw.rect(self.screen, (180, 50, 50, 200) if resign_hov else (120, 40, 40, 180),
                         resign_rect, 2, border_radius=4)
        r_txt = self.font_btn.render(locale.t("btn_resign"), True, (220, 80, 80) if resign_hov else (160, 60, 60))
        self.screen.blit(r_txt, (resign_rect.centerx - r_txt.get_width() // 2,
                                  resign_rect.centery - r_txt.get_height() // 2))
        self.resign_rect = resign_rect
        y += 42

        # 무승부 제안 버튼
        draw_rect = pygame.Rect(px + pad, y, PANEL_WIDTH - pad * 2, 34)
        draw_hov = draw_rect.collidepoint(mx, my)
        if self.draw_offer_pending:
            bg2 = (15, 40, 15)
            border = (60, 160, 60, 200)
            txt_color = (80, 200, 80)
            label = locale.t("btn_draw_offered")
        else:
            bg2 = (20, 28, 20) if draw_hov else (12, 18, 12)
            border = (60, 140, 60, 200) if draw_hov else (40, 100, 40, 160)
            txt_color = (80, 180, 80) if draw_hov else (50, 130, 50)
            label = locale.t("btn_offer_draw")
        pygame.draw.rect(self.screen, bg2, draw_rect, border_radius=4)
        pygame.draw.rect(self.screen, border, draw_rect, 2, border_radius=4)
        d_txt = self.font_btn.render(label, True, txt_color)
        self.screen.blit(d_txt, (draw_rect.centerx - d_txt.get_width() // 2,
                                  draw_rect.centery - d_txt.get_height() // 2))
        self.draw_offer_rect = draw_rect
        y += 42
        return y

    def draw_draw_offer_popup(self):
        """무승부 제안 수락/거절 팝업"""
        import math

        cx = BOARD_OFFSET_X + BOARD_SIZE // 2
        cy = BOARD_OFFSET_Y + BOARD_SIZE // 2
        box_w, box_h = 360, 160
        bx = cx - box_w // 2
        by = cy - box_h // 2

        overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box, (10, 10, 15, 245), (0, 0, box_w, box_h), border_radius=10)
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.002)
        pygame.draw.rect(box, (60, 160, 60, int(160 + 95 * pulse)),
                         (0, 0, box_w, box_h), 2, border_radius=10)
        self.screen.blit(box, (bx, by))

        offerer = "White" if self.draw_offer_by and self.draw_offer_by.value == "white" else "Black"
        title = self.title_font.render(locale.t("draw_offer_title"), True, (80, 200, 80))
        self.screen.blit(title, (cx - title.get_width() // 2, by + 16))

        sub = self.info_font.render(locale.t("draw_offer_white") if self.draw_offer_by and self.draw_offer_by.value == "white" else locale.t("draw_offer_black"), True, C_MUTED)
        self.screen.blit(sub, (cx - sub.get_width() // 2, by + 72))

        mx, my = pygame.mouse.get_pos()
        btn_y = by + 108

        # Accept
        acc_rect = pygame.Rect(cx - 160, btn_y, 130, 38)
        acc_hov = acc_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (15, 40, 15) if acc_hov else (10, 25, 10), acc_rect, border_radius=4)
        pygame.draw.rect(self.screen, (80, 200, 80) if acc_hov else (50, 140, 50), acc_rect, 2, border_radius=4)
        a_txt = self.font_btn.render(locale.t("btn_accept"), True, (80, 220, 80) if acc_hov else (60, 180, 60))
        self.screen.blit(a_txt, (acc_rect.centerx - a_txt.get_width() // 2,
                                  acc_rect.centery - a_txt.get_height() // 2))

        # Decline
        dec_rect = pygame.Rect(cx + 30, btn_y, 130, 38)
        dec_hov = dec_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (40, 15, 15) if dec_hov else (25, 10, 10), dec_rect, border_radius=4)
        pygame.draw.rect(self.screen, (200, 60, 60) if dec_hov else (140, 40, 40), dec_rect, 2, border_radius=4)
        d_txt = self.font_btn.render(locale.t("btn_decline"), True, (220, 80, 80) if dec_hov else (180, 60, 60))
        self.screen.blit(d_txt, (dec_rect.centerx - d_txt.get_width() // 2,
                                  dec_rect.centery - d_txt.get_height() // 2))

        self.draw_acc_rect = acc_rect
        self.draw_dec_rect = dec_rect

    def draw_game_over(self):
        """게임 오버 화면 — 보드 위 오버레이"""
        import math

        # 배경 어둡게
        overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (BOARD_OFFSET_X, BOARD_OFFSET_Y))

        cx = BOARD_OFFSET_X + BOARD_SIZE // 2
        cy = BOARD_OFFSET_Y + BOARD_SIZE // 2

        # 팝업 박스
        box_w, box_h = 420, 220
        bx = cx - box_w // 2
        by = cy - box_h // 2

        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box, (10, 10, 15, 245), (0, 0, box_w, box_h), border_radius=10)
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.002)
        border_alpha = int(180 + 75 * pulse)
        pygame.draw.rect(box, (201, 168, 76, border_alpha),
                         (0, 0, box_w, box_h), 2, border_radius=10)
        self.screen.blit(box, (bx, by))

        # 왕관 아이콘
        if self.game.winner:
            crown_sym = "♔" if self.game.winner == Color.WHITE else "♚"
            crown = self.piece_font.render(crown_sym, True, C_GOLD)
            self.screen.blit(crown, (cx - crown.get_width() // 2, by + 18))

        # 결과 텍스트
        draw_reason = getattr(self.game, 'draw_reason', None)
        if self.game.winner:
            winner_str = "White" if self.game.winner == Color.WHITE else "Black"
            result_text = f"{winner_str} Wins!"
            sub_text = locale.t("resigned") if draw_reason == "resign" else locale.t("checkmate")
        else:
            result_text = locale.t("draw")
            sub_text = locale.t("by_agreement") if draw_reason == "agreement" else locale.t("stalemate")

        result_surf = self.title_font.render(result_text, True, C_GOLD_BRIGHT if hasattr(self, 'C_GOLD_BRIGHT') else (255, 215, 100))
        self.screen.blit(result_surf, (cx - result_surf.get_width() // 2, by + 65))

        sub_surf = self.info_font.render(sub_text, True, C_MUTED)
        self.screen.blit(sub_surf, (cx - sub_surf.get_width() // 2, by + 115))

        # 구분선
        pygame.draw.line(self.screen, C_GOLD,
                         (bx + 40, by + 140), (bx + box_w - 40, by + 140), 1)

        # 버튼
        mx, my = pygame.mouse.get_pos()
        btn_y = by + 155

        # Play Again 버튼
        again_rect = pygame.Rect(cx - 170, btn_y, 150, 42)
        again_hov = again_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (35, 28, 12) if again_hov else (20, 18, 10),
                         again_rect, border_radius=4)
        pygame.draw.rect(self.screen, (255, 215, 100) if again_hov else C_GOLD,
                         again_rect, 2, border_radius=4)
        again_txt = self.font_btn.render(locale.t("btn_play_again"), True,
                                          (255, 215, 100) if again_hov else C_GOLD)
        self.screen.blit(again_txt, (again_rect.centerx - again_txt.get_width() // 2,
                                      again_rect.centery - again_txt.get_height() // 2))

        # Main Menu 버튼
        menu_rect = pygame.Rect(cx + 20, btn_y, 150, 42)
        menu_hov = menu_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (35, 28, 12) if menu_hov else (20, 18, 10),
                         menu_rect, border_radius=4)
        pygame.draw.rect(self.screen, (255, 215, 100) if menu_hov else C_GOLD,
                         menu_rect, 2, border_radius=4)
        menu_txt = self.font_btn.render(locale.t("btn_main_menu"), True,
                                         (255, 215, 100) if menu_hov else C_GOLD)
        self.screen.blit(menu_txt, (menu_rect.centerx - menu_txt.get_width() // 2,
                                     menu_rect.centery - menu_txt.get_height() // 2))

        self.gameover_again_rect = again_rect
        self.gameover_menu_rect  = menu_rect



    def _handle_net_ability(self, msg: dict):
        """상대방 능력 수신 처리"""
        from chess_engine import Position, PieceType
        ability = msg.get("ability")

        if ability == "iron_fortress":
            rook = msg.get("rook")
            if rook:
                self.abilities.activate_iron_fortress(Position(rook[0], rook[1]))
                self.sounds.play("ability")

        elif ability == "into_shadows":
            bishop = msg.get("bishop")
            if bishop:
                self.abilities.activate_into_shadows(Position(bishop[0], bishop[1]))
                self.sounds.play("ability")

        elif ability == "land_mine":
            pawn = msg.get("pawn")
            if pawn:
                self.abilities.activate_double_advance(Position(pawn[0], pawn[1]))
                self.sounds.play("ability")

        elif ability == "domination_aura":
            target = msg.get("target")
            if target:
                # 퀸 찾기
                for r in range(8):
                    for c in range(8):
                        p = self.game.board.get(Position(r, c))
                        if p and p.piece_type == PieceType.QUEEN and p.color == self.game.current_turn:
                            self.abilities.activate_domination_aura(Position(r, c))
                            self.abilities.execute_domination_aura(Position(target[0], target[1]))
                            self.sounds.play("ability")
                            break

        elif ability == "phantom_jump":
            fr = msg.get("from")
            to = msg.get("to")
            if fr and to:
                self.abilities.activate_shadow_leap(Position(fr[0], fr[1]))
                self.abilities.execute_shadow_leap(Position(to[0], to[1]))
                self.sounds.play("ability")

        self.message = f"⚡ {ability.replace('_', ' ').title()}"

    def _handle_net_msg(self, msg: dict):
        """네트워크 메시지 처리"""
        from chess_engine import Position, PieceType, Color
        t = msg.get("type")

        if t == "login_ok":
            self.my_rating = msg["rating"]
            self.my_nick   = msg["nickname"]

        elif t == "room_created":
            self.online_room_code = msg["code"]
            self.my_color = msg["color"]
            self.waiting_opponent = True

        elif t == "room_joined":
            self.my_color = msg["color"]
            self.opponent_nick = msg.get("opponent", "")
            self.waiting_opponent = False

        elif t == "opponent_joined":
            self.opponent_nick = msg.get("opponent", "")
            self.waiting_opponent = False
            self.message = f"{self.opponent_nick} 참가!"

        elif t == "move":
            fr = msg["from"]
            to = msg["to"]
            from_pos = Position(fr[0], fr[1])
            to_pos   = Position(to[0], to[1])
            result = self.game.move(from_pos, to_pos)
            if result["success"]:
                self.last_from = from_pos
                self.last_to   = to_pos
                if result["captured"]:
                    self.sounds.play("capture")
                else:
                    self.sounds.play("move")
                promo = msg.get("promotion")
                if result["info"] == "promotion_pending":
                    if promo:
                        pt_map = {"Q": PieceType.QUEEN, "R": PieceType.ROOK,
                                  "B": PieceType.BISHOP, "N": PieceType.KNIGHT}
                        self.game.promote(pt_map.get(promo, PieceType.QUEEN))
                    else:
                        self.game.promote(PieceType.QUEEN)
                if result["info"] == "checkmate":
                    self.sounds.play("checkmate")
                    self.message = locale.t("msg_checkmate")
                elif result["info"] == "check":
                    self.message = locale.t("msg_check")

        elif t == "ability":
            self._handle_net_ability(msg)

        elif t == "draw_offer":
            self.draw_offer_pending = True
            self.draw_offer_by = self.game.current_turn.opponent()

        elif t == "game_over":
            reason = msg.get("reason")
            winner = msg.get("winner")
            self.game.game_over = True
            self.game.winner = Color.WHITE if winner == "white" else (Color.BLACK if winner == "black" else None)
            self.game.draw_reason = reason or ""

        elif t == "rating_update":
            self.my_rating = msg["rating"]
            self.message = f"레이팅: {msg['rating']} (W{msg['wins']} L{msg['losses']} D{msg['draws']})"

        elif t == "chat":
            nick = msg.get("nick", "?")
            text = msg.get("msg", "")
            self.chat_msgs.append(f"{nick}: {text}")
            if len(self.chat_msgs) > 6:
                self.chat_msgs.pop(0)

        elif t == "opponent_disconnected":
            self.message = "상대방이 연결을 끊었습니다." if locale.lang=="ko" else "Opponent disconnected."
            self.game.game_over = True

        elif t == "disconnected":
            self.message = "서버 연결이 끊어졌습니다." if locale.lang=="ko" else "Disconnected from server."

    def _draw_waiting(self):
        """상대 대기 화면"""
        import math
        self.screen.fill((8, 8, 12))
        cx, cy = WINDOW_W // 2, WINDOW_H // 2
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.003)

        title = "상대방 대기 중..." if locale.lang=="ko" else "Waiting for opponent..."
        ts = self.title_font.render(title, True, C_GOLD)
        self.screen.blit(ts, (cx - ts.get_width()//2, cy - 60))

        code_label = "방 코드" if locale.lang=="ko" else "Room Code"
        cs = self.info_font.render(f"{code_label}:", True, C_MUTED)
        self.screen.blit(cs, (cx - cs.get_width()//2, cy - 20))

        code_color = tuple(int(c * (0.7 + 0.3 * pulse)) for c in (255, 215, 100))
        code_font = pygame.font.SysFont("consolas", 52, bold=True)
        code_s = code_font.render(self.online_room_code, True, code_color)
        self.screen.blit(code_s, (cx - code_s.get_width()//2, cy + 10))

        hint = "이 코드를 친구에게 알려주세요" if locale.lang=="ko" else "Share this code with your friend"
        hs = self.status_font.render(hint, True, C_MUTED)
        self.screen.blit(hs, (cx - hs.get_width()//2, cy + 80))

    def _draw_chat(self):
        """채팅창 (인게임)"""
        if not self.net:
            return
        px = PANEL_X
        y  = WINDOW_H - 180
        pad = 10

        # 채팅 메시지
        for msg in self.chat_msgs[-5:]:
            ms = self.status_font.render(msg[:30], True, C_MUTED)
            self.screen.blit(ms, (px + pad, y))
            y += 18

        # 입력창
        input_rect = pygame.Rect(px + pad, y + 4, PANEL_WIDTH - pad*2, 28)
        active = self.chat_active
        pygame.draw.rect(self.screen, (25, 20, 10) if active else (15, 12, 6), input_rect, border_radius=3)
        pygame.draw.rect(self.screen, C_GOLD if active else C_GOLD_DIM, input_rect, 1, border_radius=3)
        ct = self.chat_input + ("|" if active and pygame.time.get_ticks() % 1000 < 500 else "")
        placeholder = "채팅..." if locale.lang=="ko" else "Chat..."
        cs = self.status_font.render(ct if ct else placeholder, True, C_GOLD if ct else C_MUTED)
        self.screen.blit(cs, (input_rect.x + 6, input_rect.y + 5))
        self._chat_input_rect = input_rect


    def draw_ability_bar(self):
        """보드 아래 능력 바 (마우스 클릭)"""
        import math
        from chess_engine import PieceType, Color

        abilities = [
            ("Q", "Royal Decree",    PieceType.KING,   C_GOLD,           self._try_royal_decree),
            ("W", "Dom. Aura",       PieceType.QUEEN,  (180, 130, 220),  self._try_domination_aura),
            ("E", "Iron Fortress",   PieceType.ROOK,   (100, 160, 220),  self._try_iron_fortress),
            ("F", "Phantom Jump",    PieceType.KNIGHT, (100, 200, 140),  self._try_shadow_leap),
            ("S", "Into Shadows",    PieceType.BISHOP, (160, 100, 220),  self._try_into_shadows),
            ("D", "Land Mine",       PieceType.PAWN,   (200, 160,  80),  self._try_double_advance),
        ]

        btn_w = BOARD_SIZE // len(abilities)
        btn_h = 80
        mx, my = pygame.mouse.get_pos()
        self._ability_bar_rects = []

        for i, (key, name, ptype, color, fn) in enumerate(abilities):
            bx = BOARD_OFFSET_X + i * btn_w
            by = ABILITY_BAR_Y
            rect = pygame.Rect(bx, by, btn_w - 2, btn_h)
            self._ability_bar_rects.append((rect, fn, key))

            hov = rect.collidepoint(mx, my)
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.003 + i)

            # 현재 선택된 능력 모드 하이라이트
            active = False
            if self.ability_mode == "decree_select_piece" and ptype == PieceType.KING:   active = True
            if self.ability_mode == "aura_select"         and ptype == PieceType.QUEEN:  active = True
            if self.ability_mode == "leap_select"         and ptype == PieceType.KNIGHT: active = True
            if self.ability_mode == "advance_select"      and ptype == PieceType.PAWN:   active = True

            # 배경
            bg_col = tuple(int(c * 0.4) for c in color) if not (hov or active) else tuple(int(c * 0.25) for c in color)
            pygame.draw.rect(self.screen, bg_col, rect, border_radius=5)

            # 테두리
            border_alpha = int(180 + 75 * pulse) if (hov or active) else 80
            border_col = tuple(min(255, int(c * (0.6 + 0.4 * pulse))) for c in color) if (hov or active) else tuple(int(c * 0.5) for c in color)
            pygame.draw.rect(self.screen, border_col, rect, 2, border_radius=5)

            # 위쪽 색상 바
            top_bar = pygame.Rect(bx, by, btn_w - 2, 3)
            pygame.draw.rect(self.screen, color if (hov or active) else tuple(int(c*0.4) for c in color), top_bar)

            # 쿨다운 확인
            cd = self._get_ability_cooldown(ptype)
            on_cd = cd > 0

            # 기물 심볼
            symbols = {
                PieceType.KING:   ("♔", "♚"),
                PieceType.QUEEN:  ("♕", "♛"),
                PieceType.ROOK:   ("♖", "♜"),
                PieceType.KNIGHT: ("♘", "♞"),
                PieceType.BISHOP: ("♗", "♝"),
                PieceType.PAWN:   ("♙", "♟"),
            }
            sym_w, sym_b = symbols[ptype]
            cur_sym = sym_w if self.game.current_turn == Color.WHITE else sym_b
            piece_font = pygame.font.SysFont("segoeuisymbol", 26)
            sym_surf = piece_font.render(cur_sym, True, color if not on_cd else (80, 80, 80))
            self.screen.blit(sym_surf, (bx + 6, by + 6))

            # 능력 이름
            name_ko = locale.t(f"key_{['royal','aura','fortress','leap','shadows','advance'][i]}")
            name_surf = self.status_font.render(name_ko, True, color if not on_cd else (80, 80, 80))
            self.screen.blit(name_surf, (bx + 6, by + 36))

            # 키 힌트
            key_surf = self.label_font.render(f"[{key}]", True, (100, 100, 100))
            self.screen.blit(key_surf, (bx + btn_w - key_surf.get_width() - 6, by + 6))

            # 쿨다운 오버레이
            if on_cd:
                cd_surf = pygame.Surface((btn_w - 2, btn_h), pygame.SRCALPHA)
                cd_surf.fill((0, 0, 0, 120))
                self.screen.blit(cd_surf, (bx, by))
                cd_text = self.title_font.render(str(cd), True, (200, 80, 80))
                self.screen.blit(cd_text, (bx + btn_w//2 - cd_text.get_width()//2,
                                           by + btn_h//2 - cd_text.get_height()//2))

    def _get_ability_cooldown(self, ptype) -> int:
        """현재 턴 기준 해당 기물의 쿨다운 반환"""
        from chess_engine import PieceType, Color
        cur = self.game.current_turn
        for r in range(8):
            for c in range(8):
                from chess_engine import Position
                pos = Position(r, c)
                piece = self.game.board.get(pos)
                if piece and piece.color == cur and piece.piece_type == ptype:
                    return piece.ability_cooldown
        return 0

    def draw_panel(self):
        """우측 정보 패널"""
        px = PANEL_X
        pygame.draw.rect(self.screen, C_PANEL_BG, (px, BOARD_OFFSET_Y, PANEL_WIDTH, BOARD_SIZE))
        pygame.draw.line(self.screen, C_PANEL_LINE, (px, BOARD_OFFSET_Y), (px, BOARD_OFFSET_Y + BOARD_SIZE), 2)

        y = BOARD_OFFSET_Y + 10
        pad = 16

        # 타이틀
        title = self.title_font.render("Chess Abilities", True, C_GOLD)
        self.screen.blit(title, (px + pad, y))
        y += 34

        pygame.draw.line(self.screen, C_PANEL_LINE, (px + pad, y), (px + PANEL_WIDTH - pad, y))
        y += 14

        # 현재 턴
        turn_color = (255, 215, 100) if self.game.current_turn == Color.WHITE else (201, 168, 76)
        if self.ai:
            ai_side = "Black" if self.ai.color == Color.BLACK else "White"
            diff = self.ai.difficulty.capitalize()
            ai_label = self.status_font.render(f"AI: {ai_side} ({diff})", True, C_MUTED)
            self.screen.blit(ai_label, (px + pad, y - 16))
        turn_text = locale.t("white_turn") if self.game.current_turn == Color.WHITE else locale.t("black_turn")
        turn_surf = self.info_font.render(turn_text, True, turn_color)
        self.screen.blit(turn_surf, (px + pad, y))
        y += 28

        # 온라인: 내 색상 표시
        if self.net:
            my_col = Color.WHITE if self.my_color == "white" else Color.BLACK
            sym = "♔ 백" if self.my_color == "white" else "♚ 흑"
            my_col_color = (240, 240, 240) if self.my_color == "white" else (120, 120, 180)
            ms = self.status_font.render(f"나: {sym}", True, my_col_color)
            self.screen.blit(ms, (px + pad, y))
            y += 20

        # 수 번호
        move_surf = self.status_font.render(f"{locale.t("move_count")}: {self.game.move_count + 1}", True, C_MUTED)
        self.screen.blit(move_surf, (px + pad, y))
        y += 24

        # 타이머 표시
        if self.time_limit > 0:
            def fmt(s):
                s = max(0, int(s))
                return f"{s//60:02d}:{s%60:02d}"
            w_col = (220, 80, 80) if self.white_time < 30 else C_GOLD
            b_col = (220, 80, 80) if self.black_time < 30 else (180, 180, 180)
            w_label = "♔ " + fmt(self.white_time)
            b_label = "♚ " + fmt(self.black_time)
            w_surf = self.info_font.render(w_label, True, w_col)
            b_surf = self.info_font.render(b_label, True, b_col)
            # 현재 턴 강조
            if self.game.current_turn == Color.WHITE:
                pygame.draw.rect(self.screen, (40, 30, 10), (px + pad - 4, y - 2, PANEL_WIDTH - pad, 22), border_radius=3)
            self.screen.blit(w_surf, (px + pad, y))
            if self.game.current_turn == Color.BLACK:
                pygame.draw.rect(self.screen, (40, 30, 10), (px + pad - 4, y + 20, PANEL_WIDTH - pad, 22), border_radius=3)
            self.screen.blit(b_surf, (px + pad, y + 20))
            y += 50
        else:
            y += 6

        pygame.draw.line(self.screen, C_PANEL_LINE, (px + pad, y), (px + PANEL_WIDTH - pad, y))
        y += 14

        # 상태 메시지
        if self.message:
            msg_color = C_GOLD if "Check" in self.message else C_WHITE_TEXT
            msg_surf = self.status_font.render(self.message, True, msg_color)
            self.screen.blit(msg_surf, (px + pad, y))
        y += 30

        pygame.draw.line(self.screen, C_PANEL_LINE, (px + pad, y), (px + PANEL_WIDTH - pad, y))
        y += 14

        # 잡은 기물
        cap_title = self.label_font.render(locale.t("captured"), True, C_MUTED)
        self.screen.blit(cap_title, (px + pad, y))
        y += 20

        # 백이 잡은 흑 기물
        if self.captured_black:
            cap_font = pygame.font.SysFont("segoeuisymbol", 22)
            line = " ".join(self.captured_black)
            # 너무 길면 줄바꿈
            cap_surf = cap_font.render(line[:12], True, (200, 200, 200))
            self.screen.blit(cap_surf, (px + pad, y))
        y += 26

        # 흑이 잡은 백 기물
        if self.captured_white:
            cap_font = pygame.font.SysFont("segoeuisymbol", 22)
            line = " ".join(self.captured_white)
            cap_surf = cap_font.render(line[:12], True, (200, 200, 200))
            self.screen.blit(cap_surf, (px + pad, y))
        y += 36

        pygame.draw.line(self.screen, C_PANEL_LINE, (px + pad, y), (px + PANEL_WIDTH - pad, y))
        y += 14

        pygame.draw.line(self.screen, C_PANEL_LINE, (px + pad, y), (px + PANEL_WIDTH - pad, y))
        y += 14

        # 기권 / 무승부 버튼
        y = self.draw_resign_buttons(y, px, pad)

        pygame.draw.line(self.screen, C_PANEL_LINE, (px + pad, y), (px + PANEL_WIDTH - pad, y))
        y += 10

        # 온라인 정보
        if self.net:
            rating_s = self.status_font.render(f"{self.my_nick}  ★{self.my_rating}", True, C_GOLD)
            self.screen.blit(rating_s, (px + pad, y))
            y += 20
            if self.opponent_nick:
                opp_s = self.status_font.render(f"vs  {self.opponent_nick}", True, C_MUTED)
                self.screen.blit(opp_s, (px + pad, y))
            y += 24

        pygame.draw.line(self.screen, C_PANEL_LINE, (px + pad, y), (px + PANEL_WIDTH - pad, y))
        y += 10

        # 능력 패널
        y = self.draw_ability_panel(y, px, pad)
        self._draw_chat()

    # ── 입력 처리 ──

    def handle_click(self, px: int, py: int):
        """마우스 클릭 처리 (능력 모드 포함)"""
        # 무승부 제안 팝업 처리
        if self.draw_offer_pending:
            if hasattr(self, 'draw_acc_rect') and self.draw_acc_rect.collidepoint(px, py):
                # 수락 — 무승부
                self.game.game_over = True
                self.game.winner = None
                self.game.draw_reason = "agreement"
                self.draw_offer_pending = False
            elif hasattr(self, 'draw_dec_rect') and self.draw_dec_rect.collidepoint(px, py):
                # 거절
                self.draw_offer_pending = False
                self.message = locale.t("msg_draw_decline")
            return

        # 게임 오버 버튼 처리
        if self.game.game_over:
            if hasattr(self, 'gameover_again_rect') and self.gameover_again_rect.collidepoint(px, py):
                self.reset()
            elif hasattr(self, 'gameover_menu_rect') and self.gameover_menu_rect.collidepoint(px, py):
                self._go_to_menu = True
            return

        # 승진 팝업 처리 — 다른 클릭 차단
        if self.game.promotion_pending:
            from chess_engine import PieceType
            for pt, rect in getattr(self, 'promo_rects', {}).items():
                if rect.collidepoint(px, py):
                    self.game.promote(pt)
                    self.message = f"Promoted to {pt.value}!"
            return

        if self.game.game_over:
            return

        pos = self.pixel_to_pos(px, py)
        if pos is None:
            return

        # 온라인 모드: 내 턴이 아니면 이동 불가
        if self.net:
            my_color_enum = Color.WHITE if self.my_color == "white" else Color.BLACK
            if self.game.current_turn != my_color_enum:
                return

        piece = self.game.board.get(pos)

        # ── 오라 모드: 마비 대상 선택 ──
        if self.ability_mode == "aura_select":
            if pos in self.abilities.aura_targets:
                result = self.abilities.execute_domination_aura(pos)
                self.message = result.info
                if result.success and self.net and self.net.connected:
                    self.net.send_ability("domination_aura", {"target": [pos.row, pos.col]})
                self.ability_mode = ""
                self.selected = None
                self.legal_moves = []
            else:
                self.message = "Target not in Queen's range! Select another or press W to cancel."
            return

        # ── 연속 돌격 모드: 전진 칸 선택 ──
        if self.ability_mode == "advance_select":
            if pos in self.abilities.advance_moves:
                result = self.abilities.execute_double_advance(pos)
                self.message = result.info
                self.last_from = self.abilities.advance_pending if self.abilities.advance_pending else pos
                self.last_to = pos
            else:
                self.message = "Invalid square. Double Advance cancelled."
                self.abilities.cancel_double_advance()
            self.ability_mode = ""
            self.selected = None
            self.legal_moves = []
            return

        # ── 그림자 도약 모드: 잡기 목적지 선택 ──
        if self.ability_mode == "leap_select":
            if pos in self.abilities.leap_moves:
                from_leap = self.abilities.leap_pending
                result = self.abilities.execute_shadow_leap(pos)
                if result.success:
                    self.last_from = from_leap if from_leap else pos
                    self.last_to = pos
                    if result.captured:
                        sym = SYMBOLS[(result.captured.piece_type, result.captured.color)]
                        if result.captured.color == Color.BLACK:
                            self.captured_black.append(sym)
                        else:
                            self.captured_white.append(sym)
                    if self.net and self.net.connected:
                        self.net.send_ability("phantom_jump", {
                            "from": [from_leap.row, from_leap.col] if from_leap else None,
                            "to":   [pos.row, pos.col]
                        })
                    self.message = result.info
                else:
                    self.message = result.info
            else:
                self.message = "Not a valid target. Phantom Jump cancelled."
                self.abilities.cancel_shadow_leap()
            self.ability_mode = ""
            self.selected = None
            self.legal_moves = []
            return

        # ── 칙령 모드: 대상 기물 선택 ──
        if self.ability_mode == "decree_select_piece":
            result = self.abilities.select_royal_decree_target(pos)
            if result.success:
                self.decree_piece_pos = pos
                self.ability_mode = "decree_select_dest"
                self.legal_moves = self.abilities.royal_decree_targets
                self.message = "Select destination (move only, no capture)"
            else:
                self.message = result.info
                if piece is None or piece.color != self.game.current_turn:
                    self.abilities.cancel_royal_decree()
                    self.ability_mode = ""
                    self.selected = None
                    self.legal_moves = []
            return

        # ── 칙령 모드: 목적지 선택 ──
        if self.ability_mode == "decree_select_dest":
            if pos in self.abilities.royal_decree_targets:
                result = self.abilities.execute_royal_decree(self.decree_piece_pos, pos)
                self.message = "Royal Decree!" if result.success else result.info
                self.last_from = self.decree_piece_pos
                self.last_to   = pos
            else:
                self.message = "Invalid destination. Royal Decree cancelled."
                self.abilities.cancel_royal_decree()
            self.ability_mode = ""
            self.decree_piece_pos = None
            self.selected = None
            self.legal_moves = []
            return

        # ── 일반 모드 ──
        if self.selected is None:
            if piece and piece.color == self.game.current_turn:
                self.selected = pos
                self.legal_moves = MoveGenerator.get_legal_moves(self.game.board, pos, self.abilities)
            return

        if pos == self.selected:
            self.selected = None
            self.legal_moves = []
            return

        if piece and piece.color == self.game.current_turn:
            self.selected = pos
            self.legal_moves = MoveGenerator.get_legal_moves(self.game.board, pos, self.abilities)
            return

        # 이동 시도
        if pos in self.legal_moves:
            from_pos_send = self.selected  # 전송용 저장
            moving_color = self.game.current_turn  # 이동 전 색상 저장
            result = self.game.move(self.selected, pos)
            if result["success"]:
                self.last_from = from_pos_send
                self.last_to   = pos
                # 온라인 이동 전송
                if self.net and self.net.connected:
                    promo = result.get("promotion")
                    self.net.send_move(from_pos_send, pos, promo)
                    print(f"[이동 전송] {from_pos_send} → {pos}")
                # 지뢰 체크
                if hasattr(self.abilities, 'check_mines'):
                    mine_hit = self.abilities.check_mines(pos, moving_color)
                    if mine_hit:
                        self.message = "💥 지뢰!" if locale.lang == "ko" else "💥 Land Mine!"
                        self.sounds.play("capture")
                if result["captured"]:
                    cap = result["captured"]
                    sym = SYMBOLS[(cap.piece_type, cap.color)]
                    if cap.color == Color.BLACK:
                        self.captured_black.append(sym)
                    else:
                        self.captured_white.append(sym)
                    self.abilities.on_turn_end()

                info = result["info"]
                if info == "promotion_pending":
                    self.message = locale.t("msg_promotion")
                    self.selected = None
                    self.legal_moves = []
                    return
                if info == "checkmate":
                    self.message = locale.t("msg_checkmate")
                    self.sounds.play("checkmate")
                elif info == "stalemate":
                    self.message = locale.t("msg_stalemate")
                elif info == "check":
                    self.message = locale.t("msg_check")
                elif result["special"] == "castling":
                    self.message = locale.t("msg_castling")
                elif result["special"] == "promotion":
                    self.message = "Promotion! (Queen)"
                elif result["special"] == "en_passant":
                    self.message = locale.t("msg_en_passant")
                else:
                    self.message = ""
                # 은신 비숍이 공격하면 위치 드러남
                if result.get("special_extra") == "shadow_revealed":
                    self.message = "Shadow Revealed! Bishop position exposed!"
                # 이동/잡기 효과음
                if info != "checkmate":
                    if result["captured"]:
                        self.sounds.play("capture")
                    else:
                        self.sounds.play("move")
            self.selected = None
            self.legal_moves = []
        else:
            self.selected = None
            self.legal_moves = []

    def _try_royal_decree(self):
        """Q키 — 현재 선택된 킹으로 칙령 발동 시도"""
        from chess_engine import PieceType
        if self.game.game_over:
            return
        if self.ability_mode:
            # 이미 능력 모드면 취소
            self.abilities.cancel_royal_decree()
            self.ability_mode = ""
            self.selected = None
            self.legal_moves = []
            self.message = "Royal Decree cancelled."
            return
        # 현재 선택된 킹 또는 현재 턴의 킹 자동 탐색
        king_pos = None
        if self.selected:
            p = self.game.board.get(self.selected)
            if p and p.piece_type == PieceType.KING and p.color == self.game.current_turn:
                king_pos = self.selected
        if king_pos is None:
            king_pos = self.game.board.find_king(self.game.current_turn)
        if king_pos is None:
            return
        result = self.abilities.activate_royal_decree(king_pos)
        if result.success:
            self.sounds.play("ability")
            self.ability_mode = "decree_select_piece"
            self.selected = king_pos
            self.legal_moves = []
            self.message = "Royal Decree! Select a friendly piece to move."
        else:
            self.message = result.info






    def _try_double_advance(self):
        """D키 — 선택된 폰 또는 아무 폰으로 Double Advance 발동"""
        from chess_engine import PieceType, Position
        if self.game.game_over:
            return
        if self.ability_mode == "advance_select":
            self.abilities.cancel_double_advance()
            self.ability_mode = ""
            self.selected = None
            self.legal_moves = []
            self.message = "Double Advance cancelled."
            return
        pawn_pos = None
        if self.selected:
            p = self.game.board.get(self.selected)
            if p and p.piece_type == PieceType.PAWN and p.color == self.game.current_turn:
                pawn_pos = self.selected
        if pawn_pos is None:
            for r in range(8):
                for c in range(8):
                    p = self.game.board.get(Position(r, c))
                    if p and p.piece_type == PieceType.PAWN and p.color == self.game.current_turn:
                        if p.ability_cooldown == 0:
                            pawn_pos = Position(r, c)
                            break
                if pawn_pos:
                    break
        if pawn_pos is None:
            self.message = "No Pawn available (all on cooldown)!"
            return
        result = self.abilities.activate_double_advance(pawn_pos)
        if result.success:
            self.sounds.play("ability")
            self.ability_mode = "advance_select"
            self.selected = pawn_pos
            self.legal_moves = self.abilities.advance_moves
            self.message = result.info
        else:
            self.message = result.info

    def _try_into_shadows(self):
        """S키 — 선택된 비숍 또는 아무 비숍으로 Into the Shadows 발동"""
        from chess_engine import PieceType, Position
        if self.game.game_over:
            return
        bishop_pos = None
        if self.selected:
            p = self.game.board.get(self.selected)
            if p and p.piece_type == PieceType.BISHOP and p.color == self.game.current_turn:
                bishop_pos = self.selected
        if bishop_pos is None:
            for r in range(8):
                for c in range(8):
                    p = self.game.board.get(Position(r, c))
                    if p and p.piece_type == PieceType.BISHOP and p.color == self.game.current_turn:
                        if p.ability_cooldown == 0 and not p.is_hidden:
                            bishop_pos = Position(r, c)
                            break
                if bishop_pos:
                    break
        if bishop_pos is None:
            self.message = "No Bishop available!"
            return
        result = self.abilities.activate_into_shadows(bishop_pos)
        if result.success:
            self.sounds.play("ability")
            if self.net and self.net.connected:
                self.net.send_ability("into_shadows", {"bishop": [bishop_pos.row, bishop_pos.col]})
        self.message = result.info

    def _try_shadow_leap(self):
        """F키 — 선택된 나이트 또는 아무 나이트로 Shadow Leap 발동"""
        from chess_engine import PieceType, Position
        if self.game.game_over:
            return
        if self.ability_mode == "leap_select":
            self.abilities.cancel_shadow_leap()
            self.ability_mode = ""
            self.selected = None
            self.legal_moves = []
            self.message = "Shadow Leap cancelled."
            return
        knight_pos = None
        if self.selected:
            p = self.game.board.get(self.selected)
            if p and p.piece_type == PieceType.KNIGHT and p.color == self.game.current_turn:
                knight_pos = self.selected
        if knight_pos is None:
            for r in range(8):
                for c in range(8):
                    p = self.game.board.get(Position(r, c))
                    if p and p.piece_type == PieceType.KNIGHT and p.color == self.game.current_turn:
                        if p.ability_cooldown == 0:
                            knight_pos = Position(r, c)
                            break
                if knight_pos:
                    break
        if knight_pos is None:
            self.message = "No Knight available (all on cooldown)!"
            return
        result = self.abilities.activate_shadow_leap(knight_pos)
        if result.success:
            self.sounds.play("ability")
            self.last_from = knight_pos
            self.last_to = self.abilities.leap_moves[0] if self.abilities.leap_moves else knight_pos
            self.message = result.info
            self.selected = None
            self.legal_moves = []
            self.ability_mode = ""
        else:
            self.message = result.info

    def _try_iron_fortress(self):
        """E키 — 선택된 룩 또는 아무 룩으로 Iron Fortress 발동"""
        from chess_engine import PieceType, Position
        if self.game.game_over:
            return
        rook_pos = None
        if self.selected:
            p = self.game.board.get(self.selected)
            if p and p.piece_type == PieceType.ROOK and p.color == self.game.current_turn:
                rook_pos = self.selected
        if rook_pos is None:
            for r in range(8):
                for c in range(8):
                    p = self.game.board.get(Position(r, c))
                    if p and p.piece_type == PieceType.ROOK and p.color == self.game.current_turn:
                        if p.ability_cooldown == 0:
                            rook_pos = Position(r, c)
                            break
                if rook_pos:
                    break
        if rook_pos is None:
            self.message = "No Rook available (all on cooldown)!"
            return
        result = self.abilities.activate_iron_fortress(rook_pos)
        if result.success:
            self.sounds.play("ability")
            if self.net and self.net.connected:
                self.net.send_ability("iron_fortress", {"rook": [rook_pos.row, rook_pos.col]})
        self.message = result.info if result.success else result.info

    def _try_domination_aura(self):
        """W키 — 현재 선택된 퀸으로 Domination Aura 발동 시도"""
        from chess_engine import PieceType
        if self.game.game_over:
            return
        if self.ability_mode == "aura_select":
            self.abilities.cancel_domination_aura()
            self.ability_mode = ""
            self.selected = None
            self.legal_moves = []
            self.message = "Domination Aura cancelled."
            return
        # 선택된 퀸 또는 현재 턴의 퀸 자동 탐색
        queen_pos = None
        if self.selected:
            p = self.game.board.get(self.selected)
            if p and p.piece_type == PieceType.QUEEN and p.color == self.game.current_turn:
                queen_pos = self.selected
        if queen_pos is None:
            # 보드에서 퀸 찾기
            for r in range(8):
                for c in range(8):
                    p = self.game.board.get(Position(r, c))
                    if p and p.piece_type == PieceType.QUEEN and p.color == self.game.current_turn:
                        queen_pos = Position(r, c)
                        break
                if queen_pos:
                    break
        if queen_pos is None:
            self.message = "No Queen on the board!"
            return
        result = self.abilities.activate_domination_aura(queen_pos)
        if result.success:
            self.sounds.play("ability")
            self.ability_mode = "aura_select"
            self.selected = queen_pos
            self.legal_moves = self.abilities.aura_targets
            self.message = "Domination Aura! Click any enemy piece to paralyze."
        else:
            self.message = result.info

    def draw_ability_panel(self, y: int, px: int, pad: int):
        """능력 상태 패널 — 설명 + 쿨다운 카드형"""
        from chess_engine import PieceType, Position

        ab_title = self.label_font.render(locale.t("abilities_title") if hasattr(locale, "t") else "Abilities", True, C_GOLD)
        self.screen.blit(ab_title, (px + pad, y))
        y += 22

        abilities = [
            (PieceType.KING,   locale.t("ability_royal"),    locale.t("desc_royal"),    C_GOLD,          "decree"),
            (PieceType.QUEEN,  locale.t("ability_aura"),     locale.t("desc_aura"),     (180,130,220),   "aura"),
            (PieceType.ROOK,   locale.t("ability_fortress"), locale.t("desc_fortress"), (100,160,220),   "fortress"),
            (PieceType.KNIGHT, locale.t("ability_leap"),     locale.t("desc_leap"),     (100,200,140),   "leap"),
            (PieceType.BISHOP, locale.t("ability_shadows"),  locale.t("desc_shadows"),  (160,100,220),   "shadow"),
            (PieceType.PAWN,   locale.t("ability_advance"),  locale.t("desc_advance"),  (200,160, 80),   "mine"),
        ]

        for ptype, name, desc, color, tag in abilities:
            # 쿨다운 계산
            cd = 0
            active = False
            for r in range(8):
                for c in range(8):
                    p = self.game.board.get(Position(r, c))
                    if p and p.piece_type == ptype and p.color == self.game.current_turn:
                        cd = max(cd, p.ability_cooldown)
            if ptype == PieceType.KING:
                used = self.abilities.royal_decree_used.get(self.game.current_turn.value, False)
                if used: cd = 99
            active = (
                (tag == "decree" and self.ability_mode in ("decree_select_piece","decree_select_dest")) or
                (tag == "aura"   and self.ability_mode == "aura_select") or
                (tag == "leap"   and self.ability_mode == "leap_select")
            )

            # 카드 배경
            card_h = 42
            card_rect = pygame.Rect(px + pad, y, PANEL_WIDTH - pad * 2, card_h)
            bg = (40, 30, 10) if active else (20, 18, 10)
            pygame.draw.rect(self.screen, bg, card_rect, border_radius=4)
            border_col = color if active else tuple(int(c*0.5) for c in color)
            pygame.draw.rect(self.screen, border_col, card_rect, 1, border_radius=4)
            # 왼쪽 색 바
            pygame.draw.rect(self.screen, color if not cd else (60,60,60),
                             pygame.Rect(px + pad, y, 3, card_h), border_radius=2)

            # 능력 이름
            name_col = color if not cd else C_MUTED
            ns = self.status_font.render(name, True, name_col)
            self.screen.blit(ns, (px + pad + 8, y + 4))

            # 설명 (첫 줄만)
            desc_line = desc.split("\n")[0]
            ds = self.label_font.render(desc_line, True, C_MUTED)
            self.screen.blit(ds, (px + pad + 8, y + 22))

            # 쿨다운 또는 ACTIVE 표시
            if active:
                badge = self.label_font.render("ACTIVE", True, (100, 220, 100))
            elif cd == 99:
                badge = self.label_font.render("USED", True, C_MUTED)
            elif cd > 0:
                badge = self.label_font.render(f"CD:{cd}", True, (220, 100, 100))
            else:
                badge = self.label_font.render("READY", True, color)
            self.screen.blit(badge, (px + PANEL_WIDTH - pad - badge.get_width() - 4, y + 14))

            y += card_h + 4

        return y

    def reset(self):
        """게임 재시작"""
        self.game          = Game()
        self.selected      = None
        self.legal_moves   = []
        self.last_from     = None
        self.last_to       = None
        self.message       = ""
        self.captured_white = []
        self.captured_black = []
        self.abilities = AbilitySystem(self.game)
        self.game.ability_system = self.abilities
        self.ability_mode = ""
        self.hidden_bishop_revealed = {}
        self._go_to_menu = False
        self.draw_offer_pending = False
        self.draw_offer_by = None
        # 타이머
        self.time_limit = 0
        self.white_time = 0
        self.black_time = 0
        self.last_tick = pygame.time.get_ticks()
        # AI 는 reset 시 유지
        self.decree_piece_pos = None

    # ── 메인 루프 ──

    def run(self):
        while True:
            # 이벤트 처리
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_r:
                        self.reset()
                    # Q키 — 선택된 킹으로 Royal Decree 발동
                    if event.key == pygame.K_q:
                        self._try_royal_decree()
                    # W키 — 선택된 퀸으로 Domination Aura 발동
                    if event.key == pygame.K_w:
                        self._try_domination_aura()
                    # E키 — 선택된 룩으로 Iron Fortress 발동
                    if event.key == pygame.K_e:
                        self._try_iron_fortress()
                    # R키 — 선택된 나이트로 Shadow Leap 발동 (단, R은 재시작과 충돌 방지)
                    if event.key == pygame.K_f:
                        self._try_shadow_leap()
                    # S키 — 비숍 Into the Shadows
                    if event.key == pygame.K_s:
                        self._try_into_shadows()
                    # D키 — 폰 Double Advance
                    if event.key == pygame.K_d:
                        self._try_double_advance()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 좌클릭
                        # 능력 바 클릭 체크
                        clicked_ability = False
                        for rect, fn, key in getattr(self, '_ability_bar_rects', []):
                            if rect.collidepoint(*event.pos):
                                fn()
                                clicked_ability = True
                                break
                        if not clicked_ability:
                            self.handle_click(*event.pos)

            # 그리기
            self.screen.fill(C_PANEL_BG)
            # 오프스크린 서피스에 렌더링
            orig_screen = self.screen
            self.screen = self._render_surf

            self.draw_board()
            self.draw_board_border()
            self.draw_blockades()
            self.draw_mines()
            self.draw_coordinates()
            self.draw_check_highlight()
            self.draw_paralyzed()
            self.draw_move_hints()
            self.draw_pieces()
            self.draw_ability_bar()
            self.draw_panel()
            # 승진 팝업
            if self.game.promotion_pending:
                self.draw_promotion_popup()
            # 무승부 제안 팝업
            if self.draw_offer_pending:
                self.draw_draw_offer_popup()
            # 게임 오버 화면
            if self.game.game_over:
                self.draw_game_over()

            # screen 복원
            self.screen = orig_screen

            # 전체화면이면 render_surf 를 화면 크기에 맞게 스케일링
            if self._fullscreen:
                sw, sh = self.screen.get_size()
                # 비율 유지하면서 중앙에 배치
                scale = min(sw / WINDOW_W, sh / WINDOW_H)
                scaled_w = int(WINDOW_W * scale)
                scaled_h = int(WINDOW_H * scale)
                offset_x = (sw - scaled_w) // 2
                offset_y = (sh - scaled_h) // 2
                scaled = pygame.transform.smoothscale(self._render_surf, (scaled_w, scaled_h))
                self.screen.fill((0, 0, 0))
                self.screen.blit(scaled, (offset_x, offset_y))
            else:
                self.screen.blit(self._render_surf, (0, 0))

            pygame.display.flip()
            self.clock.tick(FPS)

            # 네트워크 메시지 처리 (대기 화면보다 먼저)
            if self.net and self.net.connected:
                for msg in self.net.poll():
                    self._handle_net_msg(msg)

            # 온라인 대기 화면
            if self.waiting_opponent:
                self._draw_waiting()
                pygame.display.flip()
                self.clock.tick(FPS)
                # 대기 중에도 네트워크 메시지 처리
                if self.net and self.net.connected:
                    for msg in self.net.poll():
                        self._handle_net_msg(msg)
                continue

            # 타이머 감소
            if self.time_limit > 0 and not self.game.game_over and not self.game.promotion_pending:
                now = pygame.time.get_ticks()
                elapsed = (now - self.last_tick) / 1000.0
                self.last_tick = now
                if self.game.current_turn == Color.WHITE:
                    self.white_time = max(0, self.white_time - elapsed)
                    if self.white_time <= 0:
                        self.game.game_over = True
                        self.game.winner = Color.BLACK
                        self.game.draw_reason = "timeout"
                        self.sounds.play("checkmate")
                else:
                    self.black_time = max(0, self.black_time - elapsed)
                    if self.black_time <= 0:
                        self.game.game_over = True
                        self.game.winner = Color.WHITE
                        self.game.draw_reason = "timeout"
                        self.sounds.play("checkmate")

            # AI 이동 처리
            if (self.ai and
                    not self.game.game_over and
                    not self.game.promotion_pending and
                    not self.draw_offer_pending and
                    self.game.current_turn == self.ai.color):
                pygame.time.wait(300)  # 약간의 딜레이
                move = self.ai.get_move(self.game)
                if move:
                    from_pos, to_pos = move
                    result = self.game.move(from_pos, to_pos)
                    if result["success"]:
                        self.last_from = from_pos
                        self.last_to = to_pos
                        if result["captured"]:
                            self.sounds.play("capture")
                            sym = SYMBOLS.get((result["captured"].piece_type, result["captured"].color), "?")
                            if result["captured"].color == Color.BLACK:
                                self.captured_black.append(sym)
                            else:
                                self.captured_white.append(sym)
                        else:
                            self.sounds.play("move")
                        if result["info"] == "checkmate":
                            self.sounds.play("checkmate")
                            self.message = locale.t("msg_checkmate")
                        elif result["info"] == "check":
                            self.message = locale.t("msg_check")
                        elif result["info"] == "promotion_pending":
                            # AI는 자동으로 퀸으로 승진
                            from chess_engine import PieceType as PT
                            self.game.promote(PieceType.QUEEN)
                            self.message = locale.t("msg_ai_promoted")
                        self.selected = None
                        self.legal_moves = []

            # 메인 메뉴로 돌아가기
            if self._go_to_menu:
                return "menu"


# ──────────────────────────────────────────────
# 3. 실행
# ──────────────────────────────────────────────

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Chess Abilities")
    clock = pygame.time.Clock()

    while True:
        # 시작 화면
        start = StartScreen(screen, clock)
        result = start.run()

        # 게임 실행
        if result["action"] == "online":
            from network import NetworkClient
            import time as _time

            net = NetworkClient()
            url = result["server_host"]  # wss://... URL

            # 연결 중 화면 표시
            screen.fill((8, 8, 12))
            font_conn = pygame.font.SysFont("malgun gothic", 28)
            txt = font_conn.render("서버 연결 중...", True, (200, 160, 60))
            screen.blit(txt, (screen.get_width()//2 - txt.get_width()//2,
                               screen.get_height()//2 - txt.get_height()//2))
            pygame.display.flip()

            connected = net.connect(url, timeout=10.0)
            print(f"[연결 결과] {connected}, URL={url}")

            if connected:
                renderer = ChessRenderer(screen=screen, clock=clock)
                renderer.net = net
                renderer.sounds.set_volume(result["volume"])
                user = getattr(start, 'logged_in_user', None) or {}
                nick = user.get("nickname", "Guest")
                renderer.my_nick = nick
                renderer.my_rating = user.get("rating", 1200)
                net.login(nick)
                _time.sleep(0.5)
                for msg in net.poll():
                    if msg.get("type") == "login_ok":
                        renderer.my_rating = msg.get("rating", 1200)
                if result["online_action"] == "host":
                    tl = result.get("time_limit", 0)
                    net.create_room(tl)
                    renderer.waiting_opponent = True
                else:
                    net.join_room(result.get("room_code", ""))
                    renderer.waiting_opponent = False
                ret = renderer.run()
                net.disconnect()
            else:
                # 연결 실패 메시지
                screen.fill((8, 8, 12))
                font_err = pygame.font.SysFont("malgun gothic", 24)
                err = font_err.render("연결 실패! 서버 주소를 확인하세요.", True, (220, 80, 80))
                screen.blit(err, (screen.get_width()//2 - err.get_width()//2,
                                   screen.get_height()//2))
                pygame.display.flip()
                _time.sleep(2)
                ret = "menu"
            if ret != "menu":
                break

        elif result["action"] == "play":
            ai = None
            if result.get("mode") == "ai":
                ai = ChessAI(color=Color.BLACK, difficulty=result.get("difficulty", "medium"))
            renderer = ChessRenderer(screen=screen, clock=clock, ai=ai)
            renderer.sounds.set_volume(result["volume"])
            tl = result.get("time_limit", 0)
            renderer.time_limit = tl
            renderer.white_time = tl
            renderer.black_time = tl
            renderer.last_tick = pygame.time.get_ticks()
            ret = renderer.run()
            if ret != "menu":
                break  # 메뉴로 안 돌아가면 종료
