import pytest
from source.BitStreamIO import *


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


def test_BitStreamReader_1():
    with BitStreamReader("D:\\PWr\\3rd_year\\CyberSec\\Steganography\\source\\test_file1.txt", 4) as reader:
        assert str(reader.read_bits(8 * 10)) == "Lorem Ipsu"