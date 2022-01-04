def bytearray_to_int(data):
    """Compute bytearray from int."""
    result = 0
    n = len(data)-1
  
    if data[0] < 128:
        # Positive number
        for value in list(data):
            result += value*(1 << (n * 8))
            n -= 1
    else:
        # Negative number (2s complement)
        for value in list(data):
            result += (255 - value) * (1 << (n * 8))
            n -= 1
        result = -(result + 1)
    
    return result


def get_crc(frame):
    """Get CRC from frame."""
    crc_mask = 0x31
    crc = 0xFF
  
    for c in list(frame):      
        for cnt in range(0, 8):
            if (crc ^ c) & 0x80:
                crc = ((crc << 1) & 0xFF) ^ crc_mask
            else:
                crc = (crc << 1) & 0xFF
            c = c << 1
  
    return bytearray([crc])
