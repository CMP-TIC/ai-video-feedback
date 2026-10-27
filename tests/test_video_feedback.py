import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/video-feedback/scripts/analyze_video.py'


class VideoFeedbackTest(unittest.TestCase):
    def test_real_video_with_audio_and_feedback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / 'grabación con espacios.mkv'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'testsrc2=size=320x180:rate=10', '-f', 'lavfi', '-i',
                            'sine=frequency=440:sample_rate=16000', '-t', '2',
                            '-c:v', 'mpeg4', '-c:a', 'pcm_s16le', str(video)], check=True)
            command = [sys.executable, str(SCRIPT), str(video), '-o', str(root / 'out'),
                       '--start', '0.5', '--end', '1.8', '--interval', '0.25',
                       '--max-frames', '3', '--feedback', 'El botón no guarda.']
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((root / 'out/manifest.json').read_text())
            self.assertEqual(len(manifest['frames']), 3)
            self.assertEqual(manifest['frames'][0]['timestamp_seconds'], 0.5)
            self.assertGreater(manifest['frames'][-1]['timestamp_seconds'], 1.5)
            for frame in manifest['frames']:
                self.assertGreater((root / 'out' / frame['path']).stat().st_size, 0)
            self.assertGreater((root / 'out/audio.wav').stat().st_size, 44)
            self.assertIn('El botón no guarda.', (root / 'out/feedback.md').read_text())
            self.assertTrue(video.is_file())
            retry = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(retry.returncode, 0)
            self.assertEqual(json.loads((root / 'out/manifest.json').read_text()), manifest)
            transcript = root / 'speech.srt'
            transcript.write_text('1\n00:00:00,500 --> 00:00:01,000\nGuarda aquí.\n')
            comments = root / 'comments.txt'
            comments.write_text('Conservar selección: áéíóú.')
            extra = subprocess.run([sys.executable, str(SCRIPT), str(video),
                                    '-o', str(root / 'text-out'), '--no-audio',
                                    '--feedback-file', str(comments), '--transcript', str(transcript)],
                                   capture_output=True, text=True)
            self.assertEqual(extra.returncode, 0, extra.stderr)
            self.assertFalse((root / 'text-out/audio.wav').exists())
            self.assertEqual((root / 'text-out/transcript.srt').read_bytes(), transcript.read_bytes())
            self.assertIn(comments.read_text(), (root / 'text-out/feedback.md').read_text())

    def test_short_silent_video_and_invalid_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / 'short.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'color=c=red:size=64x64:rate=10', '-t', '0.3', str(video)], check=True)
            def run(*args):
                return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                      capture_output=True, text=True)
            result = run(video, '-o', root / 'out')
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((root / 'out/manifest.json').read_text())
            self.assertEqual(len(manifest['frames']), 1)
            self.assertIsNone(manifest['audio'])
            self.assertFalse((root / 'out/audio.wav').exists())
            for args in [(video, '--interval', '0'), (video, '--start', 'nan'),
                         (video, '--start', '5'), (root / 'missing.mp4',)]:
                self.assertNotEqual(run(*args).returncode, 0)
            bad = root / 'bad.mkv'
            bad.write_text('not a video')
            self.assertNotEqual(run(bad, '-o', root / 'bad-out').returncode, 0)
            self.assertFalse((root / 'bad-out').exists())


if __name__ == '__main__':
    unittest.main()
