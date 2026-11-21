import adafruit_pycamera
import board
import displayio
import bitmaptools
import bitmapfilter
import time

# camera settings
pc = adafruit_pycamera.PyCamera()
pc.resolution = 0 # 240x240

MUTED = False
SCALE_FACTOR = 2 # halftoned image is scaled up

display = board.DISPLAY

# bitmap - RGB565
bmp = displayio.Bitmap(display.width, display.height, 65535)
cmy = displayio.Bitmap(display.width * SCALE_FACTOR, display.height * SCALE_FACTOR, 8)

pal_cmy = displayio.Palette(8)
pal_cmy[0] = 0xcccccc # 000 white
pal_cmy[1] = 0xcccc33 # 001 yellow
pal_cmy[2] = 0xcc33cc # 010 magenta
pal_cmy[3] = 0xcc3333 # 011 red
pal_cmy[4] = 0x33cccc # 100 cyan
pal_cmy[5] = 0x33cc33 # 101 green
pal_cmy[6] = 0x3333cc # 110 blue
pal_cmy[7] = 0x333333 # 111 black

tile_cmy = displayio.TileGrid(cmy, pixel_shader=pal_cmy)
group = displayio.Group(y = 32)
group.append(tile_cmy)

display.root_group.append(group)

# halftone shapes, light to dark (0:bg, 1:fg)
halftones = [
  # 0 = square
  [[0, 0, 0, 0,
    0, 0, 0, 0,
    0, 0, 0, 0,
    0, 0, 0, 0],

   [0, 0, 0, 0,
    0, 1, 1, 0,
    0, 1, 1, 0,
    0, 0, 0, 0],

   [0, 1, 1, 0,
    1, 1, 1, 1,
    1, 1, 1, 1,
    0, 1, 1, 0],

   [1, 1, 1, 1,
    1, 1, 1, 1,
    1, 1, 1, 1,
    1, 1, 1, 1]],

  # 1 = line
  [[0, 0, 0, 0,
    0, 0, 0, 0,
    0, 0, 0, 0,
    0, 0, 0, 0],

   [0, 0, 0, 1,
    0, 0, 1, 0,
    0, 1, 0, 0,
    1, 0, 0, 0],

   [0, 0, 1, 1,
    0, 1, 1, 1,
    1, 1, 1, 0,
    1, 1, 0, 0],

   [1, 1, 1, 1,
    1, 1, 1, 1,
    1, 1, 1, 1,
    1, 1, 1, 1]]
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
  # halftone dimensions
  sz = int(len(halftones[0][0]) ** 0.5)
  for x in range(bitmap.width / sz * SCALE_FACTOR):
    for y in range(bitmap.height / sz * SCALE_FACTOR):
      # top left coord of 4x4 square from original bitmap
      rx = int(sz * x / SCALE_FACTOR)
      ry = int(sz * y / SCALE_FACTOR)
      total = 0
      pixel = bitmap[rx, ry]
      # 16 bit rgb - 0bRRRRRGGGGGGBBBBB (5R, 6G, 5B)
      r = (pixel & 0b1111100000000000) >> 11
      g = (pixel & 0b0000011111100000) >> 5
      b = pixel & 0b0000000000011111
      # convert to cmy: scale based on # of shades
      max_idx = len(halftones[0]) - 1
      c = int(max_idx * (1 - r / 31))
      m = int(max_idx * (1 - g / 63))
      y = int(max_idx * (1 - b / 31))

      square = [4 * vc + 2 * vm + 1 * vy for vc, vm, vy in zip(halftones[shape][c], halftones[shape][m], halftones[shape][y])]
      bitmaptools.arrayblit(cmy, bytes(square), rx, ry, int(rx + sz / SCALE_FACTOR), int(ry + sz / SCALE_FACTOR))
      print(square)
      print("({}, {}): {}; rgb({}, {}, {}); cmy({}, {}, {})".format(x, y, pixel, r, g, b, c, m, y))

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
    time.sleep(3)

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
    shape = cycle(shape, len(halftones) - 1)
  elif pc.ok.fell:
    print("ok")
    tone(500, 0.1)
    # normal / b&w
    pc.effect = toggle(pc.effect, 0, 2)
