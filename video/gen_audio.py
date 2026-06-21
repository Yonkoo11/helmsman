"""Generate the demo voiceover via ElevenLabs (Brian). Key from env, never logged."""
import os, subprocess, sys, requests

VOICE = "nPczCjzI2devNBz1zQrb"  # Brian
CLIPS = [
    "You want an AI agent to trade for you. But would you hand a bot your private keys?",
    "Helmsman never asks you to. It signs every trade itself, through Trust Wallet.",
    "Watch it run one cycle. It reads CoinMarketCap and scores the market regime.",
    "Before it signs, a hard risk layer checks the trade against its own rules.",
    "It pays for live data with x402, signs the swap locally, and sends it to BNB Chain.",
    "Every trade lands on-chain. Here is the confirmed transaction on BscScan.",
    "The keys never left the wallet. Self-custody trader, unattended-safe.",
]
key = os.getenv("ELEVENLABS_API_KEY")
if not key:
    sys.exit("no ELEVENLABS_API_KEY")
os.makedirs("video/assets", exist_ok=True)
for i, text in enumerate(CLIPS, 1):
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}",
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        json={"text": text, "model_id": "eleven_turbo_v2_5",
              "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": 0.95}},
        timeout=60,
    )
    if r.status_code != 200:
        sys.exit(f"clip {i} failed {r.status_code}: {r.text[:160]}")
    mp3 = f"video/assets/clip_{i}.mp3"
    open(mp3, "wb").write(r.content)
    # normalize to 48kHz wav (QuickTime-safe)
    subprocess.run(["ffmpeg", "-y", "-i", mp3, "-ar", "48000", "-ac", "2",
                    f"video/assets/clip_{i}.wav"], capture_output=True)
    dur = subprocess.run(["ffprobe", "-v", "0", "-show_entries", "format=duration",
                          "-of", "csv=p=0", f"video/assets/clip_{i}.wav"],
                         capture_output=True, text=True).stdout.strip()
    print(f"clip {i}: {float(dur):.1f}s  \"{text[:40]}...\"")
print("audio done")
