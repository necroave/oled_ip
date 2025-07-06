# OLED Info Display

A configurable Python script for displaying system or custom command output on an SSD1306 OLED screen over I²C.

## Features

- Output any shell command or static text to OLED
- Scrolls long lines horizontally
- Auto-refreshes output at configurable intervals
- External `config.yaml` for display and command settings
- Supports custom TrueType fonts (TTF)
- Optional debug logging to console
- Contains own SSD1306 driver
---

## Requirements

- [Pillow](https://pypi.org/project/Pillow/) >=9.0.0
- [PyYAML](https://pypi.org/project/PyYAML/)  >=6.0
- SSD1306 OLED display connected via I2C  

---
## Usage
- Prepare your config.yaml file (see example below) and place it in the same directory as the script or executable.
- Place the font file (e.g. DejaVuSans.ttf) in the same directory or adjust the path in the config.
- Run the script directly:

```bash
python3 oled_ip.py [--config ./config.yaml] [--font ./DejaVuSans.ttf] [--debug]
```
Or run the PyInstaller pre-compiled binary:
```bash
./oled_ip
```
---

## Configuratioin:
Create a config.yaml file with screen and commands sections.
You can specify global_refresh_timeout for update all strings, or specify refresh_time for every string if needed.
```yaml
screen:
  width: 128            # OLED display width in pixels
  height: 64            # OLED display height in pixels
  font_size: 10         # Font size in points
  font: DejaVuSans.ttf  # Font file name or path to TrueType font
  refresh_time: 1       # Time interval (seconds) to refresh and update all command outputs on screen
  scroll_speed: 1       # Delay (seconds) between each scroll step for lines wider than screen
  scroll_step: 20       # Number of pixels to shift text per scroll step
  i2c_bus: 4            # I2C bus number used for the OLED display
  i2c_address: 0x3c     # I2C address of the OLED display

commands:
  - text: "IP: "
    command: "hostname -I | cut -d' ' -f1"
  - text: "Load: "
    command: "uptime | awk -F'load average:' '{print $2}'"
    refresh_time: 1
  - text: "Static Info"
```

---

## Building binary (optional)
To create a single executable using PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile oled_ip.py
```
Then run:
```bash
./dist/oled_ip --config ./config.yaml --font ./DejaVuSans.ttf
```
