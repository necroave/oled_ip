from smbus2 import SMBus
from PIL import Image

# SSD1306 Command constants
SET_CONTRAST = 0x81
DISPLAY_ALL_ON_RESUME = 0xA4
DISPLAY_ALL_ON = 0xA5
NORMAL_DISPLAY = 0xA6
INVERT_DISPLAY = 0xA7
DISPLAY_OFF = 0xAE
DISPLAY_ON = 0xAF
SET_DISPLAY_OFFSET = 0xD3
SET_COM_PINS = 0xDA
SET_VCOM_DETECT = 0xDB
SET_DISPLAY_CLOCK_DIV = 0xD5
SET_PRECHARGE = 0xD9
SET_MULTIPLEX = 0xA8
SET_LOW_COLUMN = 0x00
SET_HIGH_COLUMN = 0x10
SET_START_LINE = 0x40
MEMORY_MODE = 0x20
COLUMN_ADDR = 0x21
PAGE_ADDR = 0x22
COM_SCAN_INC = 0xC0
COM_SCAN_DEC = 0xC8
SEG_REMAP = 0xA0
CHARGE_PUMP = 0x8D
EXTERNAL_VCC = 0x1
SWITCH_CAP_VCC = 0x2

class SSD1306:
    def __init__(self, width, height, i2c_bus=1, address=0x3C):
        self.width = width
        self.height = height
        self.pages = height // 8
        self.address = address
        self.bus = SMBus(i2c_bus)

        self.buffer = [0x00] * (self.width * self.pages)

        self._init_display()

    def _command(self, cmd):
        self.bus.write_byte_data(self.address, 0x00, cmd)

    def _data(self, data):
        # Send data in chunks to avoid overflows
        for i in range(0, len(data), 16):
            self.bus.write_i2c_block_data(self.address, 0x40, data[i:i+16])

    def _init_display(self):
        self._command(DISPLAY_OFF)
        self._command(SET_DISPLAY_CLOCK_DIV)
        self._command(0x80)
        self._command(SET_MULTIPLEX)
        self._command(self.height - 1)
        self._command(SET_DISPLAY_OFFSET)
        self._command(0x00)
        self._command(SET_START_LINE | 0x00)
        self._command(CHARGE_PUMP)
        self._command(0x14)
        self._command(MEMORY_MODE)
        self._command(0x00)
        self._command(SEG_REMAP | 0x1)
        self._command(COM_SCAN_DEC)
        self._command(SET_COM_PINS)
        self._command(0x12)
        self._command(SET_CONTRAST)
        self._command(0xCF)
        self._command(SET_PRECHARGE)
        self._command(0xF1)
        self._command(SET_VCOM_DETECT)
        self._command(0x40)
        self._command(DISPLAY_ALL_ON_RESUME)
        self._command(NORMAL_DISPLAY)
        self._command(DISPLAY_ON)

    def clear(self):
        self.buffer = [0x00] * (self.width * self.pages)
        self.display()

    def image(self, image: Image.Image):
        """Convert Pillow image to display buffer"""
        if image.mode != '1':
            raise ValueError("Image must be in mode '1'")
        pixels = image.load()

        for page in range(self.pages):
            for x in range(self.width):
                byte = 0
                for bit in range(8):
                    y = page * 8 + bit
                    if y >= self.height:
                        continue
                    if pixels[x, y]:
                        byte |= (1 << bit)
                self.buffer[page * self.width + x] = byte

    def display(self):
        self._command(COLUMN_ADDR)
        self._command(0)
        self._command(self.width - 1)
        self._command(PAGE_ADDR)
        self._command(0)
        self._command(self.pages - 1)
        self._data(self.buffer)
