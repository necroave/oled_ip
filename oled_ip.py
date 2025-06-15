import socket
import fcntl
import struct
import psutil
import time
import yaml
import subprocess
import os
import sys
from smbus2 import SMBus
from ssd1306 import SSD1306
from PIL import Image, ImageDraw, ImageFont

# path detection
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# path to config and font
config_path = os.path.join(base_path, "config.yaml")
font_path_default = os.path.join(base_path, "DejaVuSans.ttf")

# load config
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

# get data
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip = fcntl.ioctl(
            s.fileno(),
            0x8915,
            struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24]
        return socket.inet_ntoa(ip)
    except OSError:
        return "No IP"

def get_cpu_load():
    return psutil.cpu_percent(interval=0.5)

def get_disk_usage(path):
    usage = psutil.disk_usage(path)
    used = usage.used / (1024 ** 3)
    free = usage.free / (1024 ** 3)
    return used, free

def get_temp_from_sensors(chip_name, feature_label):
    try:
        output = subprocess.check_output(['sensors'], encoding='utf-8')
        lines = output.splitlines()
        in_chip = False
        for line in lines:
            if line.strip().startswith(chip_name):
                in_chip = True
                continue
            if in_chip:
                if line.strip() == "":
                    break
                if feature_label in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith("+") and part.endswith("°C"):
                            return float(part[1:-2])
    except Exception as e:
        print(f"sensors error: {e}")
    return None

# temp parameters from config
temp_config = config.get("temp", {})
chip_name = temp_config.get("chip_name", "")
feature_label = temp_config.get("feature_label", "temp1")

min_temp = temp_config.get("min_temp", 30)
max_temp = temp_config.get("max_temp", 100)
min_bar_height = temp_config.get("min_bar_height", 1)
max_bar_height = temp_config.get("max_bar_height", 6)
bar_width = temp_config.get("bar_width", 2)
bar_spacing = temp_config.get("bar_spacing", 1)
font_size = temp_config.get("font_size", 10)
font_path = temp_config.get("font_path", font_path_default)

graph_x = temp_config.get("graph_x", 60)
graph_y_offset = temp_config.get("graph_y_offset", 4)
graph_height = temp_config.get("graph_height", 6)
graph_width = temp_config.get("graph_width", 50)

num_bars = graph_width // (bar_width + bar_spacing)

# init oled and font
i2c = SMBus(config["i2c_bus"])
oled = SSD1306(128, 64, i2c, addr=config["i2c_addr"])
font = ImageFont.truetype(font_path, font_size)

temp_history = [0] * num_bars

while True:
    ip = get_ip_address(config["net_interface"])
    cpu = get_cpu_load()
    used, free = get_disk_usage(config["disk_path"])
    temp = get_temp_from_sensors(chip_name, feature_label)

    if temp is not None:
        temp_history.append(temp)
    else:
        temp_history.append(0)
    if len(temp_history) > num_bars:
        temp_history.pop(0)

    image = Image.new("1", (128, 64))
    draw = ImageDraw.Draw(image)

    # text output
    draw.text((0, 0),  f"{config['net_interface']}: {ip}", font=font, fill=255)
    draw.text((0, 14), f"CPU: {cpu:.1f}%", font=font, fill=255)
    draw.text((0, 28), f"Disk: {used:.0f}G u {free:.0f}G f", font=font, fill=255)

    temp_x = 0
    temp_y = 42
    if temp is not None:
        draw.text((temp_x, temp_y), f"Temp: {temp:.1f}C", font=font, fill=255)

        # temperature chart with history
        for i, t in enumerate(temp_history):
            if t < min_temp:
                bar_height = 0
            else:
                scale = (t - min_temp) / (max_temp - min_temp)
                if scale > 1:
                    scale = 1
                bar_height = int(scale * max_bar_height)
                if 0 < bar_height < min_bar_height:
                    bar_height = min_bar_height
            if bar_height > 0:
                x0 = graph_x + i * (bar_width + bar_spacing)
                y0 = temp_y + graph_y_offset + graph_height - bar_height
                x1 = x0 + bar_width - 1
                y1 = temp_y + graph_y_offset + graph_height
                draw.rectangle([x0, y0, x1, y1], fill=255)
    else:
        draw.text((temp_x, temp_y), "Temp: N/A", font=font, fill=255)

    oled.fill(0)
    oled.image(image)
    oled.show()

    time.sleep(config.get("update_interval", 5))
