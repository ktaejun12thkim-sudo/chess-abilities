# ============================================================
#  Chess Abilities — 효과음 매니저 (sound_manager.py)
#  numpy로 파형 생성, 외부 파일 불필요
# ============================================================

import pygame
import numpy as np

SAMPLE_RATE = 44100


def _make_sound(samples: np.ndarray) -> pygame.sndarray.make_sound:
    """numpy 배열 → pygame Sound"""
    samples = np.clip(samples, -1.0, 1.0)
    arr = (samples * 32767).astype(np.int16)
    # 스테레오로 변환
    stereo = np.column_stack([arr, arr])
    return pygame.sndarray.make_sound(stereo)


def _sine(freq, duration, sr=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def _envelope(samples, attack=0.01, decay=0.1, sustain=0.7, release=0.1, sr=SAMPLE_RATE):
    n = len(samples)
    env = np.ones(n)
    a = int(attack * sr)
    d = int(decay * sr)
    r = int(release * sr)
    # Attack
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    # Decay
    if d > 0 and a + d < n:
        env[a:a+d] = np.linspace(1, sustain, d)
    # Sustain
    s_end = n - r
    if a + d < s_end:
        env[a+d:s_end] = sustain
    # Release
    if r > 0:
        env[s_end:] = np.linspace(sustain, 0, n - s_end)
    return samples * env


def _make_move_sound() -> pygame.mixer.Sound:
    """기물 이동 — 짧고 부드러운 나무 클릭"""
    dur = 0.18
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)

    # 저음 클릭 + 고음 탁
    click = _sine(180, dur) * 0.5
    click += _sine(420, dur) * 0.3
    click += _sine(800, dur) * 0.15
    # 빠른 감쇠
    env = np.exp(-t * 28)
    samples = click * env * 0.6
    return _make_sound(samples)


def _make_capture_sound() -> pygame.mixer.Sound:
    """기물 잡기 — 묵직한 타격음"""
    dur = 0.28
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)

    # 낮은 임팩트 + 잡음 질감
    impact = _sine(120, dur) * 0.6
    impact += _sine(60, dur) * 0.5
    impact += _sine(300, dur) * 0.2
    noise = np.random.uniform(-0.15, 0.15, len(t))
    env = np.exp(-t * 18)
    samples = (impact + noise) * env * 0.75
    return _make_sound(samples)


def _make_check_sound() -> pygame.mixer.Sound:
    """체크메이트 — 위협적이고 웅장한 화음"""
    dur = 1.2
    # 단조 화음 (Am 느낌)
    freqs = [220, 261, 329, 440]
    samples = np.zeros(int(SAMPLE_RATE * dur))
    for i, f in enumerate(freqs):
        wave = _sine(f, dur) * 0.25
        # 각 음에 약간 딜레이
        delay = int(i * 0.04 * SAMPLE_RATE)
        wave = _envelope(wave, attack=0.05, decay=0.2, sustain=0.6, release=0.3)
        samples[delay:] += wave[:len(samples)-delay]
    samples = np.clip(samples, -1, 1) * 0.8
    return _make_sound(samples)


def _make_ability_sound() -> pygame.mixer.Sound:
    """능력 발동 — 마법 같은 상승 음계"""
    dur = 0.5
    # 빠르게 상승하는 주파수
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    freq = np.linspace(300, 900, len(t))
    wave = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)
    # 배음 추가
    freq2 = np.linspace(600, 1800, len(t))
    wave += np.sin(2 * np.pi * np.cumsum(freq2) / SAMPLE_RATE) * 0.3
    env = np.exp(-t * 4) * (1 - np.exp(-t * 30))
    samples = wave * env * 0.7
    return _make_sound(samples)


class SoundManager:
    def __init__(self, volume: int = 70):
        """
        volume: 0~100
        """
        # pygame.mixer 초기화
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            self._enabled = True
        except Exception:
            self._enabled = False
            return

        self._volume = volume / 100.0
        self._sounds = {}
        self._load_sounds()

    def _load_sounds(self):
        try:
            self._sounds = {
                "move":    _make_move_sound(),
                "capture": _make_capture_sound(),
                "checkmate": _make_check_sound(),
                "ability": _make_ability_sound(),
            }
            self._apply_volume()
        except Exception as e:
            print(f"[사운드] 로드 실패: {e}")
            self._enabled = False

    def _apply_volume(self):
        for s in self._sounds.values():
            s.set_volume(self._volume)

    def set_volume(self, volume: int):
        """volume: 0~100"""
        self._volume = max(0, min(100, volume)) / 100.0
        if self._enabled:
            self._apply_volume()

    def play(self, name: str):
        """효과음 재생. name: 'move' | 'capture' | 'checkmate' | 'ability'"""
        if not self._enabled:
            return
        sound = self._sounds.get(name)
        if sound:
            sound.play()
