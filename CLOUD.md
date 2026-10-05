# MomentMeter cloud operation

No Windows machine is required. GitHub Actions installs FFmpeg and espeak-ng,
downloads the licensed sources listed in a ready job, creates a 1080×1920 Short,
and saves a review artifact for 30 days. Only the finished edit and review metadata
are saved as artifacts; raw stock footage is not committed to the public repo.

The workflow runs at 12:00 UTC / 15:00 Riyadh daily, on manual dispatch, and when
its initial configuration is pushed. It processes at most one new ready job per
UTC day. Each job is rendered once, with a persistent record in data/cloud-runs.
An empty queue produces no video. This is a curated queue, not an unlimited
automated content discovery service. Rendering is not publication approval.

## Google Drive delivery

Optional repository secrets: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
GOOGLE_REFRESH_TOKEN. Repository variable: DRIVE_FOLDER_ID.
Use a user OAuth grant with Drive API enabled and the drive.file scope; a folder
must be accessible to that app. Credentials belong only in Actions secrets.
An app-specific destination folder is recommended. No sharing permissions are
changed by the uploader. Without the folder variable, delivery uses the review
artifact. If configured OAuth fails, the run fails instead of claiming delivery.
Connecting Drive to ChatGPT does not automatically authorize the GitHub runner.

## Reviewed YouTube uploads

The Upload a reviewed Short workflow is manual-dispatch only. Select the exact
production run, job, reviewed video SHA-256, audience classification, and privacy.
It verifies the file against the committed render record, checks that metadata
has not changed, and verifies the OAuth channel ID before uploading. It defaults
to private and records the returned privacy, not merely the requested value.
The same Google secrets require youtube.upload and youtube.readonly scopes and
YouTube Data API enabled. A browser login or API key alone cannot grant uploading.
The uploader is implemented and unit-tested, but no authenticated upload has
been tested or completed. New unaudited API projects may be restricted to private
uploads: https://developers.google.com/youtube/v3/docs/videos/insert.
If upload succeeds but its record cannot be committed, reconcile in Studio
before retrying to prevent a duplicate upload.

For privately stored source clips, set drive_file_id on a clip. The runner uses
the OAuth account to download it instead of its public download_url. The app
must have access to the selected file; drive.file does not expose arbitrary files
already in your Drive. Source rights fields remain required. Drive connection
in ChatGPT and runner OAuth are separate grants.

## Current first video

pets-001 uses five Pexels source pages, their displayed free-download URLs, and
original English commentary. Source license was checked on 2026-10-04:
https://www.pexels.com/license/. Final framing and narration need visual review.
The speech engine is free but synthetic; this first run tests production quality.
The first two hosted production attempts failed at source rank 5 with HTTP 403.
On 2026-10-05, all five sources downloaded and a local review render completed:
29.776 seconds, H.264 1080x1920, AAC, 24,255,126 bytes. Sample frames were visually
checked; complete motion/audio review and publication are still pending.
Public source requests now identify the application as MomentMeter/1.0; a real
urllib range request succeeded with this header. Hosted-run behavior is not yet
retested. The job stays blocked to prevent an unverified hosted rerun.
Drive plugin installation is confirmed, but file actions are not exposed to this
session. No Drive upload or YouTube upload was completed.
