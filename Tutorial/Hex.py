def hex_to_rgb(hex):
  rgb = []
  for i in (0, 2, 4):
    decimal = int(hex[i:i+2], 16)
    rgb.append(decimal)

  return tuple(rgb)

# ff0000 – 00ff00 = FE0100
# 16711680 – 65280 = 16646400
SpeedDiff = 4
ColorLine = int((SpeedDiff*16646400)/50)
print(hex(ColorLine))
ColorLine = ColorLine + 65280
print(ColorLine)
print(hex(ColorLine))
if len(hex(ColorLine)[2:])==4:
  ColorLine = hex_to_rgb('00'+hex(ColorLine)[2:])
elif len(hex(ColorLine)[2:])==5:
  ColorLine = hex_to_rgb('0'+hex(ColorLine)[2:])
else:
  ColorLine = hex_to_rgb(hex(ColorLine)[2:])
print(ColorLine)




