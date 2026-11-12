# AI Video Feedback

Utilidad local y skill para agentes para convertir una grabación y tus comentarios en feedback útil para un agente. Python 3 + FFmpeg; sin dependencias Python ni claves API.

## Uso con tu agente

```text
$video-feedback analiza /ruta/demo.mkv.
En 00:18 el botón Guardar pierde la selección. Debe conservarla.
Prepara el feedback y los criterios de aceptación para corregirlo.
```

Puedes aportar el vídeo sin comentarios escritos: el agente revisará las capturas y, si tiene herramientas de audio, la narración. La utilidad prepara las evidencias; la interpretación la realiza el agente. No incluye un motor de transcripción automática.

## Uso directo

```bash
python3 skills/video-feedback/scripts/analyze_video.py /ruta/demo.mkv \
  --feedback 'El botón debe conservar la selección'
```

Imprime la ruta de un informe Markdown editable. En la misma carpeta quedan `metadata.json`, `manifest.json`, capturas PNG con sus tiempos y `audio.wav` cuando existe audio. Acepta una transcripción existente con `--transcript /ruta/narracion.srt` y comentarios desde archivo con `--feedback-file /ruta/comentarios.txt`.

Para examinar una interacción breve:

```bash
python3 skills/video-feedback/scripts/analyze_video.py /ruta/demo.mkv \
  --start 15 --end 22 --interval 0.5 --max-frames 20
```

Las marcas son posiciones de búsqueda aproximadas en el vídeo original. El audio empieza en el segundo indicado por `--start`. El máximo de capturas predeterminado es 24; al alcanzarlo, el muestreo se distribuye por el tramo seleccionado. No detecta escenas ni garantiza capturar todas las acciones entre muestras. Las carpetas existentes nunca se sobrescriben. En caso de fallo puede quedar una carpeta parcial; el proceso devuelve un código distinto de cero.

## Instalación

Necesitas Git, Python 3.10 o posterior y FFmpeg (incluye `ffprobe`). En Debian/Ubuntu:

```bash
sudo apt update
sudo apt install git python3 ffmpeg
git clone https://github.com/CMP-TIC/ai-video-feedback.git
cd ai-video-feedback
python3 skills/video-feedback/scripts/analyze_video.py --help
```

En macOS puedes instalar los requisitos con `brew install python ffmpeg git`.
No necesitas instalar paquetes con `pip` ni configurar claves API.

### Registrar la skill en Codex y otros agentes

Desde la raíz del repositorio, en Linux/macOS:

```bash
mkdir -p "$HOME/.codex/skills" "$HOME/.agents/skills"
ln -s "$PWD/skills/video-feedback" "$HOME/.codex/skills/video-feedback"
ln -s "$PWD/skills/video-feedback" "$HOME/.agents/skills/video-feedback"
```

Si alguno de los destinos ya existe, revisa su contenido antes de cambiarlo.
Los enlaces comparten la misma fuente; conserva el clon en su ubicación.
Abre una sesión nueva del agente e invoca `$video-feedback`.
También puedes usar el script directamente, sin registrar la skill.

## Qué compartir

El repositorio contiene la skill, el script y sus pruebas. Los vídeos y la
carpeta `video-analysis/` no forman parte del repositorio. El procesamiento
se realiza en tu equipo; el script no sube archivos a servicios externos.
Si entregas las evidencias a un agente externo, revisa antes las capturas,
el audio y los metadatos: pueden contener información del vídeo y rutas locales.

## Validación

```bash
python3 -m unittest discover -s tests -v
```

Las pruebas generan vídeos sintéticos y verifican extracción con audio, vídeo corto sin audio, marcas de tiempo, límites, comentarios, errores y conservación de análisis anteriores.

## Procedencia

Adaptada de una utilidad interna de extracción de evidencias con FFmpeg.
Añade errores verificables, muestreo acotado, selección de tramos y contexto
para el agente. No incluye vídeos ni datos de los proyectos de origen.
