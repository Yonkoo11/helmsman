"""Motion demo: the agent appears to RUN live (typing animation), not a slideshow.

Applies our demo lessons: motion over static frames, show the core action rather
than narrate it, real on-chain proof (the actual `twak tx` confirmation) shown in
the real terminal medium, no synthetic marketing hook/close cards, no em-dashes,
no music. The product is a CLI, so the real terminal IS the product UI.
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 24
BG = (13, 17, 23)
FG = (201, 209, 217)
GREY = (110, 118, 129)
GREEN = (63, 185, 80)
CYAN = (57, 197, 187)
YELLOW = (210, 153, 34)
WHITE = (240, 246, 252)
A = "video/assets/motion"
os.makedirs(A, exist_ok=True)
MONO = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 32)
MONOH = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 24)
X0, Y0, LH = 150, 210, 46

# (text, color, kind)  kind: 'type' = typed char-by-char (commands / comments),
#                            'print' = printed instantly (agent output),
#                            'gap'  = blank line.
LINES = [
    ("# would you hand a trading bot your private keys?", GREY, "type"),
    ("# helmsman never asks. it signs every trade itself.", GREY, "type"),
    ("", FG, "gap"),
    ("$ python -m agent.runner", WHITE, "type"),
    ("", FG, "gap"),
    ("[signal]  FG=22 (Fear)   mom7d=+3.4%   mcap24h=+0.52%", CYAN, "print"),
    ("[regime]  risk-on   score=+0.239", YELLOW, "print"),
    ("[state]   equity=$12.85   peak=$12.89   drawdown=0.3%", FG, "print"),
    ("[decide]  propose swap  $1.03  USDT -> ETH", FG, "print"),
    ("[guard]   ALLOW: per-trade, daily, concentration, slippage, gas", GREEN, "print"),
    ("[x402]    paid CMC for live DEX data   (spend $0.01)", CYAN, "print"),
    ("[exec]    TWAK signed locally, submitted to BNB Chain", WHITE, "print"),
    ("[proof]   bscscan.com/tx/0xff1a49c4...938d7cbbf", GREEN, "print"),
    ("", FG, "gap"),
    ("$ twak tx 0xff1a49c4 --chain bsc", WHITE, "type"),
    ("  confirmed: true    failed: false", GREEN, "print"),
    ("", FG, "gap"),
    ("# keys never left the wallet.", GREY, "type"),
    ("# self-custody trader, unattended-safe.", GREEN, "type"),
]

TYPE_CPS = 2          # chars revealed per frame while typing
PRINT_HOLD = 16        # frames a printed line waits before the next
END_HOLD = 80         # frames to hold the final screen


def header(d):
    d.rectangle([120, 120, W - 120, 168], fill=(22, 27, 34))
    for i, c in enumerate(((237, 106, 94), (245, 191, 79), (98, 197, 84))):
        d.ellipse([150 + i * 34, 136, 168 + i * 34, 154], fill=c)
    t = "helmsman : agent"
    d.text((W / 2 - d.textlength(t, font=MONOH) / 2, 134), t, font=MONOH, fill=GREY)


def render(state, cursor_line, cursor_col, blink):
    """state: list of (visible_text, color) lines already shown."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d)
    y = Y0
    for i, (text, color) in enumerate(state):
        d.text((X0, y), text, font=MONO, fill=color)
        if i == cursor_line and blink:
            cx = X0 + d.textlength(text[:cursor_col], font=MONO)
            d.rectangle([cx, y + 4, cx + 14, y + 38], fill=FG)
        y += LH
    return img


frame = 0
shown = []  # committed lines (full)
for text, color, kind in LINES:
    if kind == "gap":
        shown.append(("", FG))
        continue
    if kind == "type":
        for n in range(0, len(text) + 1, TYPE_CPS):
            partial = shown + [(text[:n], color)]
            render(partial, len(shown), n, (frame // 6) % 2 == 0).save(f"{A}/f{frame:04d}.png")
            frame += 1
        shown.append((text, color))
    else:  # print
        shown.append((text, color))
        for _ in range(PRINT_HOLD):
            render(shown, len(shown) - 1, len(text), (frame // 6) % 2 == 0).save(f"{A}/f{frame:04d}.png")
            frame += 1
    # short pause after each committed line
    for _ in range(7):
        render(shown, len(shown) - 1, len(shown[-1][0]), (frame // 6) % 2 == 0).save(f"{A}/f{frame:04d}.png")
        frame += 1

for _ in range(END_HOLD):
    render(shown, len(shown) - 1, len(shown[-1][0]), (frame // 6) % 2 == 0).save(f"{A}/f{frame:04d}.png")
    frame += 1

subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{A}/f%04d.png",
                "-vf", f"fade=t=in:st=0:d=0.4,fade=t=out:st={frame/FPS-0.5:.2f}:d=0.5",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "video/helmsman-demo.mp4"], capture_output=True)
dur = float(subprocess.run(["ffprobe", "-v", "0", "-show_entries", "format=duration",
                            "-of", "csv=p=0", "video/helmsman-demo.mp4"],
                           capture_output=True, text=True).stdout)
print(f"built video/helmsman-demo.mp4  ({dur:.1f}s, {frame} frames)")
