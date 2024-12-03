from __future__ import annotations
import io
import logging as log
from BitPointer import *


class BitStreamBuffer:
    def __init__(self, buffer_size: int = 4096, start_pointer: int = 0) -> None:
        self._buffer_size: int = buffer_size
        self._bit_pointer: BitPointer = BitPointer(buffer_size, start_pointer)
        self._buffer: bytearray = bytearray(buffer_size)
        return

    def __iter__(self) -> int:
        return self

    # TODO: _bit_pointer is no longer an int
    def __next__(self) -> tuple[int, tuple[int, int]]:
        try: 
            adr = next(self._bit_pointer)
        except StopIteration:
            raise StopIteration
        
        val = self._buffer[adr[0]]
        val >>= 7 - adr[1]
        val &= mask(1)
        return val, adr
    
    def get_buffer_size(self) -> int:
        return self._buffer_size

    def set_buffer_size(self, new_buffer_size: int) -> bool:
        try:
            self._buffer_size = new_buffer_size
            return True
        except ValueError as ve:
            log.error(f"Failed to set new buffer size. Error: {ve}")
            return False

    def is_empty(self) -> bool:
        return self._buffer.__len__() == 0

    def set_bit_pointer(self, new_pointer: int) -> bool:
        try:
            self._bit_pointer = BitPointer(new_pointer)
            return True
        except ValueError as ve:
            log.error(f"Failed to set new bit pointer. Error: {ve}")
            return False

    def get_bit_pointer(self) -> BitPointer:
        return self._bit_pointer

    def get_buffer(self) -> bytearray:
        return self._buffer

    def set_buffer(self, insert_buffer: bytearray) -> bool:
        """
        Set the buffer content with the provided bytearray.

        Args:
            insert_buffer (bytearray): The buffer content to set.
            start (int | None): The starting index where the buffer will be inserted.
            end (int | None): The ending index where the buffer will be inserted.

        Returns:
            None
        """
        # # replace the buffer
        # if start is None and end is None:
        #     self._buffer = insert_buffer
        #     return

        # # replace the end of buffer
        # if end is None:
        #     self._buffer = self._buffer[:start] + insert_buffer
        #     return

        # # replace the start of buffer
        # if start is None:
        #     self._buffer = insert_buffer[:end] + self._buffer[end:]

        # # replace the middle of buffer
        try:
            self._buffer = insert_buffer
            return True
        except ValueError as ve:
            log.error(f"Failed to set new buffer. Error: {ve}")
            return False

    def clear_buffer(self, start: int | None, end: int | None) -> None:
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
        if start is None:
            start = 0
        if end is None:
            end = self._buffer_size
        for i in range(start, end):
            self._buffer[i] = b'\x00'
        return



class BitStreamReader(io.FileIO, BitStreamBuffer):
    def __init__(
        self,
        file: io.FileDescriptorOrPath,  # type: ignore
        buffer_size: int = 4096,
        closefd: bool = True,
        opener: io._Opener | None = None,
    ) -> None:
        
        io.FileIO.__init__(self, file, mode="rb", closefd=closefd, opener=opener)
        BitStreamBuffer.__init__(self, buffer_size, 0)

        return

    def is_EOF(self) -> bool:
        """
        Check if the end of the file has been reached.

        Returns:
            bool: True if the end of the file has been reached, False otherwise.
        """
        self.seek(1, 1)
        val = self.tell() == 0
        self.seek(-1, 1)
        return val
    
    def fill_buffer(
        self,
        start: int | None = None,
        end: int | None = None,
    ) -> bool:

        """
        Fill the buffer with data from the file.

        The method fills the buffer from the given start index to the given end index with data from the file.

        Args:
            start (int | None): The starting index of the buffer to fill. Defaults to 0.
            end (int | None): The ending index of the buffer to fill. Defaults to the buffer size.

        Returns:
            bool: True if the buffer was filled successfully, False otherwise.
        """
        if start is None:
            start = 0
        if end is None:
            end = self._buffer_size
        try:
            if self.is_EOF():
                log.info("End of file reached.")
                return False
            self._buffer = self.set_buffer(self._buffer[:start] + io.FileIO.read(self, end - start) + self._buffer[end:])
            return True

        except ValueError as ve:
            log.error(f"Failed to fill buffer. Error: {ve}")
            return False
        

    def __iter__(self) -> BitStreamReader:
        return self

    # TODO: doesn't read from file when reaching the end of buffer
    def __next__(self) -> tuple[bytes, tuple[int, int]]:

        try: 
            adr = next(self._bit_pointer)
        except StopIteration:
            if self.is_EOF():
                raise StopIteration
            self.fill_buffer()
            return next(self)
        
        val = self._buffer[adr[0]]
        val >>= 7 - adr[1]
        val &= mask(1)
        return val, adr

    def read_bits(self, num_bits: int) -> bytearray:
        if num_bits == 0:
            return b''
        
        if num_bits < 0:
            log.error(f"Can't read negative bits. Maybe move the pointer back.")
            # TODO: make a move pointer method
            raise ValueError
        
        # TODO: what if num_bits > self.len_bits()?
        # if num_bits > self._bit_pointer.len_bits():
        #     log.error(f"Can't read more bits than buffer size. Maybe increase buffer size.")
        #     raise ValueError
        
        # if self._bit_pointer + num_bits > len(self._buffer):  # if not enough bits in buffer
        #     self.set_buffer(self._buffer[self._bit_pointer.get_byte():] + \
        #         self._buffer[:self._bit_pointer.get_byte()])   # move remaining buffer to the start
        #     self.fill_buffer(len(self._buffer) - self._bit_pointer.get_byte())  # fill the rest of the buffer
        #     self._bit_pointer._address = self._bit_pointer.get_bit()              # reset pointer
            
        result: bytearray = bytearray((num_bits-1 >> 3) + 1)
        res_pointer: int = 0
        mask_3 = mask(3)
        SHIFT_TO_BYTE = 3
        
        for val, adr in self:
            result[res_pointer >> SHIFT_TO_BYTE] |= val << (mask_3 - adr[1])
            res_pointer += 1
            if res_pointer >= num_bits:
                break
        
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
