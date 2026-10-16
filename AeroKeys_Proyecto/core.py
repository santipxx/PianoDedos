"""Lógica musical y reconocimiento de gestos de AeroKeys.

Este módulo no requiere webcam ni interfaz gráfica; se puede probar por separado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import acos, degrees, sqrt

NOTES = ("C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5", "D5", "E5")
KEYS = ("a", "s", "d", "f", "g", "h", "j", "k", "l", ";")
KEY_TO_NOTE = dict(zip(KEYS, NOTES))
FINGERS = ("thumb", "index", "middle", "ring", "pinky")

HAND_NOTE = {
    ("Left", "pinky"): "C4", ("Left", "ring"): "D4",
    ("Left", "middle"): "E4", ("Left", "index"): "F4",
    ("Left", "thumb"): "G4", ("Right", "thumb"): "A4",
    ("Right", "index"): "B4", ("Right", "middle"): "C5",
    ("Right", "ring"): "D5", ("Right", "pinky"): "E5",
}

# Landmarks de MediaPipe: puntos que forman el ángulo de cada articulación.
JOINTS = {
    "thumb": (2, 3, 4),
    "index": (5, 6, 8),
    "middle": (9, 10, 12),
    "ring": (13, 14, 16),
    "pinky": (17, 18, 20),
}

SKELETON = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
)

_SEMITONE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_frequency(note: str) -> float:
    """Devuelve la frecuencia en Hz (La4 = 440 Hz)."""
    name, octave = note[0], int(note[1:])
    midi = (octave + 1) * 12 + _SEMITONE[name]
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def _xy(point) -> tuple[float, float]:
    """Admite tuplas y objetos NormalizedLandmark de MediaPipe."""
    if hasattr(point, "x") and hasattr(point, "y"):
        return float(point.x), float(point.y)
    return float(point[0]), float(point[1])


def joint_angle(a, b, c) -> float:
    """Ángulo entre tres puntos 2D, con b como vértice."""
    ax, ay = _xy(a)
    bx, by = _xy(b)
    cx, cy = _xy(c)
    ab = (ax - bx, ay - by)
    cb = (cx - bx, cy - by)
    norm = sqrt(sum(x*x for x in ab) * sum(x*x for x in cb))
    if norm < 1e-10:
        return 180.0
    cosine = max(-1.0, min(1.0, (ab[0]*cb[0] + ab[1]*cb[1]) / norm))
    return degrees(acos(cosine))


def bent_fingers(points, threshold: float = 145.0) -> set[str]:
    """Determina qué dedos están flexionados mediante ángulos articulares."""
    pressed = set()
    for finger, (a, b, c) in JOINTS.items():
        # El pulgar necesita un umbral ligeramente distinto por su movilidad.
        limit = threshold + 8 if finger == "thumb" else threshold
        if joint_angle(points[a], points[b], points[c]) < limit:
            pressed.add(finger)
    return pressed


@dataclass
class GestureGate:
    """Filtro antirrebote: 2 fotogramas de confirmación por cambio."""
    frames: int = 2
    stable: set[tuple[str, str]] = field(default_factory=set)
    _counts: dict[tuple[str, str], int] = field(default_factory=dict)

    def update(self, detected: set[tuple[str, str]]) -> set[tuple[str, str]]:
        for key in HAND_NOTE:
            target = key in detected
            current = key in self.stable
            if target == current:
                self._counts[key] = 0
                continue
            self._counts[key] = self._counts.get(key, 0) + 1
            if self._counts[key] >= self.frames:
                if target:
                    self.stable.add(key)
                else:
                    self.stable.discard(key)
                self._counts[key] = 0
        return set(self.stable)


class Melody:
    """Secuencia de notas para la demostración sin cámara."""
    NAME = "Oda a la alegría"
    TUNE = (
        "E4", "E4", "F4", "G4", "G4", "F4", "E4", "D4",
        "C4", "C4", "D4", "E4", "E4", "D4", "D4", None,
        "E4", "E4", "F4", "G4", "G4", "F4", "E4", "D4",
        "C4", "C4", "D4", "E4", "D4", "C4", "C4", None,
    )

    def __init__(self, beat_seconds: float = 0.48):
        self.beat_seconds = beat_seconds

    def at(self, elapsed: float) -> tuple[str | None, float]:
        """(nota activa, progreso 0-1 de la melodía)."""
        elapsed = max(0.0, elapsed)
        phase = elapsed / self.beat_seconds
        step = int(phase) % len(self.TUNE)
        note = self.TUNE[step] if phase % 1.0 < 0.80 else None
        return note, (phase % len(self.TUNE)) / len(self.TUNE)
