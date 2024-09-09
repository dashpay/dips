#!/usr/bin/python3
# # Example showing how to create the signing session request ID for a given index
import hashlib
import struct

def sha256(s):
    return hashlib.new('sha256', s).digest()

def serialize_with_compact_size(s):
    l = len(s)
    if l < 253:
        return struct.pack("B", l) + s
    if l < 0x10000:
        return struct.pack("<BH", 253, l) + s
    if l < 0x100000000:
        return struct.pack("<BI", 254, l) + s
    return struct.pack("<BQ", 255, l) + s

# requestID = SHA256(SHA256("plwdtx", index))
indices = [101, 123456789]

for index in indices:
    request_id_buf = serialize_with_compact_size(b"plwdtx") + struct.pack("<Q", index)
    request_id = sha256(sha256(request_id_buf))[::-1].hex()
    print(request_id)
