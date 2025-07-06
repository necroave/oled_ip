import time
import yaml
import subprocess
import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ssd1306_driver import SSD1306

parser = argparse.ArgumentParser(description="OLED display script")
parser.add_argument("--debug", action="store_true", help="Enable console logging of displayed lines")
parser.add_argument("--config", type=str, default=None, help="Path to config.yaml file")
parser.add_argument("--font", type=str, default=None, help="Path to TTF font file")
args = parser.parse_args()

# Determine base directory — next to binary or next to script
if getattr(sys, "frozen", False):
    base_dir = Path(sys.executable).parent
else:
    base_dir = Path(__file__).parent.resolve()

# Path to config file
config_path = Path(args.config) if args.config else base_dir / "config.yaml"
if not config_path.is_file():
    print(f"Config file not found: {config_path}")
    sys.exit(1)

with open(config_path, "r") as f:
    config = yaml.safe_load(f)

screen_conf = config["screen"]
commands = config["commands"]

# Path to font file
if args.font:
    font_path = Path(args.font)
else:
    font_path = Path(screen_conf.get("font", "DejaVuSans.ttf"))
    if not font_path.is_absolute():
        font_path = base_dir / font_path

if not font_path.is_file():
    print(f"Font file not found: {font_path}")
    sys.exit(1)

# Initialize OLED display with given width, height, i2c bus and address
oled = SSD1306(
    width=screen_conf["width"],
    height=screen_conf["height"],
    i2c_bus=screen_conf.get("i2c_bus", 1),
    address=screen_conf.get("i2c_address", 0x3C),
)

# Load TrueType font with configured size
font = ImageFont.truetype(str(font_path), screen_conf["font_size"])
font_height = screen_conf["font_size"]

# Refresh interval (seconds) to update all commands and displayed data
refresh_time = screen_conf.get("refresh_time", 10)
# Scroll delay (seconds) between each scroll step for long lines
scroll_speed = screen_conf.get("scroll_speed", 0.1)
# Pixels to shift text per scroll step
scroll_step = 1

def run_command(cmd: str) -> str:
    """Execute shell command and return trimmed output or 'error'."""
    try:
        return subprocess.check_output(cmd, shell=True, text=True).strip()
    except subprocess.CalledProcessError:
        return "error"

def text_width(text, font):
    """Calculate pixel width of text with given font."""
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]

max_lines = oled.height // font_height  # Maximum number of text lines on screen

while True:
    lines = []
    # Run each command and prepend static text if any
    for item in commands:
        text = item.get("text", "")
        cmd = item.get("command")
        if cmd:
            result = run_command(cmd)
            lines.append(f"{text}{result}")
        else:
            lines.append(text)

    if args.debug:
        print("=== OLED DISPLAY ===")
        for line in lines:
            print(line)
        print("====================")

    # Initialize scroll positions and max scroll offsets per line
    scroll_pos = [0] * len(lines)
    scroll_max_offsets = []
    for line in lines:
        w = text_width(line, font)
        if w > oled.width:
            scroll_max_offsets.append(w - oled.width + 10)  # Extra gap for smooth scroll
        else:
            scroll_max_offsets.append(0)

    start_time = time.time()
    # Loop for duration of refresh_time to scroll lines and update display
    while time.time() - start_time < refresh_time:
        image = Image.new("1", (oled.width, oled.height))  # Create blank monochrome image
        draw = ImageDraw.Draw(image)

        y = 0
        # Draw each line, scrolling if too wide
        for i, line in enumerate(lines[:max_lines]):
            w = text_width(line, font)
            if w > oled.width:
                offset = -scroll_pos[i]
                draw.text((offset, y), line, font=font, fill=255)
                draw.text((offset + w + 10, y), line, font=font, fill=255)  # Repeat for seamless scroll
            else:
                draw.text((0, y), line, font=font, fill=255)
            y += font_height

        oled.image(image)  # Send image buffer to OLED
        oled.display()     # Update OLED screen

        time.sleep(scroll_speed)  # Wait between scroll steps

        # Update scroll positions for lines that need scrolling
        for i in range(len(lines)):
            if scroll_max_offsets[i] > 0:
                scroll_pos[i] += scroll_step
                if scroll_pos[i] > scroll_max_offsets[i]:
                    scroll_pos[i] = 0  # Reset scroll to start when max reached
