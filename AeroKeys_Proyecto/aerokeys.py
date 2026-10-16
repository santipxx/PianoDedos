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
from pathlib import Path

import numpy as np
import pygame

from core import (
    FINGERS, HAND_NOTE, KEY_TO_NOTE, KEYS, NOTES, SKELETON,
    GestureGate, Melody, bent_fingers, note_frequency,
)

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


def text(screen, label: str, position: tuple[int, int], size=21, color=WHITE, bold=False):
    font = pygame.font.SysFont("arial", size, bold=bold)
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


def draw_info(screen, mode: str, notes: set[str], detector_ok: bool, muted: bool, progress: float):
    x, y, w, h = 758, 109, 328, 378
    pygame.draw.rect(screen, PANEL, (x, y, w, h), border_radius=16)
    text(screen, "PANEL DE CONTROL", (x + 22, y + 19), size=20, bold=True)
    pygame.draw.line(screen, (60, 79, 102), (x + 20, y + 55), (x + w - 20, y + 55))
    text(screen, "Modo", (x + 22, y + 75), size=16, color=MUTED)
    text(screen, "DEMO" if mode == "demo" else "LIBRE", (x + 170, y + 70), size=22, color=CYAN, bold=True)
    text(screen, "Detector", (x + 22, y + 120), size=16, color=MUTED)
    text(screen, "ACTIVO" if detector_ok else "TECLADO", (x + 170, y + 116), size=17,
         color=CYAN if detector_ok else PINK, bold=True)
    text(screen, "Sonido", (x + 22, y + 159), size=16, color=MUTED)
    text(screen, "SILENCIO" if muted else "ENCENDIDO", (x + 170, y + 156), size=15,
         color=PINK if muted else CYAN, bold=True)
    text(screen, "Notas activas", (x + 22, y + 207), size=17, color=MUTED)
    text(screen, ", ".join(sorted(notes)) if notes else "Ninguna", (x + 22, y + 239),
         size=21, color=WHITE, bold=True)
    if mode == "demo":
        text(screen, "Oda a la alegría", (x + 22, y + 286), size=16, color=CYAN)
        pygame.draw.rect(screen, (57, 74, 96), (x + 22, y + 321, w - 44, 8), border_radius=4)
        pygame.draw.rect(screen, PINK, (x + 22, y + 321, max(1, int((w - 44) * progress)), 8), border_radius=4)
    else:
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
    text(screen, "F1: Libre     F2: Demo     M: Silenciar     F12: Captura     ESC: Salir",
         (35, 688), size=15, color=MUTED)


def main():
    parser = argparse.ArgumentParser(description="AeroKeys: piano gestual con cámara")
    parser.add_argument("--demo", action="store_true", help="Demostración automática")
    parser.add_argument("--no-camera", action="store_true", help="Usar solo el teclado")
    parser.add_argument("--camera", type=int, default=0, help="Índice de la webcam")
    parser.add_argument("--mute", action="store_true", help="Iniciar en silencio")
    args = parser.parse_args()

    pygame.init()
    pygame.display.set_caption("AeroKeys | Piano de Gestos")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    synth = Synth()
    synth.muted = args.mute
    mode = "demo" if args.demo else "free"
    melody = Melody()
    demo_started = time.monotonic()
    gate = GestureGate()
    active = set()
    keyboard_notes = set()
    capture = None
    detector = None
    mp = None
    cv2 = None
    tracking_ready = False
    message = ""
    video = None
    hand_result = None

    if not args.no_camera and not args.demo:
        try:
            import cv2 as opencv
            cv2 = opencv
            capture = cv2.VideoCapture(args.camera)
            if not capture.isOpened():
                raise RuntimeError("No se encontró una cámara disponible")
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
            mp, detector = initialize_detector()
            tracking_ready = True
        except Exception as exc:
            message = f"Cámara o modelo no disponible: {exc}"
            print(message)
            if capture is not None:
                capture.release()
            capture = None
            detector = None

    start = time.monotonic()
    running = True
    try:
        while running:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_F1:
                        mode = "free"
                        demo_started = time.monotonic()
                    elif event.key == pygame.K_F2:
                        mode = "demo"
                        demo_started = time.monotonic()
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
                            keyboard_notes.add(KEY_TO_NOTE[label])
                elif event.type == pygame.KEYUP:
                    label = pygame.key.name(event.key).lower()
                    if label in KEY_TO_NOTE:
                        keyboard_notes.discard(KEY_TO_NOTE[label])

            detected = set()
            hand_result = None
            if capture is not None:
                ok, frame = capture.read()
                if ok:
                    frame = cv2.flip(frame, 1)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    video = np.ascontiguousarray(rgb)
                    if detector is not None:
                        timestamp_ms = int((time.monotonic() - start) * 1000)
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
                            for finger in bent_fingers(hand):
                                detected.add((handedness, finger))
            camera_keys = gate.update(detected) if mode == "free" else gate.update(set())
            camera_notes = {HAND_NOTE[key] for key in camera_keys}
            demo_note = None
            progress = 0.0
            if mode == "demo":
                demo_note, progress = melody.at(time.monotonic() - demo_started)
            target = set(keyboard_notes) | camera_notes
            if demo_note:
                target.add(demo_note)

            for note in target - active:
                synth.start(note)
            for note in active - target:
                synth.end(note)
            active = target

            draw_background(screen)
            draw_camera_panel(screen, video if mode == "free" else None, hand_result)
            draw_info(screen, mode, active, tracking_ready, synth.muted, progress)
            draw_keys(screen, active)
            if message:
                text(screen, "Modo teclado activo; revisa la terminal.", (374, 94), size=15, color=PINK)
            pygame.display.flip()
    finally:
        synth.stop_all()
        if detector:
            detector.close()
        if capture:
            capture.release()
        pygame.quit()


if __name__ == "__main__":
    main()
