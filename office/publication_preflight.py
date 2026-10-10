#!/usr/bin/env python3
"""Read-only publication gate. Does not upload, authenticate or certify listening."""
import argparse, hashlib, json
from pathlib import Path

def check(log, metadata, qa, digest, date):
    episodes = log.get('episodes', [])
    episode = metadata.get('episode')
    pending = [e for e in episodes if (e.get('sha256') == digest or
               (episode and episode in (e.get('episode'), e.get('episode_id')))) and
               (e.get('published') or e.get('scheduled') or e.get('youtube_video_id') or
                e.get('status') in ('published','scheduled','pending','awaiting_user_approval','upload_uncertain','uploading'))]
    daily = sum((bool(e.get('published') or e.get('youtube_video_id') or e.get('status') == 'published') and
                 e.get('published_date') == date) or
                (bool(e.get('scheduled') or e.get('status') in ('scheduled','pending')) and str(e.get('scheduled_time','')).startswith(date))
                for e in episodes)
    office = str(metadata.get('episode', '')).lower().startswith(('excel-','word-','powerpoint-'))
    checks = {
        'channel': log.get('channel_id') == 'UCdA8nUEGpdWp9jIretnt4qg',
        'not_duplicate_or_uncertain': not pending,
        'daily_capacity': daily < 3,
        'approval': office or metadata.get('explicit_user_approval') is True,
        'not_made_for_kids': metadata.get('made_for_kids') is False,
        'public': metadata.get('privacy') == 'public',
        'title': bool(metadata.get('title')) and len(metadata['title']) <= 100,
        'audited_hash': qa.get('sha256') == digest,
        'mechanical': qa.get('mechanical_pass') is True,
        'editorial': qa.get('editorial_pass') is True,
        'source': qa.get('source_verified') is True,
        'full_visual_review': qa.get('full_visual_review') is True,
        'full_audio_decode': qa.get('full_audio_decode') is True,
        'speech_match': qa.get('speech_match') is True,
        'no_clipping': type(qa.get('clipped_samples')) is int and qa.get('clipped_samples') == 0,
        'cta_tail': float(qa.get('cta_tail_seconds', 0)) >= 1,
    }
    return {'pass': all(checks.values()), 'checks': checks, 'published_today': daily,
            'sha256': digest, 'subjective_listening': qa.get('subjective_listening', False)}

def main():
    p=argparse.ArgumentParser(); p.add_argument('log',type=Path);p.add_argument('video',type=Path)
    p.add_argument('metadata',type=Path);p.add_argument('qa',type=Path);p.add_argument('--date',required=True)
    a=p.parse_args()
    result=check(json.loads(a.log.read_text()),json.loads(a.metadata.read_text()),
                 json.loads(a.qa.read_text()),hashlib.sha256(a.video.read_bytes()).hexdigest(),a.date)
    print(json.dumps(result,indent=2));return 0 if result['pass'] else 1

if __name__=='__main__': raise SystemExit(main())
