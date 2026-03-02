# ============================================================
#  Chess Abilities — 체스 이동 규칙 엔진 (Phase 1)
#  pygame 렌더링 없이 순수 로직만 구현
#  나중에 main.py에서 pygame과 연결할 수 있도록 설계됨
# ============================================================

from __future__ import annotations
from enum import Enum, auto
from typing import Optional
from dataclasses import dataclass, field
import copy


# ──────────────────────────────────────────────
# 1. 기본 열거형 & 데이터 타입
# ──────────────────────────────────────────────

class Color(Enum):
    WHITE = "white"
    BLACK = "black"

    def opponent(self) -> Color:
        return Color.BLACK if self == Color.WHITE else Color.WHITE


class PieceType(Enum):
    KING   = "K"
    QUEEN  = "Q"
    ROOK   = "R"
    BISHOP = "B"
    KNIGHT = "N"
    PAWN   = "P"


@dataclass(frozen=True)
class Position:
    """체스판 좌표. row: 0(위) ~ 7(아래), col: 0(왼) ~ 7(오른)"""
    row: int
    col: int

    def is_valid(self) -> bool:
        return 0 <= self.row <= 7 and 0 <= self.col <= 7

    def __add__(self, other: tuple) -> Position:
        return Position(self.row + other[0], self.col + other[1])

    def __eq__(self, other) -> bool:
        if isinstance(other, Position):
            return self.row == other.row and self.col == other.col
        return False

    def __hash__(self) -> int:
        return hash((self.row, self.col))

    def __repr__(self) -> str:
        col_letter = "abcdefgh"[self.col]
        return f"{col_letter}{8 - self.row}"


# ──────────────────────────────────────────────
# 2. 기물 클래스
# ──────────────────────────────────────────────

