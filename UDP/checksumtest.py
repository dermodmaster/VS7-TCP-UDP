import struct

peter = "kasdgjasdojjjlbilbuibuiböiöuböuiböiuiböiböuiböuigweg"
peter = peter.encode()

# Quelle: https://github.com/houluy/UDP/blob/master/udp.py
def checksum_func(data):
    checksum = 0
    data_len = len(data)
    if (data_len % 2):
        data_len += 1
        data += struct.pack('!B', 0)

    for i in range(0, data_len, 2):
        w = (data[i] << 8) + (data[i + 1])
        checksum += w

    checksum = (checksum >> 16) + (checksum & 0xFFFF)
    checksum = ~checksum & 0xFFFF
    return checksum

# Quelle: https://github.com/houluy/UDP/blob/master/udp.py
def verify_checksum(data, checksum):
    data_len = len(data)
    if (data_len % 2) == 1:
        data_len += 1
        data += struct.pack('!B', 0)

    for i in range(0, data_len, 2):
        w = (data[i] << 8) + (data[i + 1])
        checksum += w
        checksum = (checksum >> 16) + (checksum & 0xFFFF)

    return checksum


checksum = checksum_func(peter)

print("Checksum", checksum)

verify = verify_checksum(peter,checksum)
print("Verifychecksum", verify)
if verify == 0xFFFF:
    print("CHECKSUM OK")
else:
    print("CHECKSUM BROKEN.. EXPECTED: "+str(0xFFFF)+" GOT: "+str(verify))