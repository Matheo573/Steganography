import logging
from argparse import ArgumentParser
from typing import Callable
import os
import io
from PIL import Image


def is_valid_steganography_extension(extension):
    return extension.lower() in [".png"]


def read_file_as_bytes(file_path) -> tuple[bytes, int]:
    with open(file_path, "rb") as file:
        byte_stream = file.read()
    file_size = os.path.getsize(file_path)
    
    return byte_stream, file_size


class BitStreamBuffer():
    def __init__(self, buffer_size: int = 4096, begin_pointer: int = 0) -> None:
        self._buffer_size = buffer_size
        self._buffer = bytearray(buffer_size)
        self._bit_pointer = begin_pointer
        return

    def offset(self) -> int:
        return self._bit_pointer >> 3
    
    def bit(self) -> int:
        return self._bit_pointer & 0b00000111
    
    def __len__(self) -> int:
        return self._buffer_size
    
    def getbuffer(self) -> bytearray:
        return self._buffer
    
    def clearbuffer(self, start: int = 0, end: int = -1) -> None:
        self._buffer = bytearray(self._buffer_size)
        return



class BitStreamReader(io.FileIO, BitStreamBuffer):
    def __init__(
        self,
        file: "FileDescriptorOrPath", # type: ignore
        buffer_size: int = 4096,
        begin_pointer: int = 0, 
        closefd: bool = True,
        opener: "io._Opener | None" = None
    ) -> None:
        
        io.FileIO.__init__(self, file, mode="rb", closefd=closefd, opener=opener)
        BitStreamBuffer.__init__(self, buffer_size, begin_pointer)

        return
class BitStreamWriter(io.FileIO, BitStreamBuffer):
    def __init__(
        self,
        file: "FileDescriptorOrPath", # type: ignore
        buffer_size: int = 4096,
        begin_pointer: int = 0, 
        closefd: bool = True,
        opener: "io._Opener | None" = None
    ) -> None:
        
        io.FileIO.__init__(self, file, mode="wb", closefd=closefd, opener=opener)
        BitStreamBuffer.__init__(self, buffer_size, begin_pointer)

        return

def is_transparent(pixel) -> bool:
    return not pixel[3]


class FinishLoop(Exception):
    pass


def encode(input, message, output):

    _, extension = os.path.splitext(output)
    if not is_valid_steganography_extension(extension):
        raise ValueError(f"Unsupported image extension: {extension}")

    # Open the image
    img = Image.open(input)

    # Convert to RGBA if not already
    img = img.convert("RGBA")

    # Get pixel data
    width, height = img.size

    raw_message, size = read_file_as_bytes(message)
    bit_length = len(raw_message) * 8
    bit_offset = 0
    mask_1 = 0b00000001
    mask_3 = 0b00000111
    reader = BitStreamReader(input)


    try:
        for x in range(width):
            for y in range(height):
                pixel = list(img.getpixel((x, y)))

                if is_transparent(pixel):
                    continue

                # end on
                if bit_offset >= bit_length:
                    raise FinishLoop
                # print(chr(raw_message[bit_offset>>3]))

                for i in range(3):
                    if bit_offset >= bit_length:
                        raise FinishLoop
                    pixel[i] &= ~mask_1
                    pixel[i] |= (
                        raw_message[bit_offset >> 3] >> 7 - (bit_offset & mask_3)
                    ) & mask_1
                    bit_offset += 1
                img.putpixel((x, y), tuple(pixel))

    except FinishLoop:
        pass

    img.save(output)
    print(f"Size of the encoded message: {size} bytes")
    print("Message encoded successfully")
    return


def decode(input, size, output):
    _, extension = os.path.splitext(input)
    if not is_valid_steganography_extension(extension):
        raise ValueError(f"Unsupported image extension: {extension}")

    # Open the image
    img = Image.open(input)

    # Convert to RGBA if not already
    img = img.convert("RGBA")

    # Get pixel data
    width, height = img.size

    raw_message = bytearray(size)
    bit_length = size * 8
    bit_offset = 0
    mask_1 = 0b00000001
    mask_3 = 0b00000111
    mask_8 = 0b11111111
    
    class BreakLoop(Exception):
        pass    

    try:
        for x in range(width):
            for y in range(height):
                pixel = img.getpixel((x, y))
                
                if is_transparent(pixel):
                    continue

                temp = (pixel[0] & mask_1) << 2 | (pixel[1] & mask_1) << 1 | (pixel[2] & mask_1)
                temp <<= max(5-(bit_offset & mask_3), 0)
                
                # when bits stored lay between 2 bytes
                trim = max((bit_offset & mask_3)-5, 0)
                raw_message[bit_offset >> 3] |= temp >> trim
                bit_offset += 3
                if bit_offset >= bit_length:
                    raise BreakLoop
                if trim:
                    raw_message[bit_offset >> 3] |= (temp << (8 - trim)) & mask_8
                
                
        
    except BreakLoop:
        pass

    with open(output, "wb") as file:
        file.write(raw_message)
    
    
    


def main(
    operation: Callable[..., None],
    log_level: int | None = logging.WARNING,
) -> None:
    logging.basicConfig(level=log_level)

    operation()

    return


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Steganography image encoder/decoder",
        add_help=True,
    )

    log_group = parser.add_mutually_exclusive_group(required=False)
    log_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show more information about the program",
    )
    log_group.add_argument(
        "--debug",
        action="store_true",
        help="debug mode (for developers or troubleshooting)",
    )

    # Define subparsers for encode and decode operations
    subparsers = parser.add_subparsers(dest="operation", help="Choose an operation")

    # Encoder parser
    encode_parser = subparsers.add_parser(
        "encode", help="Encode a message into an image"
    )
    encode_parser.add_argument("input", type=str, help="Path to the input image file")
    encode_parser.add_argument("message", type=str, help="Message to hide in the image")
    encode_parser.add_argument(
        "output", type=str, help="Path to save the encoded image"
    )

    # Decoder parser
    decode_parser = subparsers.add_parser(
        "decode", help="Decode a message from an image"
    )
    decode_parser.add_argument("input", type=str, help="Path to the input image file")
    decode_parser.add_argument("size", type=int, help="size of the message in bytes")
    decode_parser.add_argument(
        "output", type=str, help="Path to save the decoded message"
    )

    args = parser.parse_args()
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    if args.operation == "encode":
        operation = lambda: encode(args.input, args.message, args.output)
    elif args.operation == "decode":
        operation = lambda: decode(args.input, args.size, args.output)
    else:
        parser.print_help()
        exit(1)

    main(operation, log_level)
