import pytest
from BitPointer import *


def test_mask():
    assert mask(1) == 0b00000001
    assert mask(3) == 0b00000111
    assert mask(8) == 0b11111111
    return


def test_BitPointer_defaults():
    DEFAULT_BUFFER_SIZE: int = 4096
    pointer = BitPointer()
    assert len(pointer) == DEFAULT_BUFFER_SIZE
    assert pointer.get_byte() == 0
    assert pointer.get_bit() == 0
    return


def test_BitPointer_params():
    pointer = BitPointer(8)
    assert pointer.get_byte() == 0
    assert pointer.get_bit() == 0
    assert len(pointer) == 8
    assert pointer.len_bits() == 64
    return


def test_BitPointer_iteration():
    pointer = BitPointer(2, 7)
    val1 = next(pointer)
    val2 = next(pointer)
    val3 = next(pointer)
    assert val1 == (0, 7)
    assert val2 == (1, 0)
    assert val3 == (1, 1)
    return
