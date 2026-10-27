# Video Feedback

Utilidad local y skill global para convertir una grabación y tus comentarios en feedback útil para un agente. Python 3 + FFmpeg; sin dependencias Python ni claves API.

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

## Instalación global en este equipo

La fuente está en `skills/video-feedback`. Los enlaces en `~/.codex/skills/video-feedback` y `~/.agents/skills/video-feedback` apuntan a esa misma carpeta, por lo que los cambios se mantienen en un único sitio. Invócala como `$video-feedback`.

## Validación

```bash
python3 -m unittest discover -s tests -v
```

Las pruebas generan vídeos sintéticos y verifican extracción con audio, vídeo corto sin audio, marcas de tiempo, límites, comentarios, errores y conservación de análisis anteriores.

## Procedencia

Adaptada del patrón de extracción de `analyze_video.py` en `/opt/odoo16_dev/temp/commercial_exports_workflow`: metadatos con ffprobe, capturas y audio con ffmpeg. Se han añadido errores verificables, muestreo acotado, selección de tramos y contexto para el agente. El original y sus vídeos se conservan en su ubicación; `install_and_test.py` era una utilidad específica de Odoo y no forma parte de esta herramienta.
