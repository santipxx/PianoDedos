# 🎹 AeroKeys — Piano gestual con visión artificial

AeroKeys es una aplicación de escritorio en Python con una interfaz oscura y detalles neón. Detecta las manos con **MediaPipe Hand Landmarker**, estima qué dedos están flexionados y convierte los gestos en **10 notas musicales**. También permite tocar con el teclado y ejecutar una demostración automática de *Oda a la alegría*.

## Herramientas

- **Python 3.11** (recomendado; también 3.10 o 3.12)
- **MediaPipe** para la detección de 21 puntos de referencia por mano.
- **OpenCV** para leer y reflejar los fotogramas de la cámara.
- **Pygame** para la interfaz y el audio.
- **NumPy** para generar ondas sonoras con armónicos.

## Instalación

Descarga este proyecto y abre la carpeta en VS Code. Desde la terminal de la carpeta principal:

**Windows (PowerShell):**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe aerokeys.py --demo
```

Si no funciona `py -3.11`, usa `python` con una instalación de Python 3.11.

**macOS/Linux:**

```bash
python3.11 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python aerokeys.py --demo
```

## Modos de uso

| Modo | Windows PowerShell, desde la carpeta principal |
|------|----------|
| Piano gestual | `.\.venv\Scripts\python.exe aerokeys.py` |
| Demostración musical | `.\.venv\Scripts\python.exe aerokeys.py --demo` |
| Piano con teclado (sin cámara) | `.\.venv\Scripts\python.exe aerokeys.py --no-camera` |
| Usar segunda webcam | `.\.venv\Scripts\python.exe aerokeys.py --camera 1` |

Al iniciar el piano gestual por primera vez, el programa descarga el modelo `hand_landmarker.task` oficial de Google MediaPipe (requiere Internet). Si falla la cámara o el modelo, la aplicación continúa en modo teclado.

## Controles

- `A S D F G H J K L ;` → tocar las 10 notas.
- `F1` → modo libre.
- `F2` → demostración de *Oda a la alegría*.
- `M` → activar/desactivar audio.
- `F12` → crear `captura_aerokeys.png` para evidencias.
- `ESC` → cerrar.

## ¿Cómo funciona?

1. OpenCV obtiene la imagen de la webcam y aplica el efecto espejo.
2. MediaPipe extrae 21 puntos de cada mano.
3. Para cada dedo se calcula el ángulo de la articulación. Si está suficientemente flexionada, se considera presionado.
4. Un filtro de dos fotogramas reduce activaciones erráticas.
5. Cada dedo controla una nota, y Pygame dibuja las teclas y reproduce sonidos generados matemáticamente con NumPy.
6. La vista lateral muestra el modo, la detección y las notas activas.

## Estructura

```text
AeroKeys_Proyecto/
├── aerokeys.py         # aplicación, cámara, dibujo y audio
├── core.py             # notas, ángulos, antirrebote y melodía
├── requirements.txt    # dependencias
├── tests/test_core.py  # pruebas unitarias
├── assets/             # modelo de MediaPipe descargado al ejecutar
└── README.md           # instrucciones y explicación
```

## Pruebas

```bash
python -m unittest discover -s tests -v
```

## Antes de entregar

Ejecuta los modos demo y libre, toma una captura con `F12` y comprueba que puedes explicar cómo funcionan `joint_angle`, `bent_fingers` y `sound_wave`. Si tu asignatura exige declarar asistencia de IA, inclúyela en tu informe.
