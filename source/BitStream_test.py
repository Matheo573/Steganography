import pytest
from BitStream import *


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


def test_BitStreamBuffer_defaults():
    buffer = BitStreamBuffer()
    assert buffer.get_buffer_size() == 4096
    assert buffer.get_buffer().__len__() == 4096
    assert buffer.get_bit_pointer().get_bit() == 0
    assert buffer.get_bit_pointer().get_byte() == 0
    return
'''
'''
def test_BitStreamBuffer_next():
    buffer = BitStreamBuffer(2, 8)
    val = next(buffer._bit_pointer)
    assert buffer._bit_pointer == BitPointer(2, 9)
    assert val == (1, 0)

def test_BitStreamBuffer_next2():
    buffer = BitStreamBuffer(2, 8)
    val = next(buffer._bit_pointer)

def test_BitStreamBuffer_3():
    buffer = BitStreamBuffer(2, 8)
    assert True

def test_BitStreamBuffer_4():
    buffer = BitStreamBuffer(2, 8)
    assert True
