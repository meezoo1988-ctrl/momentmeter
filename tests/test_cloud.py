import unittest
import cloud

class DownloadBoundary(unittest.TestCase):
    def test_rejects_external_and_local_endpoints(self):
        for url in ('http://videos.pexels.com/x', 'https://localhost/x', 'https://videos.pexels.com.evil.example/x', 'https://user:password@videos.pexels.com/x', 'https://videos.pexels.com:8443/x'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                cloud.media_url(url)

    def test_allows_verified_media_host(self):
        self.assertEqual(cloud.media_url('https://videos.pexels.com/video-files/a.mp4'), 'https://videos.pexels.com/video-files/a.mp4')
