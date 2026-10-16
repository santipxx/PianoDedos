"""AeroKeys: piano visual controlado con gestos de ambas manos.

Ejemplos:
    python aerokeys.py --demo
    python aerokeys.py --no-camera
    python aerokeys.py
"""

from __future__ import annotations

import argparse
import math
import time
import urllib.request
from functools import lru_cache
from pathlib import Path

import numpy as np
import pygame

from core import (
    HAND_NOTE, KEY_TO_NOTE, KEYS, NOTES, SKELETON,
    GestureGate, bent_fingers, note_frequency,
)
from rhythm import RhythmGame, jingle_bells

ROOT = Path(__file__).resolve().parent
MODEL_FILE = ROOT / "assets" / "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
WIDTH, HEIGHT = 1120, 720
BACKGROUND = (13, 19, 35)
PANEL = (23, 33, 54)
CYAN = (78, 229, 217)
PINK = (255, 121, 164)
WHITE = (236, 246, 252)
MUTED = (146, 165, 185)
KEY_WIDTH = 98
LANE_GAP = 8
LANE_X = 34
GAME_RECT = pygame.Rect(34, 109, 1052, 378)
HIT_Y = 465
FALL_SECONDS = 2.4
FALL_SPEED = (HIT_Y - 156) / FALL_SECONDS
TILE_COLORS = (
    (73, 224, 214), (90, 174, 242), (156, 123, 245),
    (245, 119, 171), (255, 184, 100), (100, 210, 185),
    (123, 184, 255), (210, 131, 247), (251, 154, 115), (255, 209, 124),
)


@lru_cache(maxsize=80)
def font_for(size, bold=False):
    return pygame.font.SysFont("arial", size, bold=bold)


def text(screen, label: str, position: tuple[int, int], size=21, color=WHITE, bold=False):
    font = font_for(size, bold)
    image = font.render(label, True, color)
    screen.blit(image, position)
    return image.get_width()


def sound_wave(note: str) -> pygame.mixer.Sound:
    """Generación propia de notas con armónicos y desvanecimiento."""
    sample_rate = 44100
    duration = 0.95
    t = np.arange(int(sample_rate * duration), dtype=np.float64) / sample_rate
    freq = note_frequency(note)
    wave = (np.sin(2 * math.pi * freq * t)
            + 0.28 * np.sin(2 * math.pi * freq * 2 * t)
            + 0.10 * np.sin(2 * math.pi * freq * 3 * t))
    envelope = np.minimum(1.0, t / 0.012) * np.exp(-2.0 * t)
    envelope *= np.minimum(1.0, (duration - t) / 0.12)
    samples = np.asarray(wave * envelope * 11000, dtype=np.int16)
    stereo = np.ascontiguousarray(np.column_stack((samples, samples)))
    return pygame.sndarray.make_sound(stereo)


class Synth:
    def __init__(self):
        self.ready = False
        self.muted = False
        self.channels: dict[str, pygame.mixer.Channel] = {}
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
            self.sounds = {note: sound_wave(note) for note in NOTES}
            self.ready = True
        except pygame.error as exc:
            print(f"Audio desactivado: {exc}")

    def start(self, note):
        if not self.ready or self.muted:
            return
        channel = self.sounds[note].play()
        if channel:
            self.channels[note] = channel

    def end(self, note):
        channel = self.channels.pop(note, None)
        if channel:
            channel.fadeout(95)

    def stop_all(self):
        for note in list(self.channels):
            self.end(note)


