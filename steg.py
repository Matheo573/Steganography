import logging
from argparse import ArgumentParser
from typing import Callable
import os
import io
from PIL import Image

default_buffer_size = 4096
def is_valid_steganography_extension(extension):
    return extension.lower() in [".png"]


def read_file_as_bytes(file_path) -> tuple[bytes, int]:
    with open(file_path, "rb") as file:
        byte_stream = file.read()
    file_size = os.path.getsize(file_path)

    return byte_stream, file_size


def mask(size: int) -> int:
    """
    Create a mask of the given size.

    Args:
        size (int): The size of the mask to create.

    Returns:
        int: The created mask.
    """
    return (1 << size) - 1

class BitPointer:
    def __init__(self, address: int | None = None, length: int | None = None) -> None:
        if address is None:
            address = 0
        if length is None:
            length = default_buffer_size
        self._address = address
        self._address_max = length << 3
        return
    
    def __len__(self) -> int:
        return self._address_max >> 3

    def len_bits(self) -> int:
        """
        Get the length of the buffer in bits.

        Returns:
            int: The length of the buffer in bits.
        """
        return self._address_max

    def position_byte(self) -> int:
        """
        Get the current byte position within the buffer.

        Returns:
            int: The current byte position within the buffer.
        """
        return self._address >> 3

    def position_bit(self) -> int:
        """
        Get the current bit position within the byte. Values in range 0 - 7

        Returns:
            int: The current bit position within the buffer.
        """
        return self._address & mask(3)

    def __iter__(self) -> "BitPointer":
        return self
    def __next__(self) -> bytes:
        if self._address >= self._address_max:
            raise StopIteration
        address = self._address
        self._address += 1
        return address

    
class BitStreamBuffer:
    def __init__(self, buffer_size: int = 4096, start_pointer: int = 0) -> None:
        self._buffer = bytearray(buffer_size)
        self._buffer_size = buffer_size
        self._bit_pointer = BitPointer(start_pointer)
        return

    def empty(self) -> bool:
        return self._buffer.__len__() == 0

    def getbuffer(self) -> bytearray:
        return self._buffer

    def clearbuffer(self, start: int | None, end: int | None) -> None:
        """
        Clear the buffer content in the given range.

        Args:
            start (int | None): The starting index of the range to clear.
            end (int | None): The ending index of the range to clear.

        Returns:
            None
        """
        if start is None and end is None:
            self._buffer = bytearray(self._buffer_size)
            return
        for i in range(start, end):
            self._buffer[i] = b''
        return

    def setbuffer(self, insert_buffer: bytearray, start: int | None = None, end: int | None = None) -> None:
        """
        Set the buffer content with the provided bytearray.

        Args:
            insert_buffer (bytearray): The buffer content to set.
            start (int | None): The starting index where the buffer will be inserted.
            end (int | None): The ending index where the buffer will be inserted.

        Returns:
            None
        """
        # replace the buffer
        if start is None and end is None:
            self._buffer = insert_buffer
            return

        # replace the end of buffer
        if end is None:
            self._buffer = self._buffer[:start] + insert_buffer
            return

        # replace the start of buffer
        if start is None:
            self._buffer = insert_buffer[:end] + self._buffer[end:]

        # replace the middle of buffer
        
        self._buffer = self._buffer[:start] + insert_buffer[:end] + self._buffer[end:]
        return


class BitStreamReader(io.FileIO, BitStreamBuffer):
    def __init__(
        self,
        file: "FileDescriptorOrPath",  # type: ignore
        buffer_size: int = 4096,
        begin_pointer: int = 0,
        closefd: bool = True,
        opener: "io._Opener | None" = None,
    ) -> None:
        
        io.FileIO.__init__(self, file, mode="rb", closefd=closefd, opener=opener)
        BitStreamBuffer.__init__(self, buffer_size, begin_pointer)

        return

    def is_end_of_file(self) -> bool:
        """
        Check if the end of the file has been reached.

        This method seeks forward one byte and checks if the file pointer has reached the start of the file.

        Returns:
            bool: True if the end of the file has been reached, False otherwise.
        """
        self.seek(1, 1)
        return self.tell() == 0

    def fill_buffer(
        self,
        start: int | None = None,
        end: int | None = None,
    ) -> None:

        """
        Fill the buffer with the provided byte range from the underlying file.

        This method seeks the file pointer to the start index and reads the specified byte range
        and sets the buffer content with the read bytes.

        Args:
            start (int | None): The starting index of the byte range to read.
            end (int | None): The ending index of the byte range to read.

        Returns:
            None
        """
        if start is None:
            start = 0
        if end is None:
            end = self._buffer_size
        if self.is_end_of_file():
            raise EOFError

        self._buffer = self.setbuffer(bytearray(io.FileIO.read(self, end - start)), start, end)
        return
        

    def __iter__(self) -> "BitStreamReader":
        return self
    
    def __next__(self) -> bytes:
        if self._bit_pointer >= self.len_bits():
            raise StopIteration
        val = self._buffer[self.position_byte()]
        val >>= 7 - self.position_bit()
        val &= mask(1)
        self._bit_pointer += 1
        return val

    def read_bits(self, num_bits: int) -> bytes:
        if num_bits <= 0:
            return b''
        
        if self._bit_pointer + num_bits > self.len_bits():
            self._buffer = self._buffer[self.position_byte():]
            self._bit_pointer = self.position_bit()
            self.fill_buffer(start=self._buffer.__len__())
        result = bytearray((num_bits-1) >> 3 + 1)
        res_pointer = 0
        for i in self:
            pass
        return result
        
        
    def read_bit(self) -> int:
        return self.read_bits(1)


class BitStreamWriter(io.FileIO, BitStreamBuffer):
    def __init__(
        self,
        file: "FileDescriptorOrPath",  # type: ignore
        buffer_size: int = 4096,
        begin_pointer: int = 0,
        closefd: bool = True,
        opener: "io._Opener | None" = None,
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

    raw_message, msg_size = read_file_as_bytes(message)
    print(f"Size of the encoded message: {msg_size} bytes")
    
    bit_length = len(raw_message) * 8
    bit_offset = 0
    mask_1 = 0b00000001
    mask_3 = 0b00000111
    reader = BitStreamReader(input)
    reader.fill_buffer()

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

                temp = (
                    (pixel[0] & mask_1) << 2
                    | (pixel[1] & mask_1) << 1
                    | (pixel[2] & mask_1)
                )
                temp <<= max(5 - (bit_offset & mask_3), 0)

                # when bits stored lay between 2 bytes
                trim = max((bit_offset & mask_3) - 5, 0)
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
