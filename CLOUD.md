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

## YouTube

The current release generates review files and upload text. It does not upload
to YouTube. The channel's browser session is not a reusable server OAuth grant.
Automated uploading needs YouTube Data API authorization separately; an API key
alone cannot upload or change a channel. Review the first real render before
publishing. Public automated publishing is not yet enabled.

## Current first video

pets-001 uses five Pexels source pages, their displayed free-download URLs, and
original English commentary. Source license was checked on 2026-10-04:
https://www.pexels.com/license/. Final framing and narration need visual review.
The speech engine is free but synthetic; this first run tests production quality.
Source availability and the first hosted run still require verification.
