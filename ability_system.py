# ============================================================
#  Chess Abilities — 특수 능력 시스템 (ability_system.py)
#  chess_engine.py, main.py 와 같은 폴더에 두세요
# ============================================================

from __future__ import annotations
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from chess_engine import Game, Position, Piece, Color, PieceType

# ──────────────────────────────────────────────
# 능력 결과 타입
# ──────────────────────────────────────────────

class AbilityResult:
    def __init__(self, success: bool, info: str = "", special: str = "", captured=None):
        self.success  = success
        self.info     = info
        self.special  = special
        self.captured = captured  # 잡은 기물 (Shadow Leap 등)


# ──────────────────────────────────────────────
# 능력 시스템 메인 클래스
# ──────────────────────────────────────────────

class AbilitySystem:
    """
    턴당 1개 기물만 능력 사용 가능.
    각 능력은 game 객체를 받아 상태를 직접 변경함.
    """

    def __init__(self, game: Game):
        self.game = game

        # 킹 칙령 — 게임당 1회, 사용 여부 추적
        self.royal_decree_used = {
            "white": False,
            "black": False,
        }

        # 킹 칙령 — 2단계 입력 상태
        # None: 미발동 / Position: 칙령 발동 후 대상 기물 선택 대기 중
        self.royal_decree_pending: Optional[object] = None   # 발동한 기물 위치
        self.royal_decree_targets: list = []                  # 이동 가능 칸 목록

        # 퀸 마비 — 마비된 (기물위치, 남은 턴) 목록
        self.paralyzed: dict = {}   # Position -> turns_left

        # 룩 봉쇄 — 봉쇄된 라인 목록
        self.blockades: list = []   # [{"color": Color, "row": int or None, "col": int or None, "turns": int}]

        # 퀸 오라 대기 상태
        self.aura_pending = None
        self.aura_targets = []
        self.leap_pending = None
        self.leap_moves = []
        self.advance_pending = None
        self.advance_moves = []
        self.advance_phase = 1

        # 폰 연속 돌격 대기 상태
        self.advance_pending = None
        self.advance_moves = []
        self.advance_phase = 1
        self.advance_phase = 1

        # 나이트 그림자 도약 대기 상태
        self.leap_pending = None
        self.leap_moves = []
        self.advance_pending = None
        self.advance_moves = []
        self.advance_phase = 1

        # 비숍 은신 — is_hidden 필드 사용 (chess_engine.py 의 Piece 필드)

    # ──────────────────────────────────────────────
    # 공통 검증
    # ──────────────────────────────────────────────

    def _can_use_ability(self, pos) -> tuple[bool, str]:
        """능력 사용 가능 여부 기본 검증"""
        from chess_engine import Position
        if self.game.ability_used_this_turn:
            return False, "Already used an ability this turn!"
        piece = self.game.board.get(pos)
        if piece is None:
            return False, "No piece at that position."
        if piece.color != self.game.current_turn:
            return False, "Not your piece."
        if piece.ability_cooldown > 0:
            return False, f"Ability on cooldown! ({piece.ability_cooldown} turns left)"
        return True, ""

    # ──────────────────────────────────────────────
    # 1. 킹 — 왕의 칙령 (Royal Decree)
    # ──────────────────────────────────────────────
    # 아군 기물 하나를 지정해 이번 턴 한 번 더 이동 (이동만, 공격 불가)
    # 킹 자신 불가 / 체크 상태 불가 / 게임당 1회

    def can_royal_decree(self, king_pos) -> tuple[bool, str]:
        from chess_engine import PieceType
        ok, msg = self._can_use_ability(king_pos)
        if not ok:
            return False, msg
        piece = self.game.board.get(king_pos)
        if piece.piece_type != PieceType.KING:
            return False, "Only the King can use Royal Decree."
        color_key = piece.color.value
        if self.royal_decree_used[color_key]:
            return False, "Royal Decree already used this game!"
        if self.game.board.is_in_check(piece.color):
            return False, "Cannot use Royal Decree while in check!"
        return True, ""

    def activate_royal_decree(self, king_pos) -> AbilityResult:
        """킹 칙령 발동 — 이후 대상 기물 선택 대기 상태로 전환"""
        ok, msg = self.can_royal_decree(king_pos)
        if not ok:
            return AbilityResult(False, msg)

        self.royal_decree_pending = king_pos
        self.royal_decree_targets = []
        return AbilityResult(True, "Royal Decree activated! Select a friendly piece to move again.", "royal_decree_select")

    def select_royal_decree_target(self, target_pos) -> AbilityResult:
        """칙령 대상 기물 선택 — 이동 가능 칸 계산"""
        from chess_engine import MoveGenerator, PieceType
        if self.royal_decree_pending is None:
            return AbilityResult(False, "Royal Decree is not active.")

        king_pos = self.royal_decree_pending
        king = self.game.board.get(king_pos)
        piece = self.game.board.get(target_pos)

        if piece is None:
            return AbilityResult(False, "No piece there.")
        if piece.color != king.color:
            return AbilityResult(False, "Must select a friendly piece.")
        if target_pos == king_pos:
            return AbilityResult(False, "Cannot target the King itself.")

        # 이동 가능 칸 계산 (공격 이동 제외 — 적 기물 있는 칸 필터)
        all_moves = MoveGenerator.get_legal_moves(self.game.board, target_pos)
        # 공격 이동 제외: 도착 칸에 적 기물이 없는 칸만
        move_only = [m for m in all_moves if self.game.board.get(m) is None]

        if not move_only:
            return AbilityResult(False, "That piece has no valid moves (movement only, no captures).")

        self.royal_decree_targets = move_only
        return AbilityResult(True, f"Select destination for the piece.", "royal_decree_move")

    def execute_royal_decree(self, piece_pos, dest_pos) -> AbilityResult:
        """칙령 이동 실행"""
        from chess_engine import PieceType
        if dest_pos not in self.royal_decree_targets:
            return AbilityResult(False, "Invalid destination for Royal Decree.")

        king_pos = self.royal_decree_pending
        king = self.game.board.get(king_pos)

        # 이동 실행 (공격 없는 순수 이동)
        piece = self.game.board.get(piece_pos)
        self.game.board._move_piece(piece_pos, dest_pos)

        # 상태 업데이트
        color_key = king.color.value
        self.royal_decree_used[color_key] = True
        self.game.ability_used_this_turn = True
        king.ability_cooldown = 999   # 사실상 재사용 불가 표시

        # 칙령 상태 초기화
        self.royal_decree_pending = None
        self.royal_decree_targets = []

        return AbilityResult(True, "Royal Decree executed!", "royal_decree_done")

    def cancel_royal_decree(self):
        """칙령 취소"""
        self.royal_decree_pending = None
        self.royal_decree_targets = []

    # ──────────────────────────────────────────────
    # 2. 퀸 — 지배의 오라 (Domination Aura)
    # ──────────────────────────────────────────────
    # 퀸 이동 범위 내 적 기물 1개를 1턴 마비
    # 마비된 기물은 해당 턴에 이동 불가 / 쿨다운 5턴

    def can_domination_aura(self, queen_pos) -> tuple[bool, str]:
        from chess_engine import PieceType
        ok, msg = self._can_use_ability(queen_pos)
        if not ok:
            return False, msg
        piece = self.game.board.get(queen_pos)
        if piece.piece_type != PieceType.QUEEN:
            return False, "Only the Queen can use Domination Aura."
        targets = self.get_aura_targets(queen_pos)
        if not targets:
            return False, "No enemy pieces in Queen's range!"
        return True, ""

    def get_aura_targets(self, queen_pos) -> list:
        """보드 전체 적 기물 위치 목록 반환 (킹 제외)"""
        from chess_engine import Position, PieceType
        piece = self.game.board.get(queen_pos)
        if piece is None:
            return []
        targets = []
        for r in range(8):
            for c in range(8):
                pos = Position(r, c)
                target = self.game.board.get(pos)
                if (target and target.color != piece.color
                        and target.piece_type != PieceType.KING):
                    targets.append(pos)
        return targets

    def activate_domination_aura(self, queen_pos) -> AbilityResult:
        """지배의 오라 발동 — 대상 선택 대기 상태로 전환"""
        ok, msg = self.can_domination_aura(queen_pos)
        if not ok:
            return AbilityResult(False, msg)
        self.aura_pending = queen_pos
        self.aura_targets = self.get_aura_targets(queen_pos)
        return AbilityResult(True, "Domination Aura! Select an enemy piece to paralyze.", "aura_select")

    def execute_domination_aura(self, target_pos) -> AbilityResult:
        """마비 실행"""
        from chess_engine import PieceType
        if not hasattr(self, 'aura_pending') or self.aura_pending is None:
            return AbilityResult(False, "Domination Aura is not active.")
        if target_pos not in self.aura_targets:
            return AbilityResult(False, "Target not in range!")
        # 킹은 절대 마비 불가
        target_piece = self.game.board.get(target_pos)
        if target_piece and target_piece.piece_type == PieceType.KING:
            return AbilityResult(False, "Cannot paralyze the King!")

        queen_pos = self.aura_pending
        queen = self.game.board.get(queen_pos)

        # 마비 적용 — 기물 자체에 저장
        target_piece = self.game.board.get(target_pos)
        if target_piece:
            target_piece.is_paralyzed = True
            target_piece.paralyzed_turns = 2

        # 쿨다운 & 능력 사용 처리
        queen.ability_cooldown = 5
        self.game.ability_used_this_turn = True

        # 상태 초기화
        self.aura_pending = None
        self.aura_targets = []
        self.leap_pending = None
        self.leap_moves = []
        self.advance_pending = None
        self.advance_moves = []
        self.advance_phase = 1

        return AbilityResult(True, "Domination Aura! Enemy piece paralyzed for 1 turn.", "aura_done")

    def cancel_domination_aura(self):
        self.aura_pending = None
        self.aura_targets = []
        self.leap_pending = None
        self.leap_moves = []
        self.advance_pending = None
        self.advance_moves = []
        self.advance_phase = 1

    # ──────────────────────────────────────────────
    # 3. 룩 — 철옹성 (Iron Fortress)
    # ──────────────────────────────────────────────
    # 룩이 있는 파일(열)로 외부에서 적 기물 진입 금지
    # 해당 파일 안에 있던 기물은 이동 가능
    # 지속 3턴 / 쿨다운 4턴

    def can_iron_fortress(self, rook_pos) -> tuple[bool, str]:
        from chess_engine import PieceType
        ok, msg = self._can_use_ability(rook_pos)
        if not ok:
            return False, msg
        piece = self.game.board.get(rook_pos)
        if piece.piece_type != PieceType.ROOK:
            return False, "Only the Rook can use Iron Fortress."
        return True, ""

    def activate_iron_fortress(self, rook_pos) -> AbilityResult:
        """철옹성 발동 — 룩의 파일(열)로 외부 진입 봉쇄"""
        ok, msg = self.can_iron_fortress(rook_pos)
        if not ok:
            return AbilityResult(False, msg)

        rook = self.game.board.get(rook_pos)

        # 기존 같은 색 봉쇄 제거
        self.blockades = [b for b in self.blockades if b["color"] != rook.color]

        # 봉쇄된 파일의 기물 초기 위치 기록 (이 파일 안에 있던 기물은 이동 허용)
        from chess_engine import Position
        pieces_in_file = set()
        for r in range(8):
            p = self.game.board.get(Position(r, rook_pos.col))
            if p is not None:
                pieces_in_file.add((r, rook_pos.col))

        # 열 봉쇄 (파일만)
        self.blockades.append({
            "color": rook.color,
            "col": rook_pos.col,
            "turns": 3,
            "pieces_in_file": pieces_in_file  # 원래 파일 안 기물 위치
        })

        rook.ability_cooldown = 4
        self.game.ability_used_this_turn = True

        col_letter = "abcdefgh"[rook_pos.col]
        return AbilityResult(True, f"Iron Fortress! File {col_letter} blockaded for 3 turns.", "fortress_done")

    def is_blockaded(self, from_pos, to_pos, moving_color) -> bool:
        """외부에서 봉쇄된 파일로 진입 시도 시 True"""
        for b in self.blockades:
            if b["color"] == moving_color:
                continue  # 자기편 봉쇄는 자기 기물에 적용 안 됨
            col = b.get("col")
            if col is not None and to_pos.col == col:
                # 목적지가 봉쇄된 파일
                # 출발지가 같은 파일이면 허용 (파일 안에 있던 기물)
                if from_pos.col == col:
                    return False
                return True  # 외부에서 진입 시도 → 봉쇄
        return False

    def get_blockaded_lines(self) -> list:
        """현재 봉쇄된 열 정보 반환 (시각화용)"""
        return self.blockades

    # ──────────────────────────────────────────────
    # 4. 나이트 — 천둥의 돌진 (Thunder Charge)
    # ──────────────────────────────────────────────
    # 같은 파일의 가장 가까운 기물 앞까지 돌진
    # 해당 기물을 뒤로 1칸 밀어냄
    # 밀려날 공간 없으면 1턴 마비
    # 쿨다운 4턴

    def can_shadow_leap(self, knight_pos) -> tuple[bool, str]:
        from chess_engine import PieceType
        ok, msg = self._can_use_ability(knight_pos)
        if not ok:
            return False, msg
        piece = self.game.board.get(knight_pos)
        if piece.piece_type != PieceType.KNIGHT:
            return False, "Only the Knight can use Thunder Charge."
        # 같은 파일에 기물이 있어야 함
        targets = self._get_thunder_target(knight_pos)
        if targets is None:
            return False, "No pieces in this file to charge at!"
        return True, ""

    def _get_thunder_target(self, knight_pos):
        """파일에서 가장 가까운 기물과 방향 반환 (target_pos, direction) or None"""
        from chess_engine import Position
        col = knight_pos.col
        row = knight_pos.row

        # 위쪽 탐색
        for r in range(row - 1, -1, -1):
            p = self.game.board.get(Position(r, col))
            if p is not None:
                return Position(r, col), -1  # 위 방향

        # 아래쪽 탐색
        for r in range(row + 1, 8):
            p = self.game.board.get(Position(r, col))
            if p is not None:
                return Position(r, col), 1  # 아래 방향

        return None

    def get_shadow_leap_moves(self, knight_pos) -> list:
        """천둥 돌진 — 돌진할 칸 반환 (시각화용)"""
        from chess_engine import Position
        result = self._get_thunder_target(knight_pos)
        if result is None:
            return []
        target_pos, direction = result
        # 나이트가 도달하는 칸 = 타겟 바로 앞
        dest_row = target_pos.row - direction
        if dest_row == knight_pos.row:
            return []  # 이미 붙어있으면 돌진 불가
        return [Position(dest_row, knight_pos.col)]

    def activate_shadow_leap(self, knight_pos) -> AbilityResult:
        """천둥 돌진 발동"""
        ok, msg = self.can_shadow_leap(knight_pos)
        if not ok:
            return AbilityResult(False, msg)

        from chess_engine import Position
        result = self._get_thunder_target(knight_pos)
        if result is None:
            return AbilityResult(False, "No target!")

        target_pos, direction = result
        dest_row = target_pos.row - direction

        if dest_row == knight_pos.row:
            return AbilityResult(False, "Already adjacent to target!")

        dest_pos = Position(dest_row, knight_pos.col)

        # 나이트 이동
        knight = self.game.board.get(knight_pos)
        self.game.board._move_piece(knight_pos, dest_pos)
        knight.has_moved = True
        # 능력 사용 후 이번 턴 이동 불가 (턴 종료)
        knight.ability_cooldown = 4
        self.game.ability_used_this_turn = True

        # ── 연쇄 밀어내기 ──
        # 타겟부터 방향으로 연속된 기물들을 모두 수집
        chain = []
        cur = target_pos
        while cur.is_valid():
            p = self.game.board.get(cur)
            if p is None:
                break
            chain.append(cur)
            cur = Position(cur.row + direction, cur.col)

        if not chain:
            return AbilityResult(True, "Thunder Charge! No chain to push.", "leap_done")

        stunned_count = 0
        pushed_count = 0

        # 뒤에서부터 처리 (연쇄 밀기)
        for pos in reversed(chain):
            p = self.game.board.get(pos)
            if p is None:
                continue
            push_to = Position(pos.row + direction, pos.col)
            if not push_to.is_valid():
                # 보드 밖 → 기절 (제자리 유지)
                p.stunned = True
                stunned_count += 1
            else:
                # 밀어내기
                self.game.board._move_piece(pos, push_to)
                pushed_count += 1

        parts = []
        if pushed_count:
            parts.append(f"{pushed_count} pushed")
        if stunned_count:
            parts.append(f"{stunned_count} stunned")
        msg = "Thunder Charge! " + ", ".join(parts) + "!"

        self.leap_pending = knight_pos
        self.leap_moves = [dest_pos]

        return AbilityResult(True, msg, "leap_done", captured=None)

    def execute_shadow_leap(self, dest_pos) -> AbilityResult:
        """천둥 돌진은 activate에서 즉시 실행되므로 여기선 결과만 반환"""
        self.leap_pending = None
        self.leap_moves = []
        return AbilityResult(True, "Thunder Charge complete!", "leap_done")

    def cancel_shadow_leap(self):
        self.leap_pending = None
        self.leap_moves = []

    # ──────────────────────────────────────────────
    # 5. 비숍 — 어둠 속으로 (Into the Shadows)
    # ──────────────────────────────────────────────
    # 비숍이 5턴 동안 은신 — 적이 그 칸을 공격 대상으로 인식 불가
    # 은신 중 비숍은 이동 시 적에게 위치가 숨겨짐
    # 공격하는 순간 은신 해제 / 쿨다운 6턴

    def can_into_shadows(self, bishop_pos) -> tuple[bool, str]:
        from chess_engine import PieceType
        ok, msg = self._can_use_ability(bishop_pos)
        if not ok:
            return False, msg
        piece = self.game.board.get(bishop_pos)
        if piece.piece_type != PieceType.BISHOP:
            return False, "Only the Bishop can use Into the Shadows."
        if piece.is_hidden:
            return False, "Bishop is already hidden!"
        return True, ""

    def activate_into_shadows(self, bishop_pos) -> AbilityResult:
        """은신 발동 — 비숍을 5턴 동안 숨김"""
        ok, msg = self.can_into_shadows(bishop_pos)
        if not ok:
            return AbilityResult(False, msg)

        bishop = self.game.board.get(bishop_pos)
        bishop.is_hidden = True
        bishop.hidden_turns_left = 5
        bishop.ability_cooldown = 6
        self.game.ability_used_this_turn = True

        return AbilityResult(True, "Into the Shadows! Bishop position hidden from enemy for 5 turns!", "shadows_done")

    def get_hidden_bishops(self, color) -> list:
        """현재 은신 중인 비숍 위치 목록"""
        from chess_engine import Position, PieceType
        hidden = []
        for r in range(8):
            for c in range(8):
                pos = Position(r, c)
                p = self.game.board.get(pos)
                if p and p.piece_type == PieceType.BISHOP and p.color == color and p.is_hidden:
                    hidden.append(pos)
        return hidden

    # ──────────────────────────────────────────────
    # 6. 폰 — 지뢰 (Land Mine)
    # ──────────────────────────────────────────────
    # 폰이 현재 자리에 지뢰를 설치. 적이 밟으면 소멸. 쿨다운 3턴

    def can_double_advance(self, pawn_pos) -> tuple[bool, str]:
        from chess_engine import PieceType
        ok, msg = self._can_use_ability(pawn_pos)
        if not ok:
            return False, msg
        piece = self.game.board.get(pawn_pos)
        if piece.piece_type != PieceType.PAWN:
            return False, "Only a Pawn can use Land Mine."
        return True, ""

    def get_double_advance_moves(self, pawn_pos) -> list:
        return []  # 지뢰는 이동 선택 불필요

    def activate_double_advance(self, pawn_pos) -> AbilityResult:
        """지뢰 설치 — 현재 칸에 즉시 설치"""
        ok, msg = self.can_double_advance(pawn_pos)
        if not ok:
            return AbilityResult(False, msg)

        # 지뢰 설치
        if not hasattr(self, 'mines'):
            self.mines = []
        piece = self.game.board.get(pawn_pos)
        self.mines.append({"pos": pawn_pos, "color": piece.color})
        piece.ability_cooldown = 3
        self.game.ability_used_this_turn = True

        return AbilityResult(True, "Land Mine placed! Enemy beware.", "mine_placed")

    def execute_double_advance(self, dest_pos) -> AbilityResult:
        return AbilityResult(False, "Land Mine has no target selection.")

    def cancel_double_advance(self):
        pass

    def check_mines(self, pos, moving_color):
        """이동한 칸에 지뢰가 있으면 기물 소멸"""
        if not hasattr(self, 'mines'):
            self.mines = []
        for mine in list(self.mines):
            if mine["pos"] == pos and mine["color"] != moving_color:
                # 지뢰 발동 — 해당 칸 기물 제거
                self.game.board.set(pos, None)
                self.mines.remove(mine)
                return True
        return False

    def on_turn_end(self):
        """턴이 끝날 때 호출 — 쿨다운/지속 효과 감소"""
        from chess_engine import Color, Position, PieceType

        # 봉쇄 턴 감소
        self.blockades = [b for b in self.blockades if b["turns"] > 1]
        for b in self.blockades:
            b["turns"] -= 1

        # 기절 해제
        from chess_engine import Position
        for r in range(8):
            for c in range(8):
                p = self.game.board.get(Position(r, c))
                if p and getattr(p, "stunned", False):
                    p.stunned = False

        # 은신 턴 감소
        for r in range(8):
            for c in range(8):
                pos = Position(r, c)
                p = self.game.board.get(pos)
                if p and p.piece_type == PieceType.BISHOP and p.is_hidden:
                    p.hidden_turns_left -= 1
                    if p.hidden_turns_left <= 0:
                        p.is_hidden = False
                        p.hidden_turns_left = 0

    def is_paralyzed(self, pos) -> bool:
        piece = self.game.board.get(pos)
        return piece is not None and piece.is_paralyzed

    def get_blockaded_squares(self, color) -> list:
        """해당 색 기준으로 봉쇄된 칸 목록 반환"""
        squares = []
        for b in self.blockades:
            if b["color"] != color:  # 상대방 봉쇄에 걸린 칸
                for r in range(8):
                    for c in range(8):
                        from chess_engine import Position
                        if (b.get("row") is not None and r == b["row"]) or \
                           (b.get("col") is not None and c == b["col"]):
                            squares.append(Position(r, c))
        return squares

    def reset(self):
        """게임 재시작 시 초기화"""
        self.royal_decree_used = {"white": False, "black": False}
        self.royal_decree_pending = None
        self.royal_decree_targets = []
        self.paralyzed = {}
        self.blockades = []
        self.aura_pending = None
        self.aura_targets = []
        self.leap_pending = None
        self.leap_moves = []
        self.advance_pending = None
        self.advance_moves = []
        self.advance_phase = 1
