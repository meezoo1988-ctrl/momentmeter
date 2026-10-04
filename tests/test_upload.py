import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import youtube_upload as y

class ReviewGate(unittest.TestCase):
    def test_changed_video_and_metadata_are_rejected(self):
        data = {'id': 'test'}
        with tempfile.TemporaryDirectory() as folder:
            video = Path(folder) / 'video.mp4'
            video.write_bytes(b'reviewed video')
            digest = y.m.sha(video)
            record = {'video_hash': digest, 'workflow_run_id': '123', 'job_hash': hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()}
            y.verify(data, video, record, digest, '123')
            with self.assertRaises(ValueError): y.verify(data, video, record, digest, '124')
            with self.assertRaises(ValueError): y.verify({'id': 'changed'}, video, record, digest, '123')
            video.write_bytes(b'changed video')
            with self.assertRaises(ValueError): y.verify(data, video, record, digest, '123')
