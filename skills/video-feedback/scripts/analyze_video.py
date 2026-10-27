#!/usr/bin/env python3
"""Prepare local video evidence for an agent; no AI service or upload required."""
import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f'{command[0]} falló: {result.stderr[-2000:].strip()}')
    return result.stdout


def timestamp(seconds):
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    secs, millis = divmod(millis, 1000)
    return f'{hours:02}:{minutes:02}:{secs:02}.{millis:03}'


def prepare(args):
    for tool in ('ffprobe', 'ffmpeg'):
        if not shutil.which(tool):
            raise ValueError(f'Falta {tool}; instala FFmpeg para usar esta utilidad.')
    video = args.video.expanduser().resolve(strict=True)
    if not video.is_file():
        raise ValueError('El vídeo debe ser un archivo local.')
    if (not all(math.isfinite(v) for v in (args.start, args.interval))
            or args.start < 0 or args.interval <= 0 or args.max_frames < 1
            or args.width < 16):
        raise ValueError('Inicio >= 0; intervalo > 0; máximo de capturas >= 1; ancho >= 16.')
    info = json.loads(run(['ffprobe', '-v', 'error', '-show_format',
                           '-show_streams', '-of', 'json', str(video)]))
    streams = info.get('streams', [])
    if not any(s.get('codec_type') == 'video' and
               not s.get('disposition', {}).get('attached_pic') for s in streams):
        raise ValueError('El archivo no contiene una pista de vídeo.')
    duration = float(info.get('format', {}).get('duration', 0))
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('No se pudo determinar una duración válida.')
    end = min(args.end, duration) if args.end is not None else duration
    if not math.isfinite(end) or not 0 <= args.start < end:
        raise ValueError('El tramo debe cumplir 0 <= inicio < fin <= duración.')
    feedback = args.feedback or ''
    if args.feedback_file:
        feedback = args.feedback_file.expanduser().read_text(encoding='utf-8')
    transcript = args.transcript.expanduser().resolve(strict=True) if args.transcript else None
    if transcript and (not transcript.is_file() or transcript.suffix.lower() not in ('.txt', '.srt', '.vtt', '.md')):
        raise ValueError('La transcripción debe ser un archivo TXT, SRT, VTT o MD.')
    output = (args.output or Path.cwd() / 'video-analysis' /
              f'{video.stem}-{datetime.now():%Y%m%d-%H%M%S-%f}').expanduser().resolve()
    # Exclusive creation preserves earlier runs and user files, including on failure.
    output.mkdir(parents=True, exist_ok=False)
    (output / 'frames').mkdir()
    (output / 'metadata.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
    span = end - args.start
    count = min(args.max_frames, max(1, math.ceil(span / args.interval)))
    # Spread capped samples across the selected span rather than dropping its tail.
    last = max(args.start, end - min(0.1, span / 2))
    capped = math.ceil(span / args.interval) > args.max_frames
    times = ([args.start + (last - args.start) * i / (count - 1) for i in range(count)]
             if capped and count > 1 else [args.start + i * args.interval for i in range(count)])
    frames = []
    for index, point in enumerate(times, 1):
        relative = f'frames/frame_{index:04}.png'
        run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(point), '-i', str(video),
             '-map', '0:V:0', '-frames:v', '1', '-vf',
             f'scale=min({args.width}\\,iw):-2', '-threads', '1', str(output / relative)])
        if not (output / relative).is_file() or not (output / relative).stat().st_size:
            raise ValueError(f'No se pudo extraer una captura en {timestamp(point)}. Carpeta parcial: {output}')
        frames.append({'path': relative, 'timestamp_seconds': round(point, 6),
                       'timestamp': timestamp(point)})
    audio = None
    if not args.no_audio and any(s.get('codec_type') == 'audio' for s in streams):
        audio = 'audio.wav'
        run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(args.start), '-i', str(video),
             '-t', str(span), '-map', '0:a:0', '-vn', '-ar', '16000', '-ac', '1',
             '-c:a', 'pcm_s16le', str(output / audio)])
    transcript_name = None
    if transcript:
        transcript_name = 'transcript' + transcript.suffix.lower()
        shutil.copyfile(transcript, output / transcript_name)
    manifest = {'source': str(video), 'duration_seconds': duration,
                'start_seconds': args.start, 'end_seconds': end,
                'requested_interval_seconds': args.interval, 'sampling_capped': capped,
                'timestamps': 'Requested seek positions, relative to the original video; frame precision depends on source FPS.',
                'frames': frames, 'audio': audio, 'audio_offset_seconds': args.start,
                'transcript': transcript_name,
                'transcript_source': str(transcript) if transcript else None}
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    links = '\n'.join(f"- [{f['timestamp']}]({f['path']})" for f in frames)
    notes = ('Audio extraído; pendiente de escucha o transcripción.' if audio else
             'Audio omitido por opción.' if args.no_audio else 'El vídeo no contiene audio.')
    report = f'''# Evidencias para feedback de vídeo

Vídeo: {video}
Tramo: {timestamp(args.start)} – {timestamp(end)}. Capturas: {len(frames)}.
Muestreo limitado: {'sí; distribuido por el tramo' if capped else 'no'}.
Las marcas son posiciones de búsqueda aproximadas en el vídeo original.
Las capturas son muestras: las acciones entre ellas requieren una revisión más densa.

## Comentarios del usuario (texto original)

{feedback or '(No se han adjuntado comentarios escritos.)'}

## Audio y transcripción

{notes}
Transcripción aportada: {transcript_name or 'ninguna'}. Se copia íntegra, sin desplazar sus tiempos.
El segundo 0 del audio extraído corresponde a {timestamp(args.start)} del vídeo original.

## Capturas

{links}

## Análisis del agente (pendiente)

Tras abrir las capturas y revisar el audio o texto disponible, redactar:
- Objetivo y pasos observados, con marcas de tiempo y evidencias.
- Feedback solicitado: comportamiento actual → esperado.
- Cambios accionables y criterio de aceptación por cambio.
- Dudas, inferencias y partes del vídeo o audio que no se han revisado.
'''
    (output / 'feedback.md').write_text(report, encoding='utf-8')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    parser.add_argument('-o', '--output', type=Path, help='Carpeta nueva; nunca sobrescribe una existente')
    parser.add_argument('--start', type=float, default=0, help='Segundo inicial en el vídeo original')
    parser.add_argument('--end', type=float, help='Segundo final; por defecto duración total')
    parser.add_argument('--interval', type=float, default=5, help='Segundos entre capturas (por defecto 5)')
    parser.add_argument('--max-frames', type=int, default=24)
    parser.add_argument('--width', type=int, default=1600, help='Ancho máximo, sin ampliar')
    parser.add_argument('--no-audio', action='store_true')
    feedback = parser.add_mutually_exclusive_group()
    feedback.add_argument('--feedback', help='Comentarios del usuario en texto')
    feedback.add_argument('--feedback-file', type=Path, help='Archivo UTF-8 con comentarios')
    parser.add_argument('--transcript', type=Path, help='Transcripción existente; no se genera automáticamente')
    args = parser.parse_args()
    try:
        output = prepare(args)
    except (OSError, ValueError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    print(output / 'feedback.md')
    return 0


if __name__ == '__main__':
    sys.exit(main())
