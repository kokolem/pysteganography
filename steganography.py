from bitstring import Bits
from PIL import Image
import argparse

argument_parser = argparse.ArgumentParser(
    description="This tool allows you to read hidden messages from images. Use the -m argument to hide the message"
                " into the image instead.")
argument_parser.add_argument("filename", help="filename of the image you want to process", type=str)
argument_parser.add_argument("-m", "--message", help="the message you want to hide into the image", type=str)

args = argument_parser.parse_args()

image = Image.open(args.filename)
width, height = image.size

# hide message
if args.message is not None:
    message_bytes = bytes(args.message, encoding='utf-8')

    byte_capacity = width * height * 3 / 8  # how many bytes can be hidden into the image
    if byte_capacity < len(message_bytes):
        print("The message is too long to fit into the image.")
        exit(1)

    # convert the message bytes into a string of ones and zeros
    bits = ""
    for byte in message_bytes:
        bits += Bits(int=byte, length=9)[1:].bin

    # end sequence - byte of ones is invalid utf-8 byte
    # the zero in the beginning is there to prevent the end sequence merging with the previous byte that might be ending
    # with a one
    bits += "011111111"

    # a little performance optimization - no need to iterate over the image pixels after the message was hidden
    finished_writing = False

    writing_bit_index = 0
    for x in range(0, width):
        for y in range(0, height):
            pixel_to_update = list(image.getpixel((x, y)))  # iterating over pixels in the image
            for rgb in range(0, 3):  # pixel is represented as [int(red),int(green),int(blue)] - iterate over the colors
                if writing_bit_index < len(bits):  # performance optimization
                    # change the last bit of the color to the bit at writing_bit_index
                    pixel_to_update[rgb] = pixel_to_update[rgb] & ~1 | int(bits[writing_bit_index])

                    writing_bit_index += 1
                else:
                    finished_writing = True
                    break
            image.putpixel((x, y), tuple(pixel_to_update))  # save the change to the pixel
            if finished_writing:
                break
        if finished_writing:
            break

    image.save(args.filename, "PNG")  # save the image

# show message
else:
    bits = ""
    for x in range(0, width):
        for y in range(0, height):
            pixel = list(image.getpixel((x, y)))  # iterating over the pixels in the image
            for rgb in range(0, 3):
                bits += str(pixel[rgb] & 1)  # read the last bit of the colors

    # find the end sequence and remove the zero that prevented merging with the previous byte
    bits = bits.split("11111111", 1)[0][:-1]

    # convert the string of ones and zeros to bytes
    decode_byte_array = int(bits, 2).to_bytes((len(bits) + 7) // 8, byteorder='big')

    print(decode_byte_array.decode("utf-8"))  # convert the bytes to string
