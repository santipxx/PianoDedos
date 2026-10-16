# AeroKeys — Jingle Bells con notas que caen

**AeroKeys** es un piano gestual educativo realizado en Python. La webcam reconoce qué dedos flexionas con MediaPipe; también puedes tocar con las teclas del computador. Incluye un **juego musical de Jingle Bells**: las fichas de colores bajan por diez carriles y debes tocarlas cuando llegan a la **línea dorada**.

## Qué hace esta versión

- **F3 — JUEGO JINGLE BELLS**: 49 notas de la melodía, con sus tiempos musicales. Usa tus manos o `A S D F G H J K L ;`. La nota correcta en el momento correcto da puntos.
- **F2 — DEMO JINGLE BELLS**: las mismas fichas caen y el piano toca automáticamente, perfecto para mostrar la tarea sin cámara.
- **F1 — PIANO LIBRE**: los diez dedos controlan diez notas (C4 a E5) al flexionarlos, o toca con el teclado.
- **Puntuación**: `PERFECT` (100), `GOOD` (70) y `OK` (40), además de combo y notas falladas (`MISS`).
- **Velocidad ajustable**: puedes indicar BPM con `--bpm 85` para practicar más despacio.
- Interfaz oscura propia, sonidos sintetizados con NumPy/Pygame y modo alternativo sin cámara.

## Requisitos

- **Windows 10/11** (o macOS/Linux con cambios en los comandos).
- **Python 3.11** recomendado, con la opción *Add Python to PATH* activada al instalar; compatibles 3.10–3.12.
- Internet para instalar dependencias; el primer uso con cámara descarga el archivo de modelo oficial de MediaPipe.
- Webcam opcional (puedes entregar una demostración con el teclado).

### 1. Comprueba que Python está disponible

Abre VS Code en la carpeta que contiene `aerokeys.py`, abre una terminal PowerShell y ejecuta:

```powershell
python --version
```

Si el comando falla, **Python no está instalado o no está en PATH**. Instálalo desde https://www.python.org/downloads/windows/ o desde PowerShell con:

```powershell
winget install -e --id Python.Python.3.11
```

Después **cierra por completo VS Code, vuelve a abrirlo** y comprueba `python --version`. No sigas con los siguientes comandos hasta verlo funcionando.

### 2. Instala las librerías (solo una vez)

**Opción simple en Windows:** haz doble clic en `INSTALAR_WINDOWS.bat`, que comprueba Python, crea el entorno virtual y descarga las librerías.

**Opción manual desde PowerShell**: copia cada comando y espera que termine, uno por uno:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> Si ves `>>` en PowerShell, presiona `Ctrl + C` para cancelar el comando incompleto y vuelve a intentarlo. Si los comandos no encuentran `requirements.txt`, abre la carpeta correcta en VS Code.

### 3. Ejecuta Jingle Bells

**Para ver la demostración con notas cayendo (NO necesita cámara):**

```powershell
.\.venv\Scripts\python.exe aerokeys.py --demo
```

**Para jugar con la webcam:**

```powershell
.\.venv\Scripts\python.exe aerokeys.py --game
```

**Para jugar sin cámara usando `A S D F G H J K L ;`:**

```powershell
.\.venv\Scripts\python.exe aerokeys.py --game --no-camera
```

**Para hacerlo más fácil y lento:**

```powershell
.\.venv\Scripts\python.exe aerokeys.py --game --no-camera --bpm 80
```

**Piano libre:**

```powershell
.\.venv\Scripts\python.exe aerokeys.py --no-camera
```

En Windows también puedes hacer doble clic en `DEMO_JINGLE.bat` o `JUGAR_JINGLE.bat` después de instalar.

### Atajos de teclado

| Tecla | Acción |
|---|---|
| `F1` | Piano libre |
| `F2` | Demostración automática de Jingle Bells con fichas cayendo |
| `F3` | Juego de Jingle Bells |
| `A S D F G H J K L ;` | 10 notas, de C4 a E5 |
| `ESPACIO` | Reinicia el juego o la demostración |
| `X` | Intercambia mano izquierda/derecha si la cámara reconoce al revés |
| `M` | Silencia o vuelve a activar el sonido |
| `F12` | Guarda `captura_aerokeys.png` para evidencias |
| `ESC` | Cierra la aplicación |

**Cómo jugar:** espera el inicio de la canción; mira el carril de cada nota. Cuando la **parte inferior del bloque** llegue a la **línea dorada**, flexiona el dedo correspondiente o presiona la tecla del carril. **Suelta y vuelve a presionar** para notas repetidas. La pantalla muestra puntaje y combo. Una ventana de tiempo de 0,31 segundos permite aciertos ligeramente adelantados o retrasados.

## Cómo funciona técnicamente

1. `aerokeys.py` abre la ventana de Pygame y maneja la cámara con OpenCV (solo si se necesita).
2. MediaPipe Hand Landmarker detecta 21 puntos por mano. `core.py` usa los ángulos de los dedos para convertir gestos en notas.
3. `rhythm.py` almacena la partitura simplificada de **Jingle Bells** en tiempos medidos en segundos a partir de BPM.
4. Los bloques se colocan según `y = HIT_Y - (momento_nota - tiempo_actual) * velocidad_caida`; así llegan exactamente a la línea cuando deben tocarse.
5. `RhythmGame` compara la pulsación real con el momento previsto y calcula resultado, puntos, combo y fallos.
6. El sintetizador produce notas con armónicos y las envía a Pygame. En modo demostración las reproduce automáticamente.

## Archivos

```text
AeroKeys_Jingle_Bells/
├── aerokeys.py           # Ventanas, audio, webcam, notas cayendo
├── core.py               # Detección de dedos, notas y frecuencias
├── rhythm.py             # Partitura Jingle Bells y puntuación
├── requirements.txt      # Librerías necesarias
├── INSTALAR_WINDOWS.bat  # Instalación automática en Windows
├── DEMO_JINGLE.bat       # Abre el modo demostración
├── JUGAR_JINGLE.bat      # Abre el modo juego
├── tests/
│   ├── test_core.py      # Pruebas de gestos y música
│   └── test_rhythm.py    # Pruebas de melodía, tiempos, combo y score
└── README.md
```

## Pruebas

Desde la carpeta del proyecto, ejecuta:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las **12 pruebas unitarias** del proyecto pasaron en el entorno de preparación. Se comprobó sintaxis y lógica musical. **No se ha validado el funcionamiento real de la webcam ni la interfaz en Windows**, por lo que se recomienda ejecutar la demo y el juego en el PC antes de la entrega.

## Entrega y autoría

Incluye una captura de la demostración de Jingle Bells y otra del modo juego, junto con una breve explicación del reconocimiento de dedos y la puntuación. Comprueba las normas de tu asignatura sobre referencias y declaración del uso de IA o código de terceros.
