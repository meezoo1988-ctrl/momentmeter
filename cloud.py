"""GitHub-hosted production and optional private Google Drive delivery."""
import argparse
import datetime as dt
import hashlib
import json
import os
import urllib.parse
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
import momentmeter as m

MEDIA_HOSTS = {'videos.pexels.com', 'www.pexels.com'}

def media_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in MEDIA_HOSTS or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Media URL must be HTTPS on an approved Pexels host')
    return url

class MediaRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        media_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

class PrivateRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Private Drive media redirects require explicit review')

def download(clip):
    if clip.get('rights_verified') is not True:
        raise ValueError('Usage rights must be verified before download')
    destination = m.local(clip['file'])
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix('.part')
    if clip.get('drive_file_id'):
        import re
        if not re.fullmatch(r'[A-Za-z0-9_-]+', clip['drive_file_id']):
            raise ValueError('Invalid Drive file ID')
        opener = urllib.request.build_opener(PrivateRedirect())
        request = urllib.request.Request('https://www.googleapis.com/drive/v3/files/' + clip['drive_file_id'] + '?alt=media', headers={'Authorization': 'Bearer ' + drive_token()})
    else:
        opener = urllib.request.build_opener(MediaRedirect())
        request = media_url(clip['download_url'])
    try:
        with opener.open(request, timeout=120) as response, temp.open('wb') as output:
            if not clip.get('drive_file_id'):
                media_url(response.url)
            count = 0
            while block := response.read(1024 * 1024):
                count += len(block)
                if count > 400 * 1024 * 1024:
                    raise ValueError('Source exceeds the 400 MB limit')
                output.write(block)
        m.duration(temp)
        temp.replace(destination)
    finally:
        temp.unlink(missing_ok=True)

def drive_token():
    values = [os.environ.get(key) for key in ('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_REFRESH_TOKEN')]
    if not all(values):
        raise ValueError('Google OAuth secrets are incomplete')
    body = urllib.parse.urlencode(dict(zip(('client_id', 'client_secret', 'refresh_token'), values), grant_type='refresh_token')).encode()
    request = urllib.request.Request('https://oauth2.googleapis.com/token', data=body)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)['access_token']

def drive_upload(video, job):
    folder = os.environ.get('DRIVE_FOLDER_ID')
    if not folder:
        print('Drive is not configured; the review video will remain in the Actions artifact.')
        return None
    token = drive_token()
    metadata = {'name': job + '.mp4', 'parents': [folder], 'appProperties': {'momentmeter_job': job, 'sha256': m.sha(video)}}
    request = urllib.request.Request('https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&fields=id,webViewLink', data=json.dumps(metadata).encode(), headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(video.stat().st_size)})
    with urllib.request.urlopen(request, timeout=30) as response:
        location = response.headers['Location']
    parsed = urllib.parse.urlsplit(location)
    if parsed.scheme != 'https' or parsed.hostname != 'www.googleapis.com':
        raise ValueError('Unexpected Google upload endpoint')
    request = urllib.request.Request(location, method='PUT', data=video.read_bytes(), headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'video/mp4'})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)

def select_job():
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    for record in (m.ROOT / 'data/cloud-runs').glob('*.json'):
        if json.loads(record.read_text())['rendered_at'].startswith(today):
            return None
    for path in sorted((m.ROOT / 'data/jobs').glob('*.json')):
        data = m.load(path.stem)
        if data.get('status') == 'ready' and not (m.ROOT / 'data/cloud-runs' / (data['id'] + '.json')).exists():
            return data
    return None

def produce():
    data = select_job()
    if data is None:
        print('No queued job, or today’s one-video limit has been reached.')
        return
    m.validate(data, draft=True)
    for clip in data['clips']:
        print('Downloading rank', clip['rank'], flush=True)
        download(clip)
    print('Rendering', data['id'], flush=True)
    m.render(data)
    output = m.ROOT / 'output' / data['id']
    review = json.loads((output / 'review.json').read_text())
    review.update(job_hash=hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(), workflow_run_id=os.environ.get('GITHUB_RUN_ID'), artifact_name='review-' + data['id'], drive_file=drive_upload(output / 'short.mp4', data['id']))
    (output / 'review.json').write_text(json.dumps(review, indent=2))
    if os.environ.get('GITHUB_OUTPUT'):
        with Path(os.environ['GITHUB_OUTPUT']).open('a') as stream:
            stream.write('job=' + data['id'] + '\n')

def record(job):
    m.load(job)
    output = m.ROOT / 'output' / job
    review = json.loads((output / 'review.json').read_text())
    if m.sha(output / 'short.mp4') != review['video_hash']:
        raise ValueError('Rendered video changed')
    target = m.ROOT / 'data/cloud-runs'
    target.mkdir(exist_ok=True)
    (target / (job + '.json')).write_text(json.dumps(review, indent=2) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['produce', 'record'])
    parser.add_argument('--job')
    args = parser.parse_args()
    os.chdir(m.ROOT)
    try:
        produce() if args.command == 'produce' else record(args.job)
    except urllib.error.HTTPError as error:
        parser.exit(1, f'Cloud HTTP request failed: status {error.code}. Credentials are not logged.\n')
    except ValueError as error:
        parser.exit(1, f'Validation failed: {error}\n')
    except subprocess.CalledProcessError as error:
        parser.exit(1, 'Media processing failed: ' + error.stderr[-1800:] + '\n')
    except Exception as error:
        parser.exit(1, f'Cloud operation failed ({type(error).__name__}). Credentials are not logged.\n')
