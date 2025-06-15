# ssd1306.py — minimal SSD1306 driver for I2C
import time

class SSD1306:
    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = self.height // 8
        self.buffer = [0x00] * (self.width * self.pages)
        self._init_display()

    def _command(self, cmd):
        self.i2c.write_i2c_block_data(self.addr, 0x00, [cmd])

    def _init_display(self):
        cmds = [
            0xAE, 0xD5, 0x80, 0xA8, self.height - 1,
            0xD3, 0x00, 0x40, 0x8D, 0x14,
            0x20, 0x00, 0xA1, 0xC8,
            0xDA, 0x12, 0x81, 0xCF,
            0xD9, 0xF1, 0xDB, 0x40,
            0xA4, 0xA6, 0xAF
        ]
        for cmd in cmds:
            self._command(cmd)
        self.fill(0)
        self.show()

    def fill(self, color):
        fill_byte = 0xFF if color else 0x00
        for i in range(len(self.buffer)):
            self.buffer[i] = fill_byte

    def show(self):
        for page in range(self.pages):
            self._command(0xB0 + page)  # Set page start address
            self._command(0x00)         # Set lower column address
            self._command(0x10)         # Set higher column address

            start = self.width * page
            end = start + self.width
            line = self.buffer[start:end]

            # Write 128 bytes in chunks of max 32 bytes
            for i in range(0, len(line), 32):
                chunk = line[i:i+32]
                self.i2c.write_i2c_block_data(self.addr, 0x40, chunk)

    def image(self, img):
        pix = img.load()
        for y in range(self.height):
            for x in range(self.width):
                if pix[x, y]:
                    self.buffer[x + (y // 8) * self.width] |= (1 << (y % 8))
                else:
                    self.buffer[x + (y // 8) * self.width] &= ~(1 << (y % 8))
