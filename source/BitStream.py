
import io


default_buffer_size = 4096


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
        self.seek(1, 1) # FIXME move back
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
