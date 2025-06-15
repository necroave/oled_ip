# OLED IP & System Monitor

A Python script to display system information on an SSD1306 OLED display via I2C.  
Shows IP address, CPU load, disk usage, CPU temperature with a simple historical temperature graph.

---

## Features

- Displays IP address of a specified network interface  
- Shows current CPU usage (%)  
- Displays disk usage (used and free space in GB)  
- Reads CPU temperature using `lm-sensors` (configurable sensor name and label)  
- Draws a historical temperature bar graph  
- Supports configuration via external `config.yaml` file  
- Loads font and config from the same directory (works with PyInstaller-built binaries)  
- Auto updates every configurable number of seconds  

---

## Requirements

- Python 3  
- [psutil](https://pypi.org/project/psutil/)  
- [PyYAML](https://pypi.org/project/PyYAML/)  
- [smbus2](https://pypi.org/project/smbus2/)  
- [Pillow](https://pypi.org/project/Pillow/)  
- `lm-sensors` installed and configured on the system  
- SSD1306 OLED display connected via I2C  

---

## Installation

```bash
pip install psutil PyYAML smbus2 Pillow
sudo apt install lm-sensors
```

---
## Usage
- Prepare your config.yaml file (see example below) and place it in the same directory as the script or executable.
- Place the font file (e.g. DejaVuSans.ttf) in the same directory or adjust the path in the config.
- Run the script directly:

```bash
python oled_ip.py
```
Or run the PyInstaller-compiled binary:
```bash
./oled_ip
```
---

## Example config.yaml
```yaml
net_interface: eth0
disk_path: /
i2c_bus: 1
i2c_addr: 0x3C
update_interval: 5

temp:
  chip_name: cpu_thermal-virtual-0
  feature_label: temp1
  min_temp: 30
  max_temp: 100
  min_bar_height: 1
  max_bar_height: 6
  bar_width: 2
  bar_spacing: 1
  font_size: 10
  font_path: DejaVuSans.ttf
  graph_x: 60
  graph_y_offset: 4
  graph_height: 6
  graph_width: 50

```
---

## Notes
- Adjust chip_name and feature_label according to the output of sensors command to match your hardware sensors correctly.
- The temperature graph displays a historical temperature trend with bar heights scaled between min_temp and max_temp.
- Ensure the I2C bus number and address correspond to your OLED hardware configuration.
- The script supports both running as a normal Python script and as a PyInstaller-built executable, automatically locating config and font relative to the executable location.
- You can customize update intervals and graphical parameters via the config file for your needs.
