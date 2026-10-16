"""Juego de ritmo Jingle Bells: partitura y puntuación independientes de Pygame.

El cursor ``t`` es el tiempo desde que se debería pulsar la primera nota.
El programa inicia con un tiempo negativo para que las fichas alcancen a caer.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core import NOTES

# Notas de la melodía principal en Do mayor. Duraciones en pulsos (beats).
# None representa un silencio breve entre frases. Melodía arreglada para
# reconocimiento de gestos, manteniendo el motivo clásico reconocible.
JINGLE_BELLS_BEATS: tuple[tuple[str | None, float], ...] = (
    ("E4", 1), ("E4", 1), ("E4", 2), (None, 0.5),
    ("E4", 1), ("E4", 1), ("E4", 2), (None, 0.5),
    ("E4", 1), ("G4", 1), ("C4", 1), ("D4", 1), ("E4", 3), (None, 0.5),
    ("F4", 1), ("F4", 1), ("F4", 1), ("F4", 1),
    ("F4", 1), ("E4", 1), ("E4", 1), ("E4", 1),
    ("E4", 1), ("D4", 1), ("D4", 1), ("E4", 1), ("D4", 2), ("G4", 3),
    (None, 1.0),
    ("E4", 1), ("E4", 1), ("E4", 2), (None, 0.5),
    ("E4", 1), ("E4", 1), ("E4", 2), (None, 0.5),
    ("E4", 1), ("G4", 1), ("C4", 1), ("D4", 1), ("E4", 3), (None, 0.5),
    ("F4", 1), ("F4", 1), ("F4", 1), ("F4", 1),
    ("F4", 1), ("E4", 1), ("E4", 1), ("E4", 1),
    ("G4", 1), ("G4", 1), ("F4", 1), ("D4", 1), ("C4", 3),
)


@dataclass(frozen=True)
class MusicTile:
    note: str
    at: float                 # Momento en segundos en que toca la línea
    duration: float           # Duración musical del bloque


def jingle_bells(bpm: int = 105) -> tuple[MusicTile, ...]:
    if bpm < 40 or bpm > 200:
        raise ValueError("BPM fuera del rango 40-200")
    beat = 60.0 / bpm
    elapsed = 0.0
    tiles: list[MusicTile] = []
    for note, length in JINGLE_BELLS_BEATS:
        if note is not None:
            if note not in NOTES:
                raise ValueError(f"Nota no soportada: {note}")
            tiles.append(MusicTile(note, elapsed, length * beat))
        elapsed += length * beat
    return tuple(tiles)


@dataclass
class RhythmGame:
    """Procesa pulsaciones y detecta notas acertadas/perdidas sin usar webcam."""
    tiles: tuple[MusicTile, ...] = field(default_factory=jingle_bells)
    score: int = 0
    combo: int = 0
    best_combo: int = 0
    hits: int = 0
    misses: int = 0
    results: dict[int, str] = field(default_factory=dict)
    last_result: str = ""
    last_result_at: float = -99.0
    window: float = 0.31

    @property
    def total(self) -> int:
        return len(self.tiles)

    @property
    def end_time(self) -> float:
        last = self.tiles[-1]
        return last.at + last.duration + 0.8

    def finished(self, t: float) -> bool:
        return t >= self.end_time and len(self.results) == self.total

    def accuracy(self) -> float:
        return (100.0 * self.hits / self.total) if self.total else 0.0

    def press(self, note: str, t: float) -> str | None:
        """Asigna la pulsación a la nota pendiente más cercana dentro de ventana."""
        candidates = (
            (abs(tile.at - t), index)
            for index, tile in enumerate(self.tiles)
            if tile.note == note and index not in self.results
            and abs(tile.at - t) <= self.window
        )
        nearest = min(candidates, default=None)
        if nearest is None:
            return None
        error, index = nearest
        judgement = "PERFECT" if error <= 0.10 else "GOOD" if error <= 0.20 else "OK"
        self.results[index] = judgement
        self.hits += 1
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)
        self.score += {"PERFECT": 100, "GOOD": 70, "OK": 40}[judgement]
        self.last_result = judgement
        self.last_result_at = t
        return judgement

    def update(self, t: float) -> None:
        """Marca como falladas las notas cuyo tiempo ya venció."""
        for index, tile in enumerate(self.tiles):
            if index not in self.results and t > tile.at + self.window:
                self.results[index] = "MISS"
                self.misses += 1
                self.combo = 0
                self.last_result = "MISS"
                self.last_result_at = t
