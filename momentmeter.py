#!/usr/bin/env python3
"""Offline Shorts production. Standard library only; no paid APIs."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import textwrap
import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / 'data/config.json').read_text())

def run(args):
    return subprocess.run([str(x) for x in args], check=True, capture_output=True, text=True).stdout

def local(path):
    p = (ROOT / path).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError('Path must stay inside the project')
    return p

def load(job):
    if not re.fullmatch(r'[a-z0-9-]+', job):
        raise ValueError('Invalid job ID')
    p = ROOT / 'data/jobs' / (job + '.json')
    data = json.loads(p.read_text())
    if data['id'] != job:
        raise ValueError('Job ID does not match filename')
    return data

def validate(data, draft=False):
    if data.get('language') != 'en':
        raise ValueError('This release supports English narration/captions')
    clips = data.get('clips', [])
    if len(clips) not in (5, 6):
        raise ValueError('Use 5 or 6 ranked clips')
    if [c['rank'] for c in clips] != list(range(len(clips), 0, -1)):
        raise ValueError('Ranks must count down to 1')
    words = len((data['hook'] + ' ' + ' '.join(c['narration'] for c in clips)).split())
    if not 70 <= words <= 100:
        raise ValueError(f'Narration must contain 70–100 words; found {words}')
    for c in clips:
        local(c['file'])
        if not c.get('narration') or not c.get('label') or float(c.get('start', 0)) < 0:
            raise ValueError('Missing caption/narration or invalid start')
        if draft:
            continue
        for key in ('source_url', 'license_url'):
            u = urllib.parse.urlsplit(c.get(key, ''))
            if u.scheme != 'https' or not u.netloc:
                raise ValueError(f'Rank {c["rank"]}: {key} needs a HTTPS URL')
        if c.get('rights_verified') is not True or not c.get('license'):
            raise ValueError(f'Rank {c["rank"]}: verify usage rights first')
        if not local(c['file']).is_file():
            raise ValueError(f'Missing clip: {c["file"]}')
    return words

def duration(path):
    return float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', path]).strip())

def fingerprint(data):
    h = hashlib.sha256(json.dumps(data, sort_keys=True).encode())
    for c in data['clips']:
        with local(c['file']).open('rb') as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                h.update(block)
        if c.get('voice_file'):
            h.update(local(c['voice_file']).read_bytes())
    return h.hexdigest()

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def render(data):
    validate(data)
    out = ROOT / 'output' / data['id']
    out.mkdir(parents=True, exist_ok=True)
    voice_tool = shutil.which('espeak-ng') or shutil.which('espeak')
    voices, lengths = [], []
    for i, clip in enumerate(data['clips']):
        sentence = (data['hook'] + ' ' if i == 0 else '') + clip['narration']
        voice = out / f'voice-{i}.wav'
        if clip.get('voice_file'):
            run(['ffmpeg', '-y', '-i', local(clip['voice_file']), '-ar', '48000', '-ac', '1', voice])
        elif voice_tool:
            run([voice_tool, '-v', 'en-us', '-s', '175', '-w', voice, sentence])
        else:
            raise ValueError('Install espeak-ng or provide a voice_file per clip; first voice includes hook')
        voices.append(voice)
        lengths.append(duration(voice) + 0.25)
    total = sum(lengths)
    if not CONFIG['min_seconds'] <= total <= CONFIG['max_seconds']:
        raise ValueError(f'Voice duration {total:.1f}s is outside 25–40s. Edit script or recorded voice.')
    segments = []
    for i, (clip, voice, seconds) in enumerate(zip(data['clips'], voices, lengths)):
        source = local(clip['file'])
        if float(clip.get('start', 0)) + seconds > duration(source):
            raise ValueError(f'Clip {clip["rank"]} is too short; choose a longer source')
        # Text files prevent user text from becoming FFmpeg filter expressions.
        label = out / f'label-{i}.txt'
        label.write_text(f'#{clip["rank"]}  {clip["label"]}')
        subtitle = out / f'captions-{i}.srt'
        sentence = (data['hook'] + ' ' if i == 0 else '') + clip['narration']
        chunks = textwrap.wrap(sentence, width=32)
        def stamp(t):
            ms = int(t * 1000)
            return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
        subtitle.write_text('\n\n'.join(f'{j+1}\n{stamp(j*seconds/len(chunks))} --> {stamp((j+1)*seconds/len(chunks))}\n{s}' for j, s in enumerate(chunks)))
        segment = out / f'segment-{i}.mp4'
        # Generated path is constrained by job ID and contains no filter metacharacters.
        label_rel = label.relative_to(ROOT).as_posix()
        subtitle_rel = subtitle.relative_to(ROOT).as_posix()
        vf = f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,subtitles={subtitle_rel}:force_style=FontName=DejaVu Sans\\,FontSize=8\\,MarginV=35\\,Outline=2,drawbox=x=0:y=180:w=iw:h=170:color=black@0.65:t=fill,drawtext=textfile={label_rel}:fontcolor=white:fontsize=56:x=(w-text_w)/2:y=235'
        run(['ffmpeg', '-y', '-ss', str(clip.get('start', 0)), '-i', source, '-i', voice, '-t', str(seconds), '-vf', vf, '-map', '0:v:0', '-map', '1:a:0', '-af', 'apad', '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '48000', '-ac', '2', segment])
        segments.append(segment)
    concat = out / 'concat.txt'
    concat.write_text('\n'.join(f"file '{p.name}'" for p in segments))
    final = out / 'short.mp4'
    run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat, '-c', 'copy', '-movflags', '+faststart', final])
    actual = duration(final)
    if not 25 <= actual <= 40:
        raise ValueError('Final video failed duration QA')
    metadata = {'job_id': data['id'], 'rendered_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'duration': actual, 'input_hash': fingerprint(data), 'video_hash': sha(final), 'approved': False}
    (out / 'review.json').write_text(json.dumps(metadata, indent=2))
    (out / 'upload.txt').write_text(data['title'] + '\n\n' + data['description'] + '\n\n' + '\n'.join(c['source_url'] for c in data['clips']))
    print(f'Rendered {final}; {actual:.1f}s. Review before approval.')

def approve(data):
    validate(data)
    out = ROOT / 'output' / data['id']
    p = out / 'review.json'
    review = json.loads(p.read_text())
    if review['input_hash'] != fingerprint(data) or review['video_hash'] != sha(out / 'short.mp4'):
        raise ValueError('Inputs or video changed; render and review again')
    review['approved'] = True
    review['approved_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
    p.write_text(json.dumps(review, indent=2))
    target = ROOT / 'data/reviews'
    target.mkdir(exist_ok=True)
    (target / (data['id'] + '.json')).write_text(json.dumps(review, indent=2))
    print('Approval recorded. Upload short.mp4 through YouTube Studio, then mark-published.')

def telegram(data):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat:
        raise ValueError('Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your shell; never commit them')
    out = ROOT / 'output' / data['id']
    review = json.loads((out / 'review.json').read_text())
    if review['input_hash'] != fingerprint(data) or review['video_hash'] != sha(out / 'short.mp4'):
        raise ValueError('Video changed; render again')
    # Send a review notification. Local video stays local; no cloud media credentials needed.
    body = urllib.parse.urlencode({'chat_id': chat, 'text': f'MomentMeter review ready: {data["id"]}\n{data["title"]}\n{review["duration"]:.1f}s\nReview output/{data["id"]}/short.mp4 then run approve locally.'}).encode()
    req = urllib.request.Request(f'https://api.telegram.org/bot{token}/sendMessage', data=body)
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.load(response)
    if not result.get('ok'):
        raise ValueError('Telegram did not confirm delivery')
    print('Review notification sent')

def main():
    os.chdir(ROOT)
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['check', 'validate', 'render', 'approve', 'notify', 'mark-published', 'sync'])
    parser.add_argument('--job', default='first-short')
    parser.add_argument('--draft', action='store_true')
    parser.add_argument('--url')
    args = parser.parse_args()
    try:
        if args.command == 'check':
            for cmd in ['ffmpeg', 'ffprobe', 'git']:
                print(cmd, 'OK' if shutil.which(cmd) else 'MISSING')
            print('voice:', shutil.which('espeak-ng') or shutil.which('espeak') or 'provide recorded voice_file')
        elif args.command == 'sync':
            # Explicit allowlist prevents accidental credentials/media commits.
            run(['git', 'add', 'data'])
            if run(['git', 'diff', '--cached', '--name-only']).strip():
                run(['git', 'commit', '-m', 'Update MomentMeter production data'])
            run(['git', 'push'])
            print('Production data synced to GitHub')
        else:
            data = load(args.job)
            if args.command == 'validate':
                print(f'Valid {"draft" if args.draft else "production"} job; {validate(data, args.draft)} narration words')
            elif args.command == 'render': render(data)
            elif args.command == 'approve': approve(data)
            elif args.command == 'notify': telegram(data)
            elif args.command == 'mark-published':
                review = json.loads((ROOT / 'output' / data['id'] / 'review.json').read_text())
                if not review.get('approved') or review['input_hash'] != fingerprint(data) or review['video_hash'] != sha(ROOT / 'output' / data['id'] / 'short.mp4'):
                    raise ValueError('Review and approve the current render first')
                if not args.url or not re.fullmatch(r'https://(www\.)?youtube\.com/(shorts/[A-Za-z0-9_-]{11}|watch\?v=[A-Za-z0-9_-]{11})', args.url):
                    raise ValueError('Provide the published YouTube video URL')
                data.update(status='published', published_url=args.url, published_at=dt.datetime.now(dt.timezone.utc).isoformat())
                (ROOT / 'data/jobs' / (args.job + '.json')).write_text(json.dumps(data, indent=2))
                print('Publication recorded')
    except (ValueError, KeyError, FileNotFoundError, subprocess.CalledProcessError) as e:
        parser.exit(1, f'Error: {e}\n')
    except Exception:
        parser.exit(1, 'Operation failed; check connectivity and configuration. Credentials are not logged.\n')

if __name__ == '__main__': main()
