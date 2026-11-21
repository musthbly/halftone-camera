import adafruit_pycamera
import displayio
import bitmaptools
import time

# camera settings
pc = adafruit_pycamera.PyCamera()
pc.resolution = 1 # 320x240

MUTED = False

# bitmap - 0bRRRRRGGGGGGBBBBB
bmp = displayio.Bitmap(320, 240, 65535)
cyan = displayio.Bitmap(320, 240, 2)
magenta = displayio.Bitmap(320, 240, 2)
yellow = displayio.Bitmap(320, 240, 2)

# halftone shapes, light to dark (0:bg, 1:fg)
halftones = [
  # 0 = circle
  [
    bytes([
      0, 0, 0, 0, 0,
      0, 0, 0, 0, 0,
      0, 0, 0, 0, 0,
      0, 0, 0, 0, 0,
      0, 0, 0, 0, 0
    ]),
    bytes([
      0, 0, 0, 0, 0,
      0, 0, 0, 0, 0,
      0, 0, 1, 0, 0,
      0, 0, 0, 0, 0,
      0, 0, 0, 0, 0
    ]),
    bytes([
      0, 0, 0, 0, 0,
      0, 1, 1, 0, 0,
      0, 1, 1, 0, 0,
      0, 0, 0, 0, 0,
      0, 0, 0, 0, 0
    ]),
    bytes([
      0, 0, 0, 0, 0,
      0, 1, 1, 0, 0,
      0, 1, 1, 1, 0,
      0, 0, 1, 1, 0,
      0, 0, 0, 0, 0
    ]),
    bytes([
      0, 0, 0, 0, 0,
      0, 1, 1, 1, 0,
      0, 1, 1, 1, 0,
      0, 1, 1, 1, 0,
      0, 0, 0, 0, 0
    ]),
    bytes([
      0, 1, 1, 0, 0,
      1, 1, 1, 1, 0,
      1, 1, 1, 1, 0,
      0, 1, 1, 0, 0,
      0, 0, 0, 0, 0
    ]),
    bytes([
      0, 0, 1, 1, 0,
      0, 1, 1, 1, 1,
      1, 1, 1, 1, 1,
      1, 1, 1, 1, 1,
      0, 1, 1, 1, 1
    ]),
    bytes([
      1, 1, 1, 1, 1,
      1, 1, 1, 1, 1,
      1, 1, 1, 1, 1,
      1, 1, 1, 1, 1,
      1, 1, 1, 1, 1
    ])
  ],
  # 1 = line
  [
    bytes([
      0, 0, 0, 0, 0,
      0, 0, 0, 0, 0,
      0, 0, 0, 0, 0,
      0, 0, 0, 0, 0,
      0, 0, 0, 0, 0
    ]),
    bytes([
      0, 0, 0, 0, 0,
      0, 0, 0, 1, 0,
      0, 0, 1, 0, 0,
      0, 0, 0, 0, 0,
      0, 0, 0, 0, 0
    ]),
    bytes([
      0, 0, 0, 0, 0,
      0, 0, 0, 1, 0,
      0, 0, 1, 1, 0,
      0, 1, 1, 0, 0,
      0, 0, 0, 0, 0
    ]),
    bytes([
      0, 0, 0, 0, 0,
      0, 0, 1, 1, 0,
      0, 1, 1, 1, 0,
      0, 1, 1, 0, 0,
      0, 0, 0, 0, 0
    ]),
    bytes([
      0, 0, 0, 1, 1,
      0, 0, 1, 1, 1,
      0, 1, 1, 1, 0,
      0, 1, 1, 0, 0,
      0, 0, 0, 0, 0
    ]),
    bytes([
      0, 0, 1, 1, 1,
      0, 1, 1, 1, 1,
      0, 1, 1, 1, 0,
      1, 1, 1, 1, 0,
      1, 1, 1, 0, 0
    ]),
    bytes([
      0, 1, 1, 1, 1,
      0, 1, 1, 1, 1,
      1, 1, 1, 1, 1,
      1, 1, 1, 1, 0,
      1, 1, 1, 1, 0
    ]),
    bytes([
      1, 1, 1, 1, 1,
      1, 1, 1, 1, 1,
      1, 1, 1, 1, 1,
      1, 1, 1, 1, 1,
      1, 1, 1, 1, 1
    ])
  ]
]
shape = 0

def cycle(cur, max, reverse = False):
  if reverse:
    if cur == 0:
      return max
    else:
      return cur - 1
  else:
    if cur == max:
      return 0
    else:
      return cur + 1

def toggle(cur, a, b):
  if cur == a:
    return b
  else:
    return a

def tone(freq, dur):
  if not MUTED:
    pc.tone(freq, dur)

def process(bitmap):
  for x in range(bitmap.width / 5):
    for y in range(bitmap.height / 5):
      # top left coord of 5x5 square from original bitmap
      rx = 5 * x
      ry = 5 * y
      total = 0
      for sx in range(rx, rx + 5):
        for sy in range(ry, ry + 5):
          total += bitmap[sx, sy]
      avg = int(total / 25)
      # 16 bit rgb - 0bRRRRRGGGGGGBBBBB (5R, 6G, 5B)
      r = (avg & 0b1111100000000000) >> 11
      g = (avg & 0b0000011111100000) >> 5
      b = avg & 0b0000000000011111
      # convert to cmy: scale based on # of shades
      SCALE = len(halftones[0]) - 1
      c = int(SCALE * (1 - r / (2 ** 5)))
      m = int(SCALE * (1 - g / (2 ** 6)))
      y = int(SCALE * (1 - b / (2 ** 5)))
      bitmaptools.arrayblit(cyan, halftones[shape][c], rx, ry, rx + 5, ry + 5)
      bitmaptools.arrayblit(magenta, halftones[shape][m], rx, ry, rx + 5, ry + 5)
      bitmaptools.arrayblit(yellow, halftones[shape][y], rx, ry, rx + 5, ry + 5)
      print("({}, {}): {}; rgb({}, {}, {}); cmy({}, {}, {})".format(x, y, avg, r, g, b, c, m, y))

# startup
print("Hello World!")
tone(300, 0.3)

while True:
  # preview
  pc.blit(pc.continuous_capture())

  pc.keys_debounce()

  # focus
  if pc.shutter.long_press:
    pc.display_message("focusing...", color=0xffffff, scale=2)
    pc.autofocus()

  # take photo
  if pc.shutter.short_count:
    print("taking photo")
    tone(500, 0.1)
    pc.display_message("processing...", color=0xffffff, scale=2)
    pc.capture_into_bitmap(bmp)
    process(bmp)
    tone(600, 0.1)
    pc.display_message("photo taken", color=0xffffff, scale=2)
    pc.live_preview_mode()
    time.sleep(1)

  if pc.up.fell:
    print("up")
    tone(500, 0.1)
    pc.led_level = cycle(pc.led_level, 4)
  elif pc.down.fell:
    print("down")
    tone(500, 0.1)
    pc.led_level = cycle(pc.led_level, 4, True)
  elif pc.left.fell:
    print("left")
    tone(500, 0.1)
    pc.led_color = cycle(pc.led_color, 7, True)
  elif pc.right.fell:
    print("right")
    tone(500, 0.1)
    pc.led_color = cycle(pc.led_color, 7)
  elif pc.select.fell:
    print("select")
    tone(500, 0.1)
    shape = cycle(shape, len(shapes) - 1)
    print("halftone shape: " + shapes[shape])
  elif pc.ok.fell:
    print("ok")
    tone(500, 0.1)
    # normal / b&w
    pc.effect = toggle(pc.effect, 0, 2)
