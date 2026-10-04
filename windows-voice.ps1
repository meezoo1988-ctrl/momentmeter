param(
    [Parameter(Mandatory=$true)][string]$TextFile,
    [Parameter(Mandatory=$true)][string]$OutputFile
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $voice = $speaker.GetInstalledVoices() | Where-Object {
        $_.Enabled -and $_.VoiceInfo.Culture.Name -like 'en-*'
    } | Select-Object -First 1
    if (-not $voice) { throw 'Install an English Windows speech voice, or use voice_file recordings.' }
    $speaker.SelectVoice($voice.VoiceInfo.Name)
    $speaker.Rate = 1
    $speaker.SetOutputToWaveFile([IO.Path]::GetFullPath($OutputFile))
    $speaker.Speak([IO.File]::ReadAllText([IO.Path]::GetFullPath($TextFile), [Text.Encoding]::UTF8))
} finally { $speaker.Dispose() }
