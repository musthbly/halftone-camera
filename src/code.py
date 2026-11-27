import adafruit_pycamera
import adafruit_bitmapsaver
import adafruit_display_text
import board
import displayio
import terminalio
import bitmaptools
import bitmapfilter
import math
import os
import time

# camera settings
pc = adafruit_pycamera.PyCamera()
pc.resolution = 0 # 240x240
MUTED = False
SCALE_FACTOR = 2 # halftoned image is scaled up
STATE = "take" # take, view

photos = []
for filename in os.listdir("/sd"):
  if filename.lower().endswith(".bmp") and not filename.startswith("._"):
    photos.append(f"/sd/{filename}")
photos.sort()

display = board.DISPLAY

# bitmap - RGB565_SWAPPED
bmp = displayio.Bitmap(pc.camera.width, pc.camera.height, 65535)
cc = displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565_SWAPPED)

scale_w = pc.camera.width * SCALE_FACTOR
scale_h = pc.camera.height * SCALE_FACTOR
roto_w = math.ceil(scale_w * math.cos(math.pi / 12) + scale_h * math.sin(math.pi / 12))
roto_h = math.ceil(scale_h * math.cos(math.pi / 12) + scale_w * math.sin(math.pi / 12))

bmp_roto = displayio.Bitmap(roto_w, roto_h, 65535)
values_roto = displayio.Bitmap(roto_w, roto_h, 2)
values_cyan = displayio.Bitmap(roto_w, roto_h, 2)
values_magenta = displayio.Bitmap(roto_w, roto_h, 2)
values_yellow = displayio.Bitmap(roto_w, roto_h, 2)
cmy = displayio.Bitmap(scale_w, scale_h, 8)

pal_cmy = displayio.Palette(8)
pal_cmy[0] = 0xf3ead9 # 000 white
pal_cmy[1] = 0xffd000 # 001 yellow
pal_cmy[2] = 0xe90057 # 010 magenta
pal_cmy[3] = 0xd72e00 # 011 red
pal_cmy[4] = 0x00c8b9 # 100 cyan
pal_cmy[5] = 0x58a600 # 101 green
pal_cmy[6] = 0x5300bb # 110 blue
pal_cmy[7] = 0x25151d # 111 black

# divide photo into SCALE_FACTOR * SCALE_FACTOR grid
tile_cmy = displayio.TileGrid(cmy, pixel_shader=pal_cmy, width=1, height=1, tile_width=pc.camera.width, tile_height=pc.camera.height)

group = displayio.Group(y=32)
group.append(tile_cmy)
display.root_group.append(group)

