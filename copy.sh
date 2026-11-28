#!/bin/zsh
# aseprite bmp format doesn't work - imagemagick convert instead
mogrify -format bmp src/*.png
cp -R src/*.{py,bmp} /Volumes/CIRCUITPY
