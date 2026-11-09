#!/usr/bin/python3
# # Example showing how to compute the transaction hash (txid) of a version 2
# # Asset Unlock transaction. The txid is the double-SHA256 of the transaction
# # serialized with the signHeight, quorumHash, and quorumSig fields set to
# # zeros, so every re-signed instance of one withdrawal shares one txid.
import hashlib
import struct

def sha256(s):
    return hashlib.new('sha256', s).digest()

def compact_size(n):
    if n < 253:
        return struct.pack("B", n)
    if n < 0x10000:
        return struct.pack("<BH", 253, n)
    if n < 0x100000000:
        return struct.pack("<BI", 254, n)
    return struct.pack("<BQ", 255, n)

def serialize_with_compact_size(s):
    return compact_size(len(s)) + s

def withdrawal_txid(index, fee, outputs):
    # Transaction version 3, type 9 (Asset Unlock)
    tx = struct.pack("<HH", 3, 9)
    # No inputs
    tx += compact_size(0)
    # Outputs
    tx += compact_size(len(outputs))
    for value, script in outputs:
        tx += struct.pack("<q", value) + serialize_with_compact_size(script)
    # nLockTime
    tx += struct.pack("<I", 0)
    # Payload with signHeight, quorumHash, and quorumSig set to zeros:
    # version (2), index, fee, signHeight (0), quorumHash (zeros), quorumSig (zeros)
    payload = struct.pack("<BQI", 2, index, fee)
    payload += struct.pack("<I", 0)   # signHeight
    payload += b"\x00" * 32           # quorumHash
    payload += b"\x00" * 96           # quorumSig
    tx += serialize_with_compact_size(payload)
    return sha256(sha256(tx))[::-1].hex()

# P2PKH output paying 100000000 duffs to public key hash 0x1111...11
script = bytes.fromhex("76a914" + "11" * 20 + "88ac")
outputs = [(100000000, script)]

for index in [101, 123456789]:
    print(withdrawal_txid(index, 70000, outputs))
