from __future__ import annotations
import logging as log


def mask(size: int) -> int:
    """
    Create a mask of the given size.

    Args:
        size (int): The size of the mask to create.

    Returns:
        int: The created mask.
    """
    return (1 << size) - 1

bit_mask = mask(3)



class BitPointer:

    def __init__(self, length: int | None = None, init_address: int | None = None) -> None:
        DEFAULT_BUFFER_SIZE: int = 4096

        if init_address is None:
            init_address = 0
        if length is None:
            length = DEFAULT_BUFFER_SIZE

        self._address = init_address
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

    def get_byte(self) -> int:
        """
        Get the current byte position within the buffer.

        Returns:
            int: The current byte position within the buffer.
        """
        return self._address >> 3

    def get_bit(self) -> int:
        """
        Get the current bit position within the byte. Values in range 0 - 7

        Returns:
            int: The current bit position within the buffer.
        """
        return self._address & bit_mask

    def __iter__(self) -> BitPointer:
        return self

    def __next__(self) -> tuple[int, int]:
        if self._address >= self._address_max:
            raise StopIteration
        offset, bit = self.get_byte(), self.get_bit()
        self._address += 1
        return offset, bit

    def __int__(self) -> int:
        return self._address

    def __str__(self) -> str:
        return f"BitPointer({self._address_max}, {self._address})"

    def __repr__(self) -> str:
        return f"BitPointer({self._address_max}, {self._address})"

    @classmethod
    def __match_args__(cls, *args):
        if len(args) == 2:
            return args
        raise TypeError(f"No match for {args}")

    def compare(self, other: BitPointer) -> tuple[int, int]:
        return self._address - other._address, self._address_max - other._address_max

    # def __eq__(self, other: object) -> bool:
    #     return int(self) == int(other)

    # def __ne__(self, other: object) -> bool:
    #     return int(self) != int(other)

    # def __lt__(self, other: object) -> bool:
    #     return int(self) < int(other)

    # def __gt__(self, other: object) -> bool:
    #     return int(self) > int(other)

    # def __le__(self, other: object) -> bool:
    #     return self < other or self == other

    # def __ge__(self, other: object) -> bool:
    #     return self > other or self == other

    def __add__(self, other: int) -> BitPointer:
        return BitPointer(self._address_max, self._address + other)

    def __sub__(self, other: int) -> BitPointer:
        return BitPointer(self._address_max, self._address - other)

    def __iadd__(self, other: int) -> BitPointer:
        self._address += other
        return self

    def __isub__(self, other: int) -> BitPointer:
        self._address -= other
        return self
