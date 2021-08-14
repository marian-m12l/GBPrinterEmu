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

def CreateImage(data, palette=0xe4, margins=0x00):
    if len(data) == 0:
        print("There's nothing to do. Exiting...")
        exit()

    data = bytes.fromhex(data)

    print(f"{str(len(data))} bytes to print...")

    dump = [data[i:i+16] for i in range(0, len(data), 16)]    # 16 bytes per tile
    print(f"{str(len(dump))} tiles to print...")

    LINES_COUNT = len(dump) // TILES_PER_LINE
    print(f"{LINES_COUNT} lines to print...")

    # Handle margins
    marginTop = (margins>>4) & 0x0f
    marginBottom = margins & 0x0f
    print(f"Margins: {marginTop} line(s) before, {marginBottom} line(s) after")

    # Compute colors from palette parameter
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

        img_timestamp = time.strftime('%Y%m%d - %H%M%S')
        img.save(f"images/decoded_{img_timestamp}.png")
        print(f"Saved to images/decoded_{img_timestamp}.png!")
    except IndexError as e:
        print("Provided data doesn't match expected size, " \
              "please double check your hex dump!")
        exit()

def CreateImageRGB(red_data, green_data, blue_data, palette=0xe4, margins=0x00):
    if len(red_data) == 0:
        print("No data for red later, can't do anything. Exiting...")
        exit()
    elif len(green_data) == 0:
        print("No data for green later, can't do anything. Exiting...")
        exit()
    elif len(blue_data) == 0:
        print("No data for blue later, can't do anything. Exiting...")
        exit()

    red_data = bytes.fromhex(red_data)
    green_data = bytes.fromhex(green_data)
    blue_data = bytes.fromhex(blue_data)

    print(f"{str(len(red_data))} bytes to print...")

    red_dump = [red_data[i:i+16] for i in range(0, len(red_data), 16)]
    print(f"{str(len(red_dump))} red tiles to print...")

    green_dump = [green_data[i:i+16] for i in range(0, len(green_data), 16)]
    print(f"{str(len(green_dump))} green tiles to print...")

    blue_dump = [blue_data[i:i+16] for i in range(0, len(blue_data), 16)]
    print(f"{str(len(blue_dump))} blue tiles to print...")

    LINES_COUNT = len(red_dump) // TILES_PER_LINE
    print(f"{LINES_COUNT} lines to print...")

    # Handle margins
    marginTop = (margins>>4) & 0x0f
    marginBottom = margins & 0x0f
    print(f"Margins: {marginTop} line(s) before, {marginBottom} line(s) after")

    # Compute colors from palette parameter
    colours = [palette>>6, (palette>>4)&0b11, (palette>>2)&0b11, palette&0b11]
    colours = [_*0x55 for _ in colours]
    colours = [(_,_,_) for _ in colours]
    print(f"Palette colours: {colours}")

    try:
        red_img = Image.new(mode='RGB', size=(TILES_PER_LINE * TILE_SIZE, (LINES_COUNT+marginTop+marginBottom) * TILE_SIZE), color=(255,255,255))
        red_pixels = red_img.load()
        for h in range(LINES_COUNT):
            for w in range(TILES_PER_LINE):
                tile = red_dump[(h*TILES_PER_LINE) + w]
                for i in range(TILE_SIZE):
                    for j in range(TILE_SIZE):
                        index = (tile[i * 2] >> (7 - j)) & 0b11
                        red_pixels[(w * TILE_SIZE) + j, ((h+marginTop) * TILE_SIZE) + i] = colours[index]
        red_img = red_img.convert("L")

        green_img = Image.new(mode='RGB', size=(TILES_PER_LINE * TILE_SIZE, (LINES_COUNT+marginTop+marginBottom) * TILE_SIZE), color=(255,255,255))
        green_pixels = green_img.load()
        for h in range(LINES_COUNT):
            for w in range(TILES_PER_LINE):
                tile = green_dump[(h*TILES_PER_LINE) + w]
                for i in range(TILE_SIZE):
                    for j in range(TILE_SIZE):
                        index = (tile[i * 2] >> (7 - j)) & 0b11
                        green_pixels[(w * TILE_SIZE) + j, ((h+marginTop) * TILE_SIZE) + i] = colours[index]
        green_img = green_img.convert("L")

        blue_img = Image.new(mode='RGB', size=(TILES_PER_LINE * TILE_SIZE, (LINES_COUNT+marginTop+marginBottom) * TILE_SIZE), color=(255,255,255))
        blue_pixels = blue_img.load()
        for h in range(LINES_COUNT):
            for w in range(TILES_PER_LINE):
                tile = blue_dump[(h*TILES_PER_LINE) + w]
                for i in range(TILE_SIZE):
                    for j in range(TILE_SIZE):
                        index = (tile[i * 2] >> (7 - j)) & 0b11
                        blue_pixels[(w * TILE_SIZE) + j, ((h+marginTop) * TILE_SIZE) + i] = colours[index]
        blue_img = blue_img.convert("L")

        rgb_image = Image.merge("RGB", (red_img, green_img, blue_img))
        img_timestamp = time.strftime('%Y%m%d - %H%M%S')
        rgb_image.save(f"images/decoded_rgb_{time}.png")
        print(f"Saved to images/decoded_rgb_{img_timestamp}.png!")
    except IndexError as e:
        print("Provided data doesn't match expected size, " \
              "please double check your hex dump!")
        exit()

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
        if len(data) == 11520:
            break
    return data

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
        CreateImage(CollectData())
        another = input("Print another? (y/N): ")
        if another.upper().startswith("Y"):
            continue
        else:
            exit()

elif choice.startswith("2"):
    while True:
        print("Please print your red layer")
        red_data = CollectData()
        print("Please print your green layer")
        green_data = CollectData()
        print("Please print your blue layer")
        blue_data = CollectData()
        CreateImageRGB(red_data, green_data, blue_data)
        another = input("Print another? (y/N): ")
        if another.upper().startswith("Y"):
            continue
        else:
            exit()
