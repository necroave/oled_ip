import time
import yaml
import subprocess
import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ssd1306_driver import SSD1306  # должен лежать рядом

parser = argparse.ArgumentParser(description="OLED display script")
parser.add_argument("--debug", action="store_true", help="Enable console logging of displayed lines")
parser.add_argument("--config", type=str, help="Path to config.yaml")
parser.add_argument("--font", type=str, help="Path to TTF font")
args = parser.parse_args()

# detect base_dir
if getattr(sys, "frozen", False):
    base_dir = Path(sys.executable).parent
else:
    base_dir = Path(__file__).parent.resolve()

# path to config.yaml
config_path = Path(args.config) if args.config else base_dir / "config.yaml"
if not config_path.is_file():
    print(f"Config file not found: {config_path}")
    sys.exit(1)

with open(config_path, "r") as f:
    config = yaml.safe_load(f)

screen_conf = config["screen"]
commands = config["commands"]

# path to font
if args.font:
    font_path = Path(args.font)
else:
    font_path = Path(screen_conf.get("font", "DejaVuSans.ttf"))
    if not font_path.is_absolute():
        font_path = base_dir / font_path

if not font_path.is_file():
    print(f"Font file not found: {font_path}")
    sys.exit(1)

# init screen
oled = SSD1306(
    width=screen_conf["width"],
    height=screen_conf["height"],
    i2c_bus=screen_conf.get("i2c_bus", 1),
    address=screen_conf.get("i2c_address", 0x3C),
)

# load font
font = ImageFont.truetype(str(font_path), screen_conf["font_size"])
font_height = screen_conf["font_size"]

# screen parameters
global_refresh_time = screen_conf.get("global_refresh_time", 10)
scroll_speed = screen_conf.get("scroll_speed", 0.1)
scroll_step = 1

def run_command(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, text=True).strip()
    except subprocess.CalledProcessError:
        return "error"

def text_width(text, font):
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]

max_lines = oled.height // font_height

# prepare strings
line_states = []
now = time.time()

for item in commands:
    text = item.get("text", "")
    cmd = item.get("command")
    rt = item.get("refresh_time", global_refresh_time)

    if cmd:
        value = run_command(cmd)
    else:
        value = ""

    line_states.append({
        "text": text,
        "command": cmd,
        "value": value,
        "refresh_time": rt,
        "last_update": now,
    })

# main cycle
while True:
    now = time.time()

    # refresh every string with timeout
    for state in line_states:
        if state["command"] and (now - state["last_update"] >= state["refresh_time"]):
            state["value"] = run_command(state["command"])
            state["last_update"] = now

    # prepare data for strings
    lines = [
        f"{s['text']}{s['value']}" if s["command"] else s["text"]
        for s in line_states
    ]

    if args.debug:
        print("=== OLED DISPLAY ===")
        for line in lines:
            print(line)
        print("====================")

    # scroll: determine string lenght
    scroll_pos = [0] * len(lines)
    scroll_max_offsets = []
    for line in lines:
        w = text_width(line, font)
        if w > oled.width:
            scroll_max_offsets.append(w - oled.width + 10)
        else:
            scroll_max_offsets.append(0)

    # scrolling
    while True:
        now = time.time()
        needs_refresh = False
        for s in line_states:
            if s["command"] and (now - s["last_update"] >= s["refresh_time"]):
                needs_refresh = True
                break
        if needs_refresh:
            break

        # draw
        image = Image.new("1", (oled.width, oled.height))
        draw = ImageDraw.Draw(image)

        y = 0
        for i, line in enumerate(lines[:max_lines]):
            w = text_width(line, font)
            if w > oled.width:
                offset = -scroll_pos[i]
                draw.text((offset, y), line, font=font, fill=255)
                draw.text((offset + w + 10, y), line, font=font, fill=255)
            else:
                draw.text((0, y), line, font=font, fill=255)
            y += font_height

        oled.image(image)
        oled.display()

        time.sleep(scroll_speed)

        # refresh scroll position
        for i in range(len(lines)):
            if scroll_max_offsets[i] > 0:
                scroll_pos[i] += scroll_step
                if scroll_pos[i] > scroll_max_offsets[i]:
                    scroll_pos[i] = 0