def initialize_detector():
    """Carga MediaPipe Tasks; descarga el modelo oficial solo si hace falta."""
    import mediapipe as mp
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MODEL_FILE.exists():
        print("Descargando modelo de manos de MediaPipe...")
        temp = MODEL_FILE.with_suffix(".part")
        urllib.request.urlretrieve(MODEL_URL, temp)
        temp.replace(MODEL_FILE)
    options = vision.HandLandmarkerOptions(
        base_options=mp_tasks.BaseOptions(model_asset_path=str(MODEL_FILE)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.55,
    )
    return mp, vision.HandLandmarker.create_from_options(options)


def draw_hand_marks(screen, result, camera_rect):
    x0, y0, width, height = camera_rect
    for landmarks in result.hand_landmarks:
        def coord(point):
            return (x0 + int(point.x * width), y0 + int(point.y * height))
        for a, b in SKELETON:
            pygame.draw.line(screen, CYAN, coord(landmarks[a]), coord(landmarks[b]), 2)
        for landmark in landmarks:
            pygame.draw.circle(screen, WHITE, coord(landmark), 3)


def draw_background(screen):
    screen.fill(BACKGROUND)
    # Identidad visual propia, con líneas decorativas y paneles modernos.
    for i in range(0, WIDTH, 55):
        pygame.draw.line(screen, (19, 28, 46), (i, 75), (i, HEIGHT), 1)
    pygame.draw.rect(screen, PANEL, (0, 0, WIDTH, 77))
    pygame.draw.circle(screen, CYAN, (39, 38), 18)
    text(screen, "♫", (29, 22), size=24, color=BACKGROUND, bold=True)
    text(screen, "AEROKEYS", (70, 20), size=28, bold=True)
    text(screen, "PIANO DE GESTOS", (252, 31), size=14, color=MUTED)
    pygame.draw.line(screen, CYAN, (0, 76), (WIDTH, 76), 2)


def draw_camera_panel(screen, camera_image, hands_result):
    x, y, w, h = 34, 109, 700, 378
    pygame.draw.rect(screen, PANEL, (x - 2, y - 2, w + 4, h + 4), border_radius=16)
    if camera_image is not None:
        surf = pygame.image.frombuffer(camera_image.tobytes(),
                                       (camera_image.shape[1], camera_image.shape[0]), "RGB")
        surf = pygame.transform.smoothscale(surf, (w, h))
        screen.blit(surf, (x, y))
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((7, 13, 31, 36))
        screen.blit(overlay, (x, y))
        if hands_result is not None:
            draw_hand_marks(screen, hands_result, (x, y, w, h))
    else:
        for j in range(12):
            pygame.draw.line(screen, (32, 48, 70), (x + 30 + j * 58, y + 20),
                             (x + 30 + j * 58, y + h - 20), 1)
        text(screen, "DEMO / MODO TECLADO", (x + 144, y + 134), size=30, bold=True)
        text(screen, "Prueba A S D F G H J K L ;", (x + 166, y + 195), color=MUTED)
    pygame.draw.rect(screen, CYAN, (x, y, w, h), width=2, border_radius=14)
    text(screen, "VISOR EN TIEMPO REAL", (x + 14, y + 12), size=13, color=WHITE, bold=True)


def draw_info(screen, notes: set[str], detector_ok: bool, muted: bool):
    x, y, w, h = 758, 109, 328, 378
    pygame.draw.rect(screen, PANEL, (x, y, w, h), border_radius=16)
    text(screen, "PANEL DE CONTROL", (x + 22, y + 19), size=20, bold=True)
    pygame.draw.line(screen, (60, 79, 102), (x + 20, y + 55), (x + w - 20, y + 55))
    text(screen, "Modo", (x + 22, y + 75), size=16, color=MUTED)
    text(screen, "LIBRE", (x + 170, y + 70), size=22, color=CYAN, bold=True)
    text(screen, "Detector", (x + 22, y + 120), size=16, color=MUTED)
    text(screen, "ACTIVO" if detector_ok else "TECLADO", (x + 170, y + 116), size=17,
         color=CYAN if detector_ok else PINK, bold=True)
    text(screen, "Sonido", (x + 22, y + 159), size=16, color=MUTED)
    text(screen, "SILENCIO" if muted else "ENCENDIDO", (x + 170, y + 156), size=15,
         color=PINK if muted else CYAN, bold=True)
    text(screen, "Notas activas", (x + 22, y + 207), size=17, color=MUTED)
    text(screen, ", ".join(sorted(notes)) if notes else "Ninguna", (x + 22, y + 239),
         size=21, color=WHITE, bold=True)
    text(screen, "Flexiona dedos frente a la cámara", (x + 22, y + 286), size=15, color=MUTED)
    text(screen, "o usa el teclado para tocar.", (x + 22, y + 312), size=15, color=MUTED)


def draw_keys(screen, pressed: set[str]):
    y = 532
    text(screen, "TECLADO MUSICAL", (36, 504), size=17, bold=True)
    x0, gap = 34, 8
    for i, (note, key) in enumerate(zip(NOTES, KEYS)):
        x = x0 + i * (KEY_WIDTH + gap)
        active = note in pressed
        base = CYAN if active else (41, 58, 83)
        pygame.draw.rect(screen, base, (x, y, KEY_WIDTH, 148), border_radius=12)
        if not active:
            pygame.draw.rect(screen, (68, 91, 117), (x, y, KEY_WIDTH, 148), width=2, border_radius=12)
        fg = BACKGROUND if active else WHITE
        text(screen, note, (x + 24, y + 36), size=27, color=fg, bold=True)
        text(screen, key.upper(), (x + 42, y + 101), size=18,
             color=BACKGROUND if active else MUTED, bold=True)
    text(screen, "F1: Libre    F2: Demo Jingle Bells    F3: Jugar    ESPACIO: Reiniciar    M: Audio    ESC: Salir",
         (35, 691), size=14, color=MUTED)



def draw_game_board(screen, game: RhythmGame, t: float, mode: str,
                    flashing: dict[str, float], muted: bool):
    """Los bloques avanzan hacia abajo y coinciden con el teclado de 10 notas."""
    pygame.draw.rect(screen, PANEL, GAME_RECT, border_radius=15)
    # Carriles verticales perfectamente alineados con las teclas inferiores.
    for i, note in enumerate(NOTES):
        x = LANE_X + i * (KEY_WIDTH + LANE_GAP)
        pygame.draw.rect(screen, (26, 39, 64) if i % 2 == 0 else (30, 43, 67),
                         (x, 160, KEY_WIDTH, HIT_Y - 160), border_radius=8)
        if flashing.get(note, -99.0) > t:
            overlay = pygame.Surface((KEY_WIDTH, HIT_Y - 160), pygame.SRCALPHA)
            overlay.fill((*TILE_COLORS[i], 48))
            screen.blit(overlay, (x, 160))
        text(screen, note, (x + 33, 167), 16, color=(118, 145, 181), bold=True)

    # Dibuja solo las notas dentro de la zona de juego.
    screen.set_clip(pygame.Rect(36, 184, 1048, HIT_Y - 184))
    for i, tile in enumerate(game.tiles):
        judgement = game.results.get(i)
        if judgement is not None and judgement != "MISS":
            continue
        delta = tile.at - t
        note_idx = NOTES.index(tile.note)
        height = max(26, min(96, round(tile.duration * FALL_SPEED * 0.54)))
        bottom = HIT_Y - delta * FALL_SPEED
        top = round(bottom - height)
        if top >= HIT_Y + 3 or bottom <= 183:
            continue
        x = LANE_X + note_idx * (KEY_WIDTH + LANE_GAP) + 10
        width = KEY_WIDTH - 20
        color = TILE_COLORS[note_idx]
        if judgement == "MISS":
            color = (90, 102, 119)
        shadow = pygame.Rect(x + 3, top + 6, width, height)
        pygame.draw.rect(screen, (12, 20, 36), shadow, border_radius=9)
        rect = pygame.Rect(x, top, width, height)
        pygame.draw.rect(screen, color, rect, border_radius=9)
        pygame.draw.rect(screen, (250, 250, 252),
                         (x + 6, top + 5, width - 12, 3), border_radius=2)
        label_width = font_for(19, True).size(tile.note)[0]
        if height >= 27:
            text(screen, tile.note, (x + (width - label_width) // 2,
                                      top + max(4, (height - 22)//2)),
                 19, BACKGROUND, True)
    screen.set_clip(None)

    # Línea de acierto por encima de las teclas.
    pygame.draw.line(screen, (255, 209, 115), (36, HIT_Y), (1084, HIT_Y), 3)
    for i in range(10):
        x = LANE_X + i * (KEY_WIDTH + LANE_GAP) + 13
        pygame.draw.line(screen, (255, 209, 115), (x, HIT_Y + 6),
                         (x + KEY_WIDTH - 26, HIT_Y + 6), 2)

    # Panel superior con datos de la partida.
    pygame.draw.rect(screen, (17, 26, 45), (34, 109, 1052, 54), border_radius=13)
    text(screen, "JINGLE BELLS", (52, 122), 25, WHITE, True)
    text(screen, "DEMO" if mode == "demo" else "JUEGO", (279, 130),
         16, CYAN if mode == "demo" else PINK, True)
    if mode == "game":
        text(screen, f"PUNTOS  {game.score}", (421, 126), 19, WHITE, True)
        text(screen, f"COMBO  {game.combo}", (671, 126), 19, WHITE, True)
        text(screen, f"{game.hits}/{game.total}", (910, 126), 19, CYAN, True)
        if t - game.last_result_at <= 0.65:
            label = game.last_result
            color = CYAN if label == "PERFECT" else (255, 209, 115) if label == "GOOD" else PINK
            width = font_for(32, True).size(label)[0]
            text(screen, label, (560 - width // 2, 262), 32, color, True)
    else:
        text(screen, "Las notas suenan automaticamente al llegar a la linea", (422, 130),
             16, MUTED)
    if t < 0:
        text(screen, f"PREPARATE  {max(1, math.ceil(-t))}", (405, 344), 32, WHITE, True)
    elif mode == "game" and game.finished(t):
        rect = pygame.Rect(285, 219, 550, 183)
        pygame.draw.rect(screen, (12, 22, 41), rect, border_radius=18)
        pygame.draw.rect(screen, CYAN, rect, width=2, border_radius=18)
        text(screen, "¡CANCION TERMINADA!", (365, 240), 27, WHITE, True)
        text(screen, f"Puntos: {game.score}   Aciertos: {game.hits}/{game.total}",
             (343, 294), 22, CYAN, True)
        text(screen, "ESPACIO para jugar otra vez", (383, 349), 18, MUTED)
    elif mode == "demo" and t > game.end_time:
        text(screen, "Jingle Bells finalizado - ESPACIO para repetir", (316, 353),
             19, CYAN, True)


def main():
    parser = argparse.ArgumentParser(description="AeroKeys: piano gestual + Jingle Bells")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--demo", action="store_true", help="Jingle Bells automatico con notas cayendo")
    group.add_argument("--game", action="store_true", help="Jugar Jingle Bells: toca las notas que caen")
    parser.add_argument("--no-camera", action="store_true", help="Usar solo el teclado")
    parser.add_argument("--camera", type=int, default=0, help="Indice de la webcam")
    parser.add_argument("--mute", action="store_true", help="Iniciar en silencio")
    parser.add_argument("--bpm", type=int, default=105, help="Tempo de Jingle Bells, 40-200")
    parser.add_argument("--swap-hands", action="store_true", help="Invertir las manos si aparecen al reves")
    args = parser.parse_args()
    try:
        song = jingle_bells(args.bpm)
    except ValueError as exc:
        parser.error(str(exc))

    pygame.init()
    pygame.display.set_caption("AeroKeys | Jingle Bells")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    synth = Synth()
    synth.muted = args.mute
    mode = "demo" if args.demo else "game" if args.game else "free"
    game = RhythmGame(tiles=song)
    started = time.monotonic()
    gate = GestureGate()
    active: set[str] = set()
    keyboard_notes: set[str] = set()
    previous_camera_notes: set[str] = set()
    flash: dict[str, float] = {}
    auto_cursor = 0
    camera = None
    detector = None
    mp = None
    cv2 = None
    tracking_ready = False
    message = ""
    video = None
    hand_result = None
    swap_hands = args.swap_hands

    def change_mode(next_mode: str):
        nonlocal mode, game, started, active, auto_cursor
        synth.stop_all()
        active.clear()
        flash.clear()
        game = RhythmGame(tiles=song)
        started = time.monotonic()
        auto_cursor = 0
        mode = next_mode

    # Si se inicia en demo no hace falta webcam, pero el juego permite teclado
    # incluso cuando la cámara está desconectada.
    if not args.no_camera and not args.demo:
        try:
            import cv2 as opencv
            cv2 = opencv
            camera = cv2.VideoCapture(args.camera)
            if not camera.isOpened():
                raise RuntimeError("No se encontro una camara disponible")
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
            mp, detector = initialize_detector()
            tracking_ready = True
        except Exception as exc:
            message = f"Camara o modelo no disponible: {exc}"
            print(message)
            if camera is not None:
                camera.release()
            camera = None
            detector = None

    detection_start = time.monotonic()
    running = True
    try:
        while running:
            clock.tick(30)
            pressed_this_frame: set[str] = set()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_F1:
                        change_mode("free")
                    elif event.key == pygame.K_F2:
                        change_mode("demo")
                    elif event.key == pygame.K_F3:
                        change_mode("game")
                    elif event.key == pygame.K_SPACE and mode in ("game", "demo"):
                        change_mode(mode)
                    elif event.key == pygame.K_x:
                        swap_hands = not swap_hands
                        gate = GestureGate()
                        previous_camera_notes.clear()
                    elif event.key == pygame.K_m:
                        synth.muted = not synth.muted
                        if synth.muted:
                            synth.stop_all()
                    elif event.key == pygame.K_F12:
                        dest = ROOT / "captura_aerokeys.png"
                        pygame.image.save(screen, str(dest))
                        print(f"Captura guardada: {dest}")
                    else:
                        label = event.unicode.lower()
                        if label in KEY_TO_NOTE:
                            note = KEY_TO_NOTE[label]
                            if note not in keyboard_notes:
                                pressed_this_frame.add(note)
                            keyboard_notes.add(note)
                elif event.type == pygame.KEYUP:
                    label = pygame.key.name(event.key).lower()
                    if label in KEY_TO_NOTE:
                        keyboard_notes.discard(KEY_TO_NOTE[label])

            detected: set[tuple[str, str]] = set()
            hand_result = None
            if camera is not None and mode in ("free", "game"):
                ok, frame = camera.read()
                if ok:
                    frame = cv2.flip(frame, 1)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    video = np.ascontiguousarray(rgb)
                    if detector is not None:
                        timestamp_ms = int((time.monotonic() - detection_start) * 1000)
                        hand_result = detector.detect_for_video(
                            mp.Image(image_format=mp.ImageFormat.SRGB, data=video),
                            timestamp_ms,
                        )
                        for i, hand in enumerate(hand_result.hand_landmarks):
                            if i >= len(hand_result.handedness) or not hand_result.handedness[i]:
                                continue
                            handedness = hand_result.handedness[i][0].category_name
                            if handedness not in ("Left", "Right"):
                                continue
                            if swap_hands:
                                handedness = "Left" if handedness == "Right" else "Right"
                            for finger in bent_fingers(hand):
                                detected.add((handedness, finger))
            camera_keys = gate.update(detected) if mode in ("free", "game") else gate.update(set())
            camera_notes = {HAND_NOTE[key] for key in camera_keys}
            new_camera_presses = camera_notes - previous_camera_notes
            previous_camera_notes = camera_notes
            now = time.monotonic()
            t = now - started - FALL_SECONDS

            if mode == "free":
                target = set(keyboard_notes) | camera_notes
                for note in target - active:
                    synth.start(note)
                for note in active - target:
                    synth.end(note)
                active = target
            else:
                # En modo juego solo cuentan nuevas pulsaciones, no mantener
                # presionada una tecla mientras caen notas repetidas.
                if mode == "game":
                    game.update(t)
                    for note in pressed_this_frame | new_camera_presses:
                        synth.start(note)
                        flash[note] = t + 0.18
                        game.press(note, t)
                else:  # demo automática de Jingle Bells, con notas cayendo
                    while auto_cursor < len(song) and song[auto_cursor].at <= t:
                        tile = song[auto_cursor]
                        synth.start(tile.note)
                        flash[tile.note] = t + min(0.25, tile.duration * 0.8)
                        game.results[auto_cursor] = "DEMO"
                        auto_cursor += 1
                active = {note for note, expires in flash.items() if expires > t}
                # Eliminar destellos antiguos.
                for note in list(flash):
                    if flash[note] <= t:
                        del flash[note]

            draw_background(screen)
            if mode == "free":
                draw_camera_panel(screen, video, hand_result)
                draw_info(screen, active, tracking_ready, synth.muted)
            else:
                draw_game_board(screen, game, t, mode, flash, synth.muted)
            draw_keys(screen, active | camera_notes | keyboard_notes if mode == "game" else active)
            if message and mode == "free":
                text(screen, "Modo teclado activo; revisa la terminal.", (374, 94),
                     size=15, color=PINK)
            pygame.display.flip()
    finally:
        synth.stop_all()
        if detector:
            detector.close()
        if camera:
            camera.release()
        pygame.quit()


if __name__ == "__main__":
    main()
