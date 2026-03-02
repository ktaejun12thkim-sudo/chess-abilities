# ============================================================
#  Chess Abilities — AI 엔진 (ai_engine.py)
#  Easy: 랜덤 / Medium: Minimax 3수 / Hard: Alpha-Beta 5수
# ============================================================

import random
from chess_engine import Game, Board, Position, MoveGenerator, PieceType, Color, Piece

# ── 기물 가치 ──
PIECE_VALUE = {
    PieceType.PAWN:   100,
    PieceType.KNIGHT: 320,
    PieceType.BISHOP: 330,
    PieceType.ROOK:   500,
    PieceType.QUEEN:  900,
    PieceType.KING:   20000,
}

# ── 포지션 테이블 (백 기준, 흑은 뒤집어서 사용) ──
PAWN_TABLE = [
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [ 5,  5, 10, 25, 25, 10,  5,  5],
    [ 0,  0,  0, 20, 20,  0,  0,  0],
    [ 5, -5,-10,  0,  0,-10, -5,  5],
    [ 5, 10, 10,-20,-20, 10, 10,  5],
    [ 0,  0,  0,  0,  0,  0,  0,  0],
]
KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50],
]
BISHOP_TABLE = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20],
]
ROOK_TABLE = [
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [ 5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [ 0,  0,  0,  5,  5,  0,  0,  0],
]
QUEEN_TABLE = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [ -5,  0,  5,  5,  5,  5,  0, -5],
    [  0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20],
]
KING_MID_TABLE = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [ 20, 20,  0,  0,  0,  0, 20, 20],
    [ 20, 30, 10,  0,  0, 10, 30, 20],
]

POSITION_TABLES = {
    PieceType.PAWN:   PAWN_TABLE,
    PieceType.KNIGHT: KNIGHT_TABLE,
    PieceType.BISHOP: BISHOP_TABLE,
    PieceType.ROOK:   ROOK_TABLE,
    PieceType.QUEEN:  QUEEN_TABLE,
    PieceType.KING:   KING_MID_TABLE,
}


def _get_pos_score(piece: Piece, pos: Position) -> int:
    table = POSITION_TABLES.get(piece.piece_type)
    if table is None:
        return 0
    r = pos.row if piece.color == Color.BLACK else (7 - pos.row)
    return table[r][pos.col]


def _evaluate(board: Board, color: Color) -> int:
    """보드 평가 함수 — color 기준 점수"""
    score = 0
    for r in range(8):
        for c in range(8):
            pos = Position(r, c)
            piece = board.get(pos)
            if piece is None:
                continue
            val = PIECE_VALUE.get(piece.piece_type, 0) + _get_pos_score(piece, pos)
            if piece.color == color:
                score += val
            else:
                score -= val
    return score


def _get_all_moves(board: Board, color: Color, ability_system=None) -> list:
    """color 의 모든 합법 이동 [(from, to), ...] 반환"""
    moves = []
    for r in range(8):
        for c in range(8):
            pos = Position(r, c)
            piece = board.get(pos)
            if piece and piece.color == color:
                for target in MoveGenerator.get_legal_moves(board, pos, ability_system):
                    moves.append((pos, target))
    return moves


def _order_moves(board: Board, moves: list) -> list:
    """MVV-LVA 정렬 — 잡기 이동 우선"""
    def priority(m):
        _, to = m
        target = board.get(to)
        if target:
            return -PIECE_VALUE.get(target.piece_type, 0)
        return 0
    return sorted(moves, key=priority)


# ──────────────────────────────────────────────
# Alpha-Beta Minimax
# ──────────────────────────────────────────────

def _minimax(board: Board, depth: int, alpha: int, beta: int,
             maximizing: bool, ai_color: Color, ability_system=None) -> int:
    color = ai_color if maximizing else ai_color.opponent()

    if depth == 0:
        return _evaluate(board, ai_color)

    moves = _get_all_moves(board, color, ability_system)
    if not moves:
        if board.is_in_check(color):
            return -99999 if maximizing else 99999
        return 0  # 스테일메이트

    moves = _order_moves(board, moves)

    if maximizing:
        best = -99999
        for from_pos, to_pos in moves:
            test = board.clone()
            test._move_piece(from_pos, to_pos)
            # 승진 자동 퀸
            p = test.get(to_pos)
            if p and p.piece_type == PieceType.PAWN:
                if to_pos.row == 0 or to_pos.row == 7:
                    p.piece_type = PieceType.QUEEN
            val = _minimax(test, depth - 1, alpha, beta, False, ai_color, ability_system)
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = 99999
        for from_pos, to_pos in moves:
            test = board.clone()
            test._move_piece(from_pos, to_pos)
            p = test.get(to_pos)
            if p and p.piece_type == PieceType.PAWN:
                if to_pos.row == 0 or to_pos.row == 7:
                    p.piece_type = PieceType.QUEEN
            val = _minimax(test, depth - 1, alpha, beta, True, ai_color, ability_system)
            best = min(best, val)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best


# ──────────────────────────────────────────────
# AI 클래스
# ──────────────────────────────────────────────

class ChessAI:
    """
    difficulty: 'easy' | 'medium' | 'hard'
    color: AI가 담당하는 색
    """
    DEPTH = {
        'easy':   0,   # 랜덤
        'medium': 3,
        'hard':   5,
    }

    def __init__(self, color: Color, difficulty: str = 'medium'):
        self.color = color
        self.difficulty = difficulty
        self.depth = self.DEPTH.get(difficulty, 3)

    def get_move(self, game: Game) -> tuple[Position, Position] | None:
        """최선의 이동 반환. 이동 없으면 None."""
        ability_system = game.ability_system
        moves = _get_all_moves(game.board, self.color, ability_system)
        if not moves:
            return None

        if self.difficulty == 'easy':
            return random.choice(moves)

        moves = _order_moves(game.board, moves)
        best_move = None
        best_val = -99999

        for from_pos, to_pos in moves:
            test = game.board.clone()
            test._move_piece(from_pos, to_pos)
            p = test.get(to_pos)
            if p and p.piece_type == PieceType.PAWN:
                if to_pos.row == 0 or to_pos.row == 7:
                    p.piece_type = PieceType.QUEEN
            val = _minimax(test, self.depth - 1, -99999, 99999,
                           False, self.color, ability_system)
            # 같은 점수면 랜덤 선택 (다양성)
            if val > best_val or (val == best_val and random.random() < 0.3):
                best_val = val
                best_move = (from_pos, to_pos)

        return best_move
