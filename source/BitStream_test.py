import pytest
import BitStream

def test_bitpointer():
	pointer = BitStream.BitPointer(0, 8)
	assert pointer.get_byte() == 0
	assert pointer.get_bit() == 0
	assert pointer.len_bits() == 8
	assert len(pointer) == 1