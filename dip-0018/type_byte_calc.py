#!/usr/bin/env python3
"""Calculate type bytes that produce specific bech32 characters."""

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

def convertbits(data, frombits, tobits, pad=True):
    """General power-of-2 base conversion."""
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret

def find_type_byte_for_char(target_char):
    """Find type bytes where the first encoded character is target_char."""
    target_index = CHARSET.index(target_char)
    print(f"\nLooking for type bytes that produce '{target_char}' (index {target_index})")
    print("-" * 60)

    # Use a sample hash (all zeros for simplicity)
    sample_hash = [0] * 20

    results = []
    for type_byte in range(256):
        payload = [type_byte] + sample_hash
        converted = convertbits(payload, 8, 5)
        if converted and CHARSET[converted[0]] == target_char:
            results.append(type_byte)

    print(f"Type bytes that produce '{target_char}': {results}")
    print(f"Hex values: {[hex(b) for b in results]}")
    return results

def show_encoding_for_type_byte(type_byte):
    """Show the full encoding details for a given type byte."""
    sample_hash = [0] * 20
    payload = [type_byte] + sample_hash
    converted = convertbits(payload, 8, 5)

    print(f"\nType byte: {type_byte} (0x{type_byte:02x}, binary: {type_byte:08b})")
    print(f"First few 5-bit values: {converted[:5]}")
    print(f"First few chars: {''.join(CHARSET[v] for v in converted[:5])}")

# Find type bytes for desired characters
print("=" * 60)
print("Finding type bytes for specific first characters")
print("=" * 60)

for char in ['q', 'k', 's', 'x', '7']:
    find_type_byte_for_char(char)

print("\n" + "=" * 60)
print("Encoding details for current and proposed type bytes")
print("=" * 60)

# Check proposed combinations
print("\n--- Checking specific values ---")
for tb in [0x30, 0xE0, 0xA0, 0x80, 48, 224]:
    show_encoding_for_type_byte(tb)
