from PIL import Image, ImageDraw
import time
import os
import platform
import usb.util
import usb.core

########################
# Image decoding stuff #
########################

# Bits and pieces (the important decoding stuff, really) borrowed from
# https://github.com/lennartba/gbpinter_dump2image_py/blob/master/dump2img.py
# The original doesn't have a license, so I'll credit the contributers here:
# - lennartba
# - Cabalist / Ryan Jarvis
# - BjornB2
#
# Now behold, jank.

TILES_PER_LINE = 20
TILE_SIZE = 8

def CreateImage(data, params="0100e440"):
    if len(data) == 0:
        print("There's nothing to do. Exiting...")
        exit()

    data = bytes.fromhex(data)
    params = bytes.fromhex(params)

    print(f"{str(len(data))} bytes to print...")

    dump = [data[i:i+16] for i in range(0, len(data), 16)]    # 16 bytes per tile
    print(f"{str(len(dump))} tiles to print...")

    LINES_COUNT = len(dump) // TILES_PER_LINE
    print(f"{LINES_COUNT} lines to print...")

    # Handle margins
    margins = params[1]
    marginTop = (margins>>4) & 0x0f
    marginBottom = margins & 0x0f
    print(f"Margins: {marginTop} line(s) before, {marginBottom} line(s) after")

    # Compute colors from palette parameter
    palette = params[2]
    colours = [palette>>6, (palette>>4)&0b11, (palette>>2)&0b11, palette&0b11]
    colours = [_*0x55 for _ in colours]
    colours = [(_,_,_) for _ in colours]
    print(f"Palette colours: {colours}")

    try:
        img = Image.new(mode='RGB', size=(TILES_PER_LINE * TILE_SIZE, (LINES_COUNT+marginTop+marginBottom) * TILE_SIZE), color=(255,255,255))
        pixels = img.load()
        for h in range(LINES_COUNT):
            for w in range(TILES_PER_LINE):
                tile = dump[(h*TILES_PER_LINE) + w]
                for i in range(TILE_SIZE):
                    for j in range(TILE_SIZE):
                        index = (tile[i * 2] >> (7 - j)) & 0b11
                        pixels[(w * TILE_SIZE) + j, ((h+marginTop) * TILE_SIZE) + i] = colours[index]
        return img
    except IndexError as e:
        print("Provided data doesn't match expected size, " \
              "please double check your hex dump!")
        exit()

def SaveImage(img):
    img_timestamp = time.strftime('%Y%m%d - %H%M%S')
    img.save(f"images/decoded_{img_timestamp}.png")
    print(f"Saved to images/decoded_{img_timestamp}.png!")

def SaveImageRGB(red_img, green_img, blue_img):
    red_img = red_img.convert("L")
    green_img = green_img.convert("L")
    blue_img = blue_img.convert("L")
    rgb_image = Image.merge("RGB", (red_img, green_img, blue_img))
    img_timestamp = time.strftime('%Y%m%d - %H%M%S')
    rgb_image.save(f"images/decoded_rgb_{img_timestamp}.png")
    print(f"Saved to images/decoded_rgb_{img_timestamp}.png!")

#############
# USB stuff #
#############

dev = usb.core.find(idVendor=0xcafe, idProduct=0x4011)

if dev is None:
    print("I could not find your link cable adapter!")
    exit()

reattach = False

if platform.system() != "Windows":
    if dev.is_kernel_driver_active(0):
        try:
            reattach = True
            dev.detach_kernel_driver(0)
            print("Detached kernel driver...")
        except usb.core.USBError as e:
            print("Could not detach kernel driver :(")
            exit()
    else:
        print("No kernel driver attached...")

dev.reset()
dev.set_configuration()

cfg = dev.get_active_configuration()

intf = usb.util.find_descriptor(
    cfg,
    bInterfaceClass = 0xff,
    iInterface = 0x5
)

if intf is None:
    print("Could not find the correct interface. If on Windows, ensure you're" \
    " using the correct driver.")
    exit()

epIn = usb.util.find_descriptor(
    intf,
    custom_match = \
    lambda e: \
        usb.util.endpoint_direction(e.bEndpointAddress) == \
        usb.util.ENDPOINT_IN)

if epIn is None:
    print("Could not establish an In endpoint.")
    exit()

epOut = usb.util.find_descriptor(
    intf,
    custom_match = \
    lambda e: \
        usb.util.endpoint_direction(e.bEndpointAddress) == \
        usb.util.ENDPOINT_OUT)

if epOut is None:
    print("Could not establish an Out endpoint.")
    exit()

print("Control transfer to enable webserial...")
try:
    dev.ctrl_transfer(bmRequestType = 1, bRequest = 0x22, wIndex = 2, wValue = 0x01)
except USBError as e:
    print("Error sending the control transfer.")
    exit()

print("Connection established!")

#########################
# Image Data Collection #
#########################

def CollectData():
    data = ""
    print("Waiting for data...")
    while True:
        recv = epIn.read(epIn.wMaxPacketSize, 30000)
        data += ('%s' % '{:{fill}{width}{base}}'.format(int.from_bytes(recv, byteorder='big'), fill='0', width=len(recv*2), base='x'))
        # print(len(data))
        if (data[-8:] == "1140feca"):
            break
    return (data[0:-16], data[-16:-8])

# Start image processing with the (hopefully) collected data
if not os.path.exists("images"):
    print("'images' directory does not exist, creating it...")
    os.makedirs("images")

##################
# Select options #
##################

print("=========================\n\
Please pick an option:\n\
1. Print single image\n\
2. Combine RGB images\n\
=========================")

choice = input("Number: ")

if choice.startswith("1"):
    while True:
        data, params = CollectData()
        SaveImage(CreateImage(data, params))
        another = input("Print another? (y/N): ")
        if another.upper().startswith("Y"):
            continue
        else:
            exit()

elif choice.startswith("2"):
    while True:
        print("Please print your red layer")
        red_data, red_params = CollectData()
        red_img = CreateImage(red_data, red_params)
        print("Please print your green layer")
        green_data, green_params = CollectData()
        green_img = CreateImage(green_data, green_params)
        print("Please print your blue layer")
        blue_data, blue_params = CollectData()
        blue_img = CreateImage(blue_data, blue_params)
        SaveImageRGB(red_img, green_img, blue_img)
        another = input("Print another? (y/N): ")
        if another.upper().startswith("Y"):
            continue
        else:
            exit()