# halftone threshold matrices
halftones = [
  [[9, 8, 7, 6], [10, 1, 0, 5], [11, 2, 3, 4], [12, 13, 14, 15]], # square
  [[15, 13, 9, 3], [12, 8, 1, 4], [7, 0, 5, 10], [2, 6, 11, 14]], # line
  [[0, 1, 3, 6], [2, 4, 7, 10], [5, 8, 11, 13], [9, 12, 14, 15]], # triangle
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
  # convert to cmy: scale based on # of shades
  max_idx = len(halftones[0]) * len(halftones[0][0]) - 1

  # cyan layer: -15° rotation
  bitmaptools.rotozoom(bmp_roto, bitmap, scale = SCALE_FACTOR, angle = -math.pi / 12)
  for x in range(bmp_roto.width):
    for y in range(bmp_roto.height):
      pixel = cc.convert(bmp_roto[x, y])
      r = (pixel & 0b1111100000000000) >> 11
      threshold = halftones[shape][x % 4][y % 4]
      cyan = int(max_idx * (1 - r / 31))
      values_roto[x, y] = int(cyan >= threshold)
  bitmaptools.rotozoom(values_cyan, values_roto, angle = math.pi / 12)

  # magenta layer: +15° rotation
  bitmaptools.rotozoom(bmp_roto, bitmap, scale = SCALE_FACTOR, angle = math.pi / 12)
  for x in range(bmp_roto.width):
    for y in range(bmp_roto.height):
      pixel = cc.convert(bmp_roto[x, y])
      g = (pixel & 0b0000011111100000) >> 5
      threshold = halftones[shape][x % 4][y % 4]
      magenta = int(max_idx * (1 - g / 63))
      values_roto[x, y] = int(magenta >= threshold)
  bitmaptools.rotozoom(values_magenta, values_roto, angle = -math.pi / 12)

  # yellow layer: 0° rotation
  bitmaptools.rotozoom(bmp_roto, bitmap, scale = SCALE_FACTOR)
  for x in range(bmp_roto.width):
    for y in range(bmp_roto.height):
      pixel = cc.convert(bmp_roto[x, y])
      b = pixel & 0b0000000000011111
      threshold = halftones[shape][x % 4][y % 4]
      yellow = int(max_idx * (1 - b / 31))
      values_yellow[x, y] = int(yellow >= threshold)

  # account for margins added to rotated bitmaps
  sx = int((roto_w - scale_w) / 2)
  sy = int((roto_h - scale_h) / 2)

  for x in range(cmy.width):
    for y in range(cmy.height):
      cmy[x, y] = 4 * values_cyan[sx + x, sy + y] + 2 * values_magenta[sx + x, sy + y] + values_yellow[sx + x, sy + y]

def display_message(msg, x=pc.display.width/2, y=pc.display.height/2, bg=0x000000, fg=0xffffff, scale=2):
  text_area = adafruit_display_text.label.Label(terminalio.FONT, text=msg, color=fg, background_color=bg, scale=scale)
  text_area.anchor_point = (0.5, 0.5)
  text_area.anchored_position = (x, y)
  pc.splash.append(text_area)
  pc.display.refresh()
  pc.splash.pop()

# startup
print("Hello World!")
tone(300, 0.3)

while True:
  pc.keys_debounce()

  # sd card
  if pc.card_detect.fell:
    print("sd card removed")
    display_message("unmounting sd card...")
    pc.unmount_sd_card()
    pc.display.refresh()
  if pc.card_detect.rose:
    print("sd card inserted")
    display_message("mounting sd card...")
    pc.mount_sd_card()
    pc.display.refresh()

  if pc.up.fell:
    print("up")
    tone(500, 0.1)
  elif pc.down.fell:
    print("down")
    tone(500, 0.1)
  elif pc.left.fell:
    print("left")
    tone(500, 0.1)
  elif pc.right.fell:
    print("right")
    tone(500, 0.1)
  elif pc.select.fell:
    print("select")
    tone(500, 0.1)
  elif pc.ok.fell:
    print("ok")
    tone(500, 0.1)

  if STATE == "take":
    # preview
    pc.blit(pc.continuous_capture())

    group.hidden = True

    # focus
    if pc.shutter.long_press:
      display_message("focusing...")
      pc.autofocus()

    # take photo
    if pc.shutter.short_count:
      print("taking photo")
      tone(500, 0.1)
      display_message("processing...")
      pc.capture_into_bitmap(bmp)
      pc.led_level = 0
      process(bmp)
      tone(600, 0.1)
      group.hidden = False
      display_message("press [ok]\nto continue")
      STATE = "view"

    if pc.up.fell:
      pc.led_level = cycle(pc.led_level, 4)
    elif pc.down.fell:
      pc.led_level = cycle(pc.led_level, 4, True)
    elif pc.left.fell:
      pc.led_color = cycle(pc.led_color, 7, True)
    elif pc.right.fell:
      pc.led_color = cycle(pc.led_color, 7)
    elif pc.select.fell:
      shape = cycle(shape, len(halftones) - 1)
      display_message("shape: {}".format(shape))
      time.sleep(0.5)
    elif pc.ok.fell:
      # normal / b&w
      pc.effect = toggle(pc.effect, 0, 2)
  elif STATE == "view":
    if pc.ok.fell:
      display_message("saving...")
      # get number: remove /sd/ and .bmp from filename
      file_num = int(photos[-1][4:-4]) + 1
      adafruit_bitmapsaver.save_pixels(f"/sd/{file_num:04}.bmp", cmy, pal_cmy)
      photos.append(f"/sd/{file_num:04}.bmp")
      display_message(f"saved as\n{file_num:04}.bmp")
      time.sleep(0.5)
      STATE = "take"
    # scroll to see full photo
    elif pc.up.fell:
      if tile_cmy[0] >= SCALE_FACTOR:
        tile_cmy[0] -= SCALE_FACTOR
        display.refresh()
    elif pc.down.fell:
      if tile_cmy[0] <= (SCALE_FACTOR ** 2 - SCALE_FACTOR - 1):
        tile_cmy[0] += SCALE_FACTOR
        display.refresh()
    elif pc.left.fell:
      if tile_cmy[0] % SCALE_FACTOR != 0:
        tile_cmy[0] -= 1
        display.refresh()
    elif pc.right.fell:
      if tile_cmy[0] % SCALE_FACTOR != SCALE_FACTOR - 1:
        tile_cmy[0] += 1
        display.refresh()
