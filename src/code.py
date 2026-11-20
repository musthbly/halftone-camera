import adafruit_pycamera
import displayio
import time

# camera settings
pc = adafruit_pycamera.PyCamera()
pc.resolution = 1 # 320x240

MUTED = True

# bitmap
bmp = displayio.Bitmap(320, 240, 65535)

shapes = ["circle", "square", "line", "star", "heart"]
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
    try:
      pc.capture_into_bitmap(bmp)
      tone(600, 0.1)
      pc.display_message("photo taken", color=0xffffff, scale=2)
      pc.live_preview_mode()
      time.sleep(1)
    except:
      tone(100, 0.1)
      pc.display_message("error", color=0xff0000, scale=2)
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
