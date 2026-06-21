"""Render demo frames (real agent output + real tx) and assemble with the voiceover.

Silent-safe, no music. Captions are byte-for-byte the spoken lines. Frames are
1920x1080 on GitHub-dark. Closes on a real artifact (the on-chain proof), no
synthetic end-card. Narration is macOS `say` (synthetic TTS) — flagged.
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG = (13, 17, 23)
FG = (201, 209, 217)
MUTE = (110, 118, 129)
GREEN = (63, 185, 80)
CYAN = (57, 197, 187)
YELLOW = (210, 153, 34)
WHITE = (240, 246, 252)
A = "video/assets"

MONO = "/System/Library/Fonts/Menlo.ttc"
SANS = "/System/Library/Fonts/Helvetica.ttc"

def font(path, size): return ImageFont.truetype(path, size)

CAPS = [
    "You want an AI agent to trade for you. But would you hand a bot your private keys?",
    "Helmsman never asks you to. It signs every trade itself, through Trust Wallet.",
    "Watch it run one cycle. It reads CoinMarketCap and scores the market regime.",
    "Before it signs, a hard risk layer checks the trade against its own rules.",
    "It pays for live data with x402, signs the swap locally, and sends it to BNB Chain.",
    "Every trade lands on-chain. Here is the confirmed transaction on BscScan.",
    "The keys never left the wallet. Self-custody trader, unattended-safe.",
]

# Real terminal lines (truthful, from the live run + real tx).
TERM = [
    ("$ python -m agent.runner", FG, False),
    ("", FG, False),
    ("[signal]  FG=22 (Fear)   mom7d=+3.4%   mcap24h=+0.52%", CYAN, False),
    ("[regime]  risk-on   score=+0.239", YELLOW, False),
    ("[state]   equity=$12.85   peak=$12.89   drawdown=0.3%", FG, False),
    ("[decide]  propose swap  $1.03  USDT -> ETH", FG, False),
    ("[guard]   ALLOW: per-trade, daily, concentration, slippage, gas OK", GREEN, False),
    ("[x402]    paid CMC for live DEX data   (spend $0.01)", CYAN, False),
    ("[exec]    TWAK signed locally + submitted to BNB Chain", WHITE, False),
    ("[proof]   bscscan.com/tx/0xff1a49c4...938d7cbbf   CONFIRMED", GREEN, True),
]
# how many terminal lines are revealed by each clip index (1-based)
REVEAL = {3: 5, 4: 7, 5: 9, 6: 10}


def caption(draw, text):
    f = font(SANS, 42)
    # wrap to <= ~62 chars
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > 62:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    y = H - 60 - len(lines) * 54
    draw.rectangle([0, y - 30, W, H], fill=(8, 11, 15))
    for ln in lines:
        tw = draw.textlength(ln, font=f)
        draw.text(((W - tw) / 2, y), ln, font=f, fill=WHITE)
        y += 54


def base():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def title_frame(big, sub, cap):
    img, d = base()
    fb, fs = font(SANS, 78), font(SANS, 40)
    d.text(((W - d.textlength("Helmsman", font=font(SANS, 34))) / 2, 150), "Helmsman",
           font=font(SANS, 34), fill=GREEN)
    # wrap big
    words, lines, cur = big.split(), [], ""
    for w in words:
        if d.textlength((cur + " " + w).strip(), font=fb) > W - 240:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    y = (H - len(lines) * 96) / 2 - 40
    for ln in lines:
        d.text(((W - d.textlength(ln, font=fb)) / 2, y), ln, font=fb, fill=WHITE); y += 96
    if sub:
        d.text(((W - d.textlength(sub, font=fs)) / 2, y + 20), sub, font=fs, fill=MUTE)
    caption(d, cap)
    return img


def term_frame(n_lines, cap):
    img, d = base()
    fm = font(MONO, 34)
    d.rectangle([120, 110, W - 120, 150], fill=(22, 27, 34))
    for i, c in enumerate(((237, 106, 94), (245, 191, 79), (98, 197, 84))):
        d.ellipse([150 + i * 34, 122, 168 + i * 34, 140], fill=c)
    d.text((W / 2 - 90, 120), "helmsman — agent", font=font(MONO, 26), fill=MUTE)
    y = 200
    for text, color, bold in TERM[:n_lines]:
        d.text((150, y), text, font=fm, fill=color); y += 52
    caption(d, cap)
    return img


frames = [
    title_frame("Would you hand a trading bot your private keys?", "", CAPS[0]),
    title_frame("It signs every trade itself.", "The keys stay in your wallet.", CAPS[1]),
    term_frame(REVEAL[3], CAPS[2]),
    term_frame(REVEAL[4], CAPS[3]),
    term_frame(REVEAL[5], CAPS[4]),
    term_frame(REVEAL[6], CAPS[5]),
    title_frame("Self-custody trader, unattended-safe.",
                "github.com/Yonkoo11/helmsman   ·   ERC-8004 agent #138851", CAPS[6]),
]
for i, fr in enumerate(frames, 1):
    fr.save(f"{A}/frame_{i}.png")

# Assemble: each segment = image + (0.4s silence + clip + 0.5s tail).
segs = []
for i in range(1, 8):
    wav, seg = f"{A}/clip_{i}.wav", f"{A}/seg_{i}.mp4"
    dur = float(subprocess.run(["ffprobe", "-v", "0", "-show_entries", "format=duration",
                                "-of", "csv=p=0", wav], capture_output=True, text=True).stdout)
    padded = f"{A}/padded_{i}.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-t", "0.4", "-i", "anullsrc=r=48000:cl=stereo",
                    "-i", wav, "-f", "lavfi", "-t", "0.5", "-i", "anullsrc=r=48000:cl=stereo",
                    "-filter_complex", "[0][1][2]concat=n=3:v=0:a=1[a]", "-map", "[a]", padded],
                   capture_output=True)
    total = dur + 0.9
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", f"{A}/frame_{i}.png", "-i", padded,
                    "-c:v", "libx264", "-t", f"{total:.2f}", "-pix_fmt", "yuv420p",
                    "-vf", f"fade=t=in:st=0:d=0.25,fade=t=out:st={total-0.25:.2f}:d=0.25",
                    "-c:a", "aac", "-ar", "48000", "-shortest", seg], capture_output=True)
    segs.append(seg)

with open(f"{A}/concat.txt", "w") as f:
    for s in segs:
        f.write(f"file '{os.path.basename(s)}'\n")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{A}/concat.txt",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart",
                "video/helmsman-demo.mp4"], capture_output=True)
out = subprocess.run(["ffprobe", "-v", "0", "-show_entries", "format=duration", "-of", "csv=p=0",
                      "video/helmsman-demo.mp4"], capture_output=True, text=True).stdout.strip()
print(f"built video/helmsman-demo.mp4  ({float(out):.1f}s)")