@dataclass
class Piece:
    piece_type: PieceType
    color: Color
    has_moved: bool = False          # 캐슬링 / 폰 첫 이동 판단용
    ability_cooldown: int = 0        # 남은 쿨다운 턴 수
    is_hidden: bool = False          # 비숍 은신 상태
    hidden_turns_left: int = 0       # 은신 남은 턴
    is_paralyzed: bool = False       # 마비 상태
    paralyzed_turns: int = 0         # 마비 남은 턴

    def symbol(self) -> str:
        """터미널 출력용 기호"""
        symbols = {
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
        return symbols[(self.piece_type, self.color)]

    def __repr__(self) -> str:
        return f"{self.color.value[0].upper()}{self.piece_type.value}"


# ──────────────────────────────────────────────
# 3. 이동 규칙 계산
# ──────────────────────────────────────────────

class MoveGenerator:
    """각 기물의 이동 가능한 칸을 반환하는 클래스 (능력 제외, 순수 체스 규칙)"""

    @staticmethod
    def get_raw_moves(board: Board, pos: Position, skip_castling: bool = False) -> list[Position]:
        """체크 검증 없이 이동 가능한 칸 목록 반환"""
        piece = board.get(pos)
        if piece is None:
            return []

        if piece.piece_type == PieceType.KING:
            return MoveGenerator._king_moves(board, pos, piece, skip_castling)

        dispatch = {
            PieceType.QUEEN:  MoveGenerator._queen_moves,
            PieceType.ROOK:   MoveGenerator._rook_moves,
            PieceType.BISHOP: MoveGenerator._bishop_moves,
            PieceType.KNIGHT: MoveGenerator._knight_moves,
            PieceType.PAWN:   MoveGenerator._pawn_moves,
        }
        return dispatch[piece.piece_type](board, pos, piece)

    @staticmethod
    def get_legal_moves(board: Board, pos: Position, ability_system=None) -> list[Position]:
        """체크를 유발하지 않는 합법적인 이동만 반환 (봉쇄/은신/마비 필터 포함)"""
        piece = board.get(pos)
        if piece is None:
            return []

        # 마비/기절된 기물은 이동 불가
        if piece.is_paralyzed or getattr(piece, "stunned", False):
            return []

        legal = []
        for target in MoveGenerator.get_raw_moves(board, pos):
            # 봉쇄된 칸으로는 이동 불가
            if ability_system and ability_system.is_blockaded(pos, target, piece.color):
                continue

            # 임시로 이동해보고 체크가 되는지 확인
            test_board = board.clone()
            test_board._move_piece(pos, target)
            if not test_board.is_in_check(piece.color):
                legal.append(target)
        return legal

    # ── 개별 기물 이동 규칙 ──

    @staticmethod
    def _sliding_moves(board: Board, pos: Position, piece: Piece,
                       directions: list[tuple]) -> list[Position]:
        """룩, 비숍, 퀸처럼 여러 칸을 직선으로 이동하는 기물용"""
        moves = []
        for dr, dc in directions:
            cur = pos + (dr, dc)
            while cur.is_valid():
                target = board.get(cur)
                if target is None:
                    moves.append(cur)
                elif target.color != piece.color:
                    moves.append(cur)  # 적 기물 잡기
                    break
                else:
                    break  # 아군 기물 막힘
                cur = cur + (dr, dc)
        return moves

    @staticmethod
    def _king_moves(board: Board, pos: Position, piece: Piece, skip_castling: bool = False) -> list[Position]:
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                target = pos + (dr, dc)
                if target.is_valid():
                    t = board.get(target)
                    if t is None or t.color != piece.color:
                        moves.append(target)

        # 캐슬링
        if not skip_castling:
            moves += MoveGenerator._castling_moves(board, pos, piece)
        return moves

    @staticmethod
    def _castling_moves(board: Board, pos: Position, piece: Piece) -> list[Position]:
        """캐슬링 가능 여부 확인"""
        moves = []
        if piece.has_moved or board.is_in_check(piece.color):
            return moves

        row = pos.row
        # 킹사이드 캐슬링
        rook_pos = Position(row, 7)
        rook = board.get(rook_pos)
        if (rook and rook.piece_type == PieceType.ROOK
                and not rook.has_moved
                and board.get(Position(row, 5)) is None
                and board.get(Position(row, 6)) is None):
            # 경유 칸도 체크 상태가 아닌지 확인
            test1 = board.clone(); test1._move_piece(pos, Position(row, 5))
            test2 = board.clone(); test2._move_piece(pos, Position(row, 6))
            if (not test1.is_in_check(piece.color)
                    and not test2.is_in_check(piece.color)):
                moves.append(Position(row, 6))

        # 퀸사이드 캐슬링
        rook_pos = Position(row, 0)
        rook = board.get(rook_pos)
        if (rook and rook.piece_type == PieceType.ROOK
                and not rook.has_moved
                and board.get(Position(row, 1)) is None
                and board.get(Position(row, 2)) is None
                and board.get(Position(row, 3)) is None):
            test1 = board.clone(); test1._move_piece(pos, Position(row, 3))
            test2 = board.clone(); test2._move_piece(pos, Position(row, 2))
            if (not test1.is_in_check(piece.color)
                    and not test2.is_in_check(piece.color)):
                moves.append(Position(row, 2))
        return moves

    @staticmethod
    def _queen_moves(board: Board, pos: Position, piece: Piece) -> list[Position]:
        dirs = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
        return MoveGenerator._sliding_moves(board, pos, piece, dirs)

    @staticmethod
    def _rook_moves(board: Board, pos: Position, piece: Piece) -> list[Position]:
        return MoveGenerator._sliding_moves(board, pos, piece, [(1,0),(-1,0),(0,1),(0,-1)])

    @staticmethod
    def _bishop_moves(board: Board, pos: Position, piece: Piece) -> list[Position]:
        return MoveGenerator._sliding_moves(board, pos, piece, [(1,1),(1,-1),(-1,1),(-1,-1)])

    @staticmethod
    def _knight_moves(board: Board, pos: Position, piece: Piece) -> list[Position]:
        moves = []
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            target = pos + (dr, dc)
            if target.is_valid():
                t = board.get(target)
                if t is None or t.color != piece.color:
                    moves.append(target)
        return moves

    @staticmethod
    def _pawn_moves(board: Board, pos: Position, piece: Piece) -> list[Position]:
        moves = []
        direction = -1 if piece.color == Color.WHITE else 1  # 흰색은 위로

        # 전진 1칸
        one_step = pos + (direction, 0)
        if one_step.is_valid() and board.get(one_step) is None:
            moves.append(one_step)
            # 첫 이동 시 2칸
            if not piece.has_moved:
                two_step = pos + (direction * 2, 0)
                if board.get(two_step) is None:
                    moves.append(two_step)

        # 대각선 잡기
        for dc in [-1, 1]:
            attack = pos + (direction, dc)
            if attack.is_valid():
                t = board.get(attack)
                if t and t.color != piece.color:
                    moves.append(attack)

        # 앙파상
        if board.en_passant_target:
            ep = board.en_passant_target
            if abs(ep.col - pos.col) == 1 and ep.row == pos.row + direction:
                moves.append(ep)

        return moves


# ──────────────────────────────────────────────
# 4. 보드 클래스
# ──────────────────────────────────────────────

class Board:
    def __init__(self):
        self._grid: list[list[Optional[Piece]]] = [[None] * 8 for _ in range(8)]
        self.en_passant_target: Optional[Position] = None  # 앙파상 가능 칸
        self._setup()

    def _setup(self):
        """초기 기물 배치"""
        back_row = [PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN,
                    PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK]

        for col, pt in enumerate(back_row):
            self._grid[0][col] = Piece(pt, Color.BLACK)   # 흑 기물 — 위 (row 0)
            self._grid[7][col] = Piece(pt, Color.WHITE)   # 백 기물 — 아래 (row 7)

        for col in range(8):
            self._grid[1][col] = Piece(PieceType.PAWN, Color.BLACK)  # 흑 폰 — row 1
            self._grid[6][col] = Piece(PieceType.PAWN, Color.WHITE)  # 백 폰 — row 6

    def get(self, pos: Position) -> Optional[Piece]:
        if not pos.is_valid():
            return None
        return self._grid[pos.row][pos.col]

    def set(self, pos: Position, piece: Optional[Piece]):
        self._grid[pos.row][pos.col] = piece

    def clone(self) -> Board:
        new = Board.__new__(Board)
        new._grid = [[copy.copy(self._grid[r][c]) for c in range(8)] for r in range(8)]
        new.en_passant_target = self.en_passant_target
        return new

    def _move_piece(self, from_pos: Position, to_pos: Position):
        """내부 이동 처리 (체크 검증 없음, clone 후 사용)"""
        piece = self.get(from_pos)
        self.set(to_pos, piece)
        self.set(from_pos, None)
        if piece:
            piece.has_moved = True

    def find_king(self, color: Color) -> Optional[Position]:
        for r in range(8):
            for c in range(8):
                p = self._grid[r][c]
                if p and p.piece_type == PieceType.KING and p.color == color:
                    return Position(r, c)
        return None

    def is_in_check(self, color: Color) -> bool:
        """해당 색의 킹이 체크 상태인지 확인"""
        king_pos = self.find_king(color)
        if king_pos is None:
            return False
        opponent = color.opponent()
        for r in range(8):
            for c in range(8):
                p = self._grid[r][c]
                if p and p.color == opponent:
                    raw = MoveGenerator.get_raw_moves(self, Position(r, c), skip_castling=True)
                    if king_pos in raw:
                        return True
        return False

    def is_checkmate(self, color: Color) -> bool:
        """체크메이트 확인"""
        if not self.is_in_check(color):
            return False
        return self._has_no_legal_moves(color)

    def is_stalemate(self, color: Color) -> bool:
        """스테일메이트 확인"""
        if self.is_in_check(color):
            return False
        return self._has_no_legal_moves(color)

    def _has_no_legal_moves(self, color: Color) -> bool:
        for r in range(8):
            for c in range(8):
                p = self._grid[r][c]
                if p and p.color == color:
                    if MoveGenerator.get_legal_moves(self, Position(r, c)):
                        return False
        return True

    def print_board(self, perspective: Color = Color.WHITE,
                    highlights: list[Position] = None):
        """터미널에 보드 출력"""
        highlights = highlights or []
        print("\n   a  b  c  d  e  f  g  h")
        print("  ─────────────────────────")
        # 백 시점: row 0(rank 8, 흑 진영)이 위, row 7(rank 1, 백 진영)이 아래
        rows = range(8) if perspective == Color.WHITE else range(7, -1, -1)
        for r in rows:
            rank = 8 - r
            row_str = f"{rank} │"
            for c in range(8):
                pos = Position(r, c)
                piece = self._grid[r][c]
                is_highlight = pos in highlights
                cell = f"[{piece.symbol()}]" if piece else "[ ]"
                if is_highlight:
                    cell = f"<{piece.symbol() if piece else ' '}>"
                row_str += cell
            print(row_str + f"│ {rank}")
        print("  ─────────────────────────")
        print("   a  b  c  d  e  f  g  h\n")


# ──────────────────────────────────────────────
# 5. 게임 클래스 (턴 관리 + 이동 실행)
# ──────────────────────────────────────────────

class Game:
    def __init__(self):
        self.board = Board()
        self.current_turn = Color.WHITE
        self.move_count = 0
        self.ability_used_this_turn = False   # 턴당 1개 기물만 능력 사용 가능
        self.ability_system = None               # AbilitySystem 참조 (main에서 주입)
        self.promotion_pending = None            # 승진 대기 중인 폰 위치
        self.draw_reason: str = ""               # 무승부 이유 (stalemate/agreement)
        self.game_over = False
        self.winner: Optional[Color] = None

    def move(self, from_pos: Position, to_pos: Position) -> dict:
        """
        이동 실행. 반환값 예시:
        {"success": True, "info": "moved", "captured": Piece or None, "special": "promotion" or None}
        """
        if self.game_over:
            return {"success": False, "info": "game_over"}

        piece = self.board.get(from_pos)
        if piece is None:
            return {"success": False, "info": "no_piece"}
        if piece.color != self.current_turn:
            return {"success": False, "info": "wrong_turn"}

        legal = MoveGenerator.get_legal_moves(self.board, from_pos)
        if to_pos not in legal:
            return {"success": False, "info": "illegal_move"}

        captured = self.board.get(to_pos)
        special = None

        # ── 캐슬링 처리 ──
        if piece.piece_type == PieceType.KING and abs(to_pos.col - from_pos.col) == 2:
            special = "castling"
            row = from_pos.row
            if to_pos.col == 6:  # 킹사이드
                self.board._move_piece(Position(row, 7), Position(row, 5))
            else:                # 퀸사이드
                self.board._move_piece(Position(row, 0), Position(row, 3))

        # ── 앙파상 처리 ──
        if (piece.piece_type == PieceType.PAWN
                and self.board.en_passant_target == to_pos):
            special = "en_passant"
            direction = 1 if piece.color == Color.WHITE else -1
            captured_pos = Position(to_pos.row + direction, to_pos.col)
            captured = self.board.get(captured_pos)
            self.board.set(captured_pos, None)

        # ── 앙파상 타겟 갱신 ──
        # 2칸 전진: 중간 칸 1개 / 3칸 전진: 지나친 칸 중 마지막 칸 설정
        if piece.piece_type == PieceType.PAWN:
            dist = abs(to_pos.row - from_pos.row)
            if dist == 2:
                mid_row = (from_pos.row + to_pos.row) // 2
                self.board.en_passant_target = Position(mid_row, from_pos.col)
            elif dist == 3:
                # 3칸 전진 — 바로 직전 칸(to_pos 에서 1칸 뒤)을 타겟으로
                direction = 1 if to_pos.row > from_pos.row else -1
                self.board.en_passant_target = Position(to_pos.row - direction, from_pos.col)
            else:
                self.board.en_passant_target = None
        else:
            self.board.en_passant_target = None

        # ── 실제 이동 ──
        self.board._move_piece(from_pos, to_pos)

        # ── 폰 승진 처리 ──
        moved_piece = self.board.get(to_pos)
        if moved_piece and moved_piece.piece_type == PieceType.PAWN:
            if to_pos.row == 0 or to_pos.row == 7:
                special = "promotion"
                self.promotion_pending = to_pos  # UI에서 선택 대기

        # 승진 대기 중이면 턴 종료 보류
        if special == "promotion":
            return {"success": True, "info": "promotion_pending",
                    "captured": captured, "special": "promotion"}

        # 은신 중 공격하면 은신 해제
        if captured and piece.is_hidden:
            piece.is_hidden = False
            piece.hidden_turns_left = 0
            special = "shadow_revealed"

        # ── 턴 종료 처리 ──
        self._end_turn()

        # ── 체크메이트 / 스테일메이트 확인 ──
        opponent = self.current_turn
        if self.board.is_checkmate(opponent):
            self.game_over = True
            self.winner = opponent.opponent()
            return {"success": True, "info": "checkmate", "captured": captured, "special": special}
        if self.board.is_stalemate(opponent):
            self.game_over = True
            return {"success": True, "info": "stalemate", "captured": captured, "special": special}

        in_check = self.board.is_in_check(opponent)
        return {
            "success": True,
            "info": "check" if in_check else "moved",
            "captured": captured,
            "special": special
        }


    def promote(self, piece_type: PieceType):
        """승진 실행 — promotion_pending 위치의 폰을 선택한 기물로 변경"""
        if self.promotion_pending is None:
            return
        piece = self.board.get(self.promotion_pending)
        if piece:
            piece.piece_type = piece_type
        pos = self.promotion_pending
        self.promotion_pending = None

        # 이제 턴 종료 처리
        self._end_turn()

        # 체크메이트 / 스테일메이트 확인
        opponent = self.current_turn
        if self.board.is_checkmate(opponent):
            self.game_over = True
            self.winner = opponent.opponent()
        elif self.board.is_stalemate(opponent):
            self.game_over = True

    def _end_turn(self):
        self.current_turn = self.current_turn.opponent()
        self.move_count += 1
        self.ability_used_this_turn = False
        # 쿨다운 & 은신 턴 감소
        for r in range(8):
            for c in range(8):
                p = self.board._grid[r][c]
                if p and p.color == self.current_turn:
                    if p.ability_cooldown > 0:
                        p.ability_cooldown -= 1
                    if p.is_hidden and p.hidden_turns_left > 0:
                        p.hidden_turns_left -= 1
                    if p.is_paralyzed:
                        p.paralyzed_turns -= 1
                        if p.paralyzed_turns <= 0:
                            p.is_paralyzed = False
                            p.paralyzed_turns = 0
                        if p.hidden_turns_left == 0:
                            p.is_hidden = False

    def status(self) -> str:
        if self.game_over:
            if self.winner:
                return f"Game Over — {'White' if self.winner == Color.WHITE else 'Black'} Wins!"
            return "Game Over — Stalemate"
        check = self.board.is_in_check(self.current_turn)
        turn = 'White' if self.current_turn == Color.WHITE else 'Black'
        return f"{turn}'s Turn  (Move {self.move_count + 1})" + ("  —  Check!" if check else "")


# ──────────────────────────────────────────────
# 6. 간단한 터미널 테스트
# ──────────────────────────────────────────────

def parse_pos(s: str) -> Optional[Position]:
    """'e2' 형식을 Position으로 변환"""
    s = s.strip().lower()
    if len(s) != 2 or s[0] not in "abcdefgh" or s[1] not in "12345678":
        return None
    col = "abcdefgh".index(s[0])
    row = 8 - int(s[1])
    return Position(row, col)


if __name__ == "__main__":
    game = Game()
    print("=" * 40)
    print("  Chess Abilities — 이동 규칙 엔진 테스트")
    print("  명령: 'e2 e4' 형식으로 입력, 'quit' 종료")
    print("  'moves e2' — 해당 칸 이동 가능한 위치 표시")
    print("=" * 40)

    while not game.game_over:
        game.board.print_board()
        print(game.status())
        cmd = input("  입력 > ").strip().lower()

        if cmd == "quit":
            break

        # 이동 가능 칸 조회
        if cmd.startswith("moves "):
            pos_str = cmd[6:]
            pos = parse_pos(pos_str)
            if pos:
                moves = MoveGenerator.get_legal_moves(game.board, pos)
                print(f"  {pos_str} → 이동 가능: {[str(m) for m in moves]}")
                game.board.print_board(highlights=moves)
            continue

        # 이동 실행
        parts = cmd.split()
        if len(parts) == 2:
            from_pos = parse_pos(parts[0])
            to_pos = parse_pos(parts[1])
            if from_pos and to_pos:
                result = game.move(from_pos, to_pos)
                if result["success"]:
                    info = result["info"]
                    if result["captured"]:
                        print(f"  ✓ {result['captured']} 잡음!")
                    if result["special"]:
                        print(f"  ★ {result['special']}!")
                    if info == "check":
                        print("  ⚠ 체크!")
                    elif info == "checkmate":
                        print(f"  ♛ 체크메이트! {game.status()}")
                    elif info == "stalemate":
                        print("  ═ 스테일메이트! 무승부!")
                else:
                    print(f"  ✗ 이동 불가: {result['info']}")
            else:
                print("  좌표 형식 오류. 예: e2 e4")
        else:
            print("  명령 형식 오류. 예: e2 e4")

    print("\n게임 종료.")
