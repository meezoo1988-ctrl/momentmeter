"""Upload a specifically reviewed cloud artifact using user OAuth."""
import argparse
import datetime as dt
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import cloud
import momentmeter as m

def verify(data, video, record, approved_hash, run_id):
    if not re.fullmatch(r'[0-9a-f]{64}', approved_hash):
        raise ValueError('Provide the reviewed video SHA-256')
    if record['video_hash'] != approved_hash or m.sha(video) != approved_hash:
        raise ValueError('The reviewed artifact does not match the recorded video')
    if str(record['workflow_run_id']) != str(run_id):
        raise ValueError('Artifact run ID does not match the recorded run')
    job_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    if record.get('job_hash') != job_hash:
        raise ValueError('Video metadata changed since rendering')

def upload(job, run_id, approved_hash, privacy, made_for_kids):
    data = m.load(job)
    published = m.ROOT / 'data/publications' / (job + '.json')
    if published.exists():
        raise ValueError('This job already has a recorded YouTube upload')
    record = json.loads((m.ROOT / 'data/cloud-runs' / (job + '.json')).read_text())
    video = m.ROOT / 'output' / job / 'short.mp4'
    verify(data, video, record, approved_hash, run_id)
    token = cloud.drive_token()
    headers = {'Authorization': 'Bearer ' + token}
    request = urllib.request.Request('https://www.googleapis.com/youtube/v3/channels?part=id&mine=true', headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        channels = json.load(response)['items']
    if [channel['id'] for channel in channels] != [m.CONFIG['channel_id']]:
        raise ValueError('OAuth grant is not for the configured MomentMeter channel')
    description = data['description'] + '\n\n' + '\n'.join(c.get('author', '') + ' — ' + c['source_url'] for c in data['clips'])
    metadata = {'snippet': {'title': data['title'], 'description': description, 'categoryId': '15', 'defaultLanguage': 'en'}, 'status': {'privacyStatus': privacy, 'selfDeclaredMadeForKids': made_for_kids}}
    request = urllib.request.Request('https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status', data=json.dumps(metadata).encode(), headers={**headers, 'Content-Type': 'application/json', 'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(video.stat().st_size)})
    with urllib.request.urlopen(request, timeout=30) as response:
        location = response.headers['Location']
    parsed = urllib.parse.urlsplit(location)
    if parsed.scheme != 'https' or parsed.hostname != 'www.googleapis.com':
        raise ValueError('Unexpected YouTube upload endpoint')
    if video.stat().st_size > 200 * 1024 * 1024:
        raise ValueError('Review video exceeds this uploader’s 200 MB limit')
    request = urllib.request.Request(location, method='PUT', data=video.read_bytes(), headers={**headers, 'Content-Type': 'video/mp4'})
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.load(response)
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', result['id']):
        raise ValueError('YouTube returned an unexpected video ID; reconcile manually before retry')
    published.parent.mkdir(exist_ok=True)
    published.write_text(json.dumps({'job_id': job, 'video_hash': approved_hash, 'workflow_run_id': run_id, 'youtube_id': result['id'], 'privacy': result['status']['privacyStatus'], 'uploaded_at': dt.datetime.now(dt.timezone.utc).isoformat()}, indent=2) + '\n')
    print('Upload recorded; privacy:', result['status']['privacyStatus'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--job', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--approved-hash', required=True)
    parser.add_argument('--privacy', choices=['private', 'unlisted', 'public'], default='private')
    parser.add_argument('--made-for-kids', choices=['true', 'false'], required=True)
    args = parser.parse_args()
    try:
        upload(args.job, args.run_id, args.approved_hash, args.privacy, args.made_for_kids == 'true')
    except ValueError as error:
        parser.exit(1, str(error) + '\n')
    except urllib.error.HTTPError as error:
        parser.exit(1, f'Google request failed: HTTP {error.code}. Credentials are not logged.\n')
    except Exception as error:
        parser.exit(1, f'Upload failed ({type(error).__name__}); verify Google configuration. If transfer had started, check Studio before retrying.\n')
