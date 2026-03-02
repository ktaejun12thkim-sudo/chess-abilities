# ============================================================
#  Chess Abilities — 언어 팩 (localization.py)
#  한국어 / English
# ============================================================

STRINGS = {
    "en": {
        # 시작 화면
        "title":            "Chess Abilities",
        "subtitle":         "— A Game of Power & Strategy —",
        "btn_play":         "▶  PLAY",
        "btn_abilities":    "📖  ABILITIES",
        "btn_settings":     "⚙  SETTINGS",
        "btn_quit":         "✕  QUIT",
        "btn_back":         "← Back",

        # 모드 선택
        "select_mode":      "Select Mode",
        "select_mode_sub":  "Choose how you want to play",
        "mode_2p":          "⚔  2 Players",
        "mode_2p_desc":     "Local multiplayer",
        "mode_easy":        "★  Easy AI",
        "mode_easy_desc":   "Random moves",
        "mode_medium":      "★★  Medium AI",
        "mode_medium_desc": "Minimax 3-ply",
        "mode_hard":        "★★★  Hard AI",
        "mode_hard_desc":   "Alpha-Beta 5-ply",

        # 능력 설명 페이지
        "abilities_title":  "Abilities",
        "abilities_sub":    "Each piece has a unique power. Press the key to activate.",

        # 설정
        "settings_title":   "Settings",
        "volume":           "Volume",
        "fullscreen":       "Fullscreen",
        "fullscreen_on":    "ON  [F11]",
        "fullscreen_off":   "OFF  [F11]",
        "resolution":       "Resolution",
        "language":         "Language",

        # 인게임 패널
        "panel_title":      "Chess Abilities",
        "white_turn":       "● White's Turn",
        "black_turn":       "● Black's Turn",
        "move_count":       "Move",
        "captured":         "Captured",
        "btn_resign":       "Resign",
        "btn_offer_draw":   "Offer Draw",
        "btn_draw_offered": "Draw Offered...",
        "ai_label":         "AI",

        # 키 안내
        "key_royal":        "Royal Decree",
        "key_aura":         "Dom. Aura",
        "key_fortress":     "Iron Fortress",
        "key_leap":         "Thunder Charge",
        "key_shadows":      "Into Shadows",
        "key_advance":      "Land Mine",
        "key_restart":      "Restart",

        # 능력 이름
        "ability_royal":    "Royal Decree",
        "ability_aura":     "Domination Aura",
        "ability_fortress": "Iron Fortress",
        "ability_leap":     "Thunder Charge",
        "ability_shadows":  "Into the Shadows",
        "ability_advance":  "Land Mine",

        # 상태 메시지
        "msg_check":        "Check!",
        "msg_checkmate":    "Checkmate!",
        "msg_stalemate":    "Stalemate!",
        "msg_promotion":    "Choose a piece to promote!",
        "msg_castling":     "Castling!",
        "msg_en_passant":   "En Passant!",
        "msg_resign":       "Resigned.",
        "msg_draw_offer":   "Draw offered! Waiting for opponent...",
        "msg_draw_decline": "Draw offer declined.",
        "msg_paralyzed":    "This piece is paralyzed!",
        "msg_ai_promoted":  "AI promoted to Queen!",

        # 게임 오버
        "white_wins":       "White Wins!",
        "black_wins":       "Black Wins!",
        "draw":             "Draw",
        "checkmate":        "Checkmate",
        "stalemate":        "Stalemate",
        "resigned":         "Resigned",
        "by_agreement":     "By Agreement",
        "btn_play_again":   "▶  Play Again",
        "btn_main_menu":    "⌂  Main Menu",

        # 무승부 제안 팝업
        "draw_offer_title": "Draw Offer",
        "draw_offer_white": "White offers a draw. Accept?",
        "draw_offer_black": "Black offers a draw. Accept?",
        "btn_accept":       "✓  Accept",
        "btn_decline":      "✕  Decline",

        # 승진
        "promotion_title":  "Promotion!",

        # 능력 설명
        "desc_royal":       "Move a friendly piece again.\nOne use per game.",
        "desc_aura":        "Paralyze any enemy piece\nfor 1 turn. CD: 5",
        "desc_fortress":    "Blockade your Rook's row\nand column for 2 turns. CD: 4",
        "desc_leap":        "Teleport to any empty square\non the board. CD: 4",
        "desc_shadows":     "Hide your Bishop's position\nfrom the enemy. CD: 6",
        "desc_advance":     "Place a mine on your square.\nEnemy who steps on it dies. CD: 3",
    },

    "ko": {
        # 시작 화면
        "title":            "체스 어빌리티",
        "subtitle":         "— 전략과 능력의 대결 —",
        "btn_play":         "▶  플레이",
        "btn_abilities":    "📖  능력 설명",
        "btn_settings":     "⚙  설정",
        "btn_quit":         "✕  종료",
        "btn_back":         "← 뒤로",

        # 모드 선택
        "select_mode":      "모드 선택",
        "select_mode_sub":  "게임 방식을 선택하세요",
        "mode_2p":          "⚔  2인 대전",
        "mode_2p_desc":     "로컬 멀티플레이어",
        "mode_easy":        "★  쉬움 AI",
        "mode_easy_desc":   "랜덤 이동",
        "mode_medium":      "★★  보통 AI",
        "mode_medium_desc": "3수 앞 계산",
        "mode_hard":        "★★★  어려움 AI",
        "mode_hard_desc":   "5수 앞 알파베타",

        # 능력 설명 페이지
        "abilities_title":  "능력 목록",
        "abilities_sub":    "각 기물은 고유한 능력을 가집니다. 키를 눌러 발동하세요.",

        # 설정
        "settings_title":   "설정",
        "volume":           "음량",
        "fullscreen":       "전체화면",
        "fullscreen_on":    "켜짐  [F11]",
        "fullscreen_off":   "꺼짐  [F11]",
        "resolution":       "해상도",
        "language":         "언어",

        # 인게임 패널
        "panel_title":      "체스 어빌리티",
        "white_turn":       "● 백의 차례",
        "black_turn":       "● 흑의 차례",
        "move_count":       "수",
        "captured":         "잡은 기물",
        "btn_resign":       "기권",
        "btn_offer_draw":   "무승부 제안",
        "btn_draw_offered": "제안 중...",
        "ai_label":         "AI",

        # 키 안내
        "key_royal":        "왕의 칙령",
        "key_aura":         "지배의 오라",
        "key_fortress":     "철옹성",
        "key_leap":         "천둥의 돌진",
        "key_shadows":      "어둠 속으로",
        "key_advance":      "지뢰",
        "key_restart":      "재시작",

        # 능력 이름
        "ability_royal":    "왕의 칙령",
        "ability_aura":     "지배의 오라",
        "ability_fortress": "철옹성",
        "ability_leap":     "천둥의 돌진",
        "ability_shadows":  "어둠 속으로",
        "ability_advance":  "지뢰",

        # 상태 메시지
        "msg_check":        "체크!",
        "msg_checkmate":    "체크메이트!",
        "msg_stalemate":    "스테일메이트!",
        "msg_promotion":    "승진할 기물을 선택하세요!",
        "msg_castling":     "캐슬링!",
        "msg_en_passant":   "앙파상!",
        "msg_resign":       "기권했습니다.",
        "msg_draw_offer":   "무승부를 제안했습니다...",
        "msg_draw_decline": "무승부 제안이 거절되었습니다.",
        "msg_paralyzed":    "이 기물은 마비 상태입니다!",
        "msg_ai_promoted":  "AI가 퀸으로 승진했습니다!",

        # 게임 오버
        "white_wins":       "백 승리!",
        "black_wins":       "흑 승리!",
        "draw":             "무승부",
        "checkmate":        "체크메이트",
        "stalemate":        "스테일메이트",
        "resigned":         "기권",
        "by_agreement":     "합의 무승부",
        "btn_play_again":   "▶  다시 하기",
        "btn_main_menu":    "⌂  메인 메뉴",

        # 무승부 제안 팝업
        "draw_offer_title": "무승부 제안",
        "draw_offer_white": "백이 무승부를 제안했습니다. 수락하시겠습니까?",
        "draw_offer_black": "흑이 무승부를 제안했습니다. 수락하시겠습니까?",
        "btn_accept":       "✓  수락",
        "btn_decline":      "✕  거절",

        # 승진
        "promotion_title":  "승진!",

        # 능력 설명
        "desc_royal":       "아군 기물을 한 번 더 이동.\n게임당 1회 사용.",
        "desc_aura":        "적 기물 1개를 1턴 마비.\n쿨다운: 5",
        "desc_fortress":    "룩의 행과 열을 2턴 봉쇄.\n쿨다운: 4",
        "desc_leap":        "적을 잡고 주변 적을 스턴.\n쿨다운: 3",
        "desc_shadows":     "비숍 위치를 5턴 은신.\n쿨다운: 6",
        "desc_advance":     "현재 칸에 지뢰 설치.\n밟는 적 기물 소멸. 쿨다운: 3",
    }
}


class Locale:
    def __init__(self, lang: str = "en"):
        self.lang = lang if lang in STRINGS else "en"

    def t(self, key: str) -> str:
        return STRINGS[self.lang].get(key, STRINGS["en"].get(key, key))

    def set_lang(self, lang: str):
        self.lang = lang if lang in STRINGS else "en"


# 전역 로케일 인스턴스
locale = Locale("en")
