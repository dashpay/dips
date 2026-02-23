#!/usr/bin/env python3
# Copyright (c) 2017, 2020 Pieter Wuille
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
DIP-18 Bech32m address encoding for Dash Platform, with full DIP-17 test vector validation.

Bech32/Bech32m functions are copied verbatim from BIP-350 reference implementation:
https://github.com/sipa/bech32/blob/master/ref/python/segwit_addr.py

This module provides:
- Bech32m encoding/decoding (BIP-350)
- Dash Platform address encoding/decoding (DIP-18)
- BIP-39/BIP-32 derivation for validating DIP-17 test vectors

Dependencies:
    pip install ecdsa

Usage:
    python bech32.py
"""

from typing import Tuple, Literal
from hashlib import sha256, pbkdf2_hmac
from enum import Enum
import hashlib
import hmac
import unicodedata

from ecdsa import SECP256k1, SigningKey

# ---- Bech32/Bech32m reference implementation (BIP-350) ----
# The following code up to "End of BIP-350 reference" is copied verbatim from:
# https://github.com/sipa/bech32/blob/master/ref/python/segwit_addr.py


class Encoding(Enum):
    """Enumeration type to list the various supported encodings."""
    BECH32 = 1
    BECH32M = 2

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
BECH32M_CONST = 0x2bc830a3

def bech32_polymod(values):
    """Internal function that computes the Bech32 checksum."""
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def bech32_hrp_expand(hrp):
    """Expand the HRP into values for checksum computation."""
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def bech32_verify_checksum(hrp, data):
    """Verify a checksum given HRP and converted data characters."""
    const = bech32_polymod(bech32_hrp_expand(hrp) + data)
    if const == 1:
        return Encoding.BECH32
    if const == BECH32M_CONST:
        return Encoding.BECH32M
    return None

def bech32_create_checksum(hrp, data, spec):
    """Compute the checksum values given HRP and data."""
    values = bech32_hrp_expand(hrp) + data
    const = BECH32M_CONST if spec == Encoding.BECH32M else 1
    polymod = bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ const
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def bech32_encode(hrp, data, spec):
    """Compute a Bech32 string given HRP and data values."""
    combined = data + bech32_create_checksum(hrp, data, spec)
    return hrp + '1' + ''.join([CHARSET[d] for d in combined])

def bech32_decode(bech):
    """Validate a Bech32/Bech32m string, and determine HRP and data."""
    if ((any(ord(x) < 33 or ord(x) > 126 for x in bech)) or
            (bech.lower() != bech and bech.upper() != bech)):
        return (None, None, None)
    bech = bech.lower()
    pos = bech.rfind('1')
    if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
        return (None, None, None)
    if not all(x in CHARSET for x in bech[pos+1:]):
        return (None, None, None)
    hrp = bech[:pos]
    data = [CHARSET.find(x) for x in bech[pos+1:]]
    spec = bech32_verify_checksum(hrp, data)
    if spec is None:
        return (None, None, None)
    return (hrp, data[:-6], spec)

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


# ---- End of BIP-350 reference ----


# ---- Dash Platform address encoding on top of Bech32m ----

Network = Literal["mainnet", "testnet"]
AddrType = Literal["p2pkh", "p2sh"]

NETWORK_TO_HRP = {
    "mainnet": "dash",
    "testnet": "tdash"
}

HRP_TO_NETWORK = {v: k for k, v in NETWORK_TO_HRP.items()}

TYPE_TO_BYTE = {
    "p2pkh": 0xb0,
    "p2sh": 0x80,
}

BYTE_TO_TYPE = {v: k for k, v in TYPE_TO_BYTE.items()}


def encode_platform_address(hash160: bytes,
                            addr_type: AddrType,
                            network: Network) -> str:
    """
    Encode a Dash Platform address as Bech32m.

    :param hash160: 20-byte HASH160(pubkey or script)
    :param addr_type: "p2pkh" or "p2sh"
    :param network: "mainnet", "testnet"
    :return: Bech32m-encoded address string
    """
    if len(hash160) != 20:
        raise ValueError("hash160 must be 20 bytes")

    if addr_type not in TYPE_TO_BYTE:
        raise ValueError("unknown addr_type")

    if network not in NETWORK_TO_HRP:
        raise ValueError("unknown network")

    hrp = NETWORK_TO_HRP[network]
    type_byte = TYPE_TO_BYTE[addr_type]

    payload_bytes = bytes([type_byte]) + hash160  # 21 bytes
    data5 = convertbits(payload_bytes, 8, 5, pad=True)

    return bech32_encode(hrp, data5, Encoding.BECH32M)


def decode_platform_address(addr: str) -> Tuple[Network, AddrType, bytes]:
    """
    Decode a Dash Platform Bech32m address into (network, addr_type, hash160).

    :param addr: Bech32m-encoded Dash Platform address
    :return: (network, "p2pkh"/"p2sh", 20-byte hash160)
    """
    hrp, data_no_checksum, spec = bech32_decode(addr)

    if hrp is None:
        raise ValueError("invalid Bech32m address")

    if spec != Encoding.BECH32M:
        raise ValueError("address is not Bech32m encoded")

    if hrp not in HRP_TO_NETWORK:
        raise ValueError(f"unknown HRP '{hrp}' for Dash Platform")

    network = HRP_TO_NETWORK[hrp]

    # Convert back to 8-bit payload, without padding
    payload_bytes = convertbits(data_no_checksum, 5, 8, pad=False)
    if payload_bytes is None:
        raise ValueError("invalid payload encoding")
    payload_bytes = bytes(payload_bytes)

    if len(payload_bytes) != 21:
        raise ValueError("invalid payload length (expected 21 bytes)")

    type_byte = payload_bytes[0]
    hash160 = payload_bytes[1:]

    if type_byte not in BYTE_TO_TYPE:
        raise ValueError(f"unknown type byte {type_byte:#x}")

    addr_type = BYTE_TO_TYPE[type_byte]

    return network, addr_type, hash160


# ---- BIP-39 / BIP-32 derivation for test vector validation ----

# Hardened flag for BIP-32 derivation
H = 0x80000000


def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """BIP-39: Convert mnemonic to 64-byte seed using PBKDF2-HMAC-SHA512."""
    mnemonic = unicodedata.normalize('NFKD', mnemonic)
    passphrase = unicodedata.normalize('NFKD', passphrase)
    return pbkdf2_hmac(
        "sha512",
        mnemonic.encode("utf-8"),
        ("mnemonic" + passphrase).encode("utf-8"),
        2048
    )


def bip32_master(seed: bytes) -> tuple[bytes, bytes]:
    """BIP-32: Derive master private key and chain code from seed."""
    I = hmac.new(b"Bitcoin seed", seed, "sha512").digest()
    return I[:32], I[32:]  # private_key, chain_code


def bip32_derive_child(priv_key: bytes, chain_code: bytes, index: int) -> tuple[bytes, bytes]:
    """BIP-32: Derive child key at given index (hardened if index >= 0x80000000)."""
    if index >= 0x80000000:  # hardened
        data = b'\x00' + priv_key + index.to_bytes(4, 'big')
    else:  # normal
        sk = SigningKey.from_string(priv_key, curve=SECP256k1)
        pubkey = sk.get_verifying_key().to_string("compressed")
        data = pubkey + index.to_bytes(4, 'big')

    I = hmac.new(chain_code, data, "sha512").digest()
    child_key_int = (int.from_bytes(I[:32], 'big') + int.from_bytes(priv_key, 'big')) % SECP256k1.order
    return child_key_int.to_bytes(32, 'big'), I[32:]


def derive_path(seed: bytes, path: list[int]) -> bytes:
    """Derive private key at full BIP-32 path."""
    priv, chain = bip32_master(seed)
    for idx in path:
        priv, chain = bip32_derive_child(priv, chain, idx)
    return priv


def hash160(data: bytes) -> bytes:
    """HASH160 = RIPEMD160(SHA256(data))."""
    return hashlib.new('ripemd160', sha256(data).digest()).digest()


def priv_to_compressed_pub(priv_key: bytes) -> bytes:
    """Convert private key to compressed public key (33 bytes)."""
    sk = SigningKey.from_string(priv_key, curve=SECP256k1)
    return sk.get_verifying_key().to_string("compressed")


def format_path(path: list[int]) -> str:
    """Format derivation path for display."""
    parts = ["m"]
    for idx in path:
        if idx >= H:
            parts.append(f"{idx - H}'")
        else:
            parts.append(str(idx))
    return "/".join(parts)


# ---- Test vectors ----

# DIP-17 P2PKH vectors: (path, priv_hex, pub_hex, hash160_hex, mainnet_addr, testnet_addr)
DIP17_VECTORS = [
    # Vector 1: m/9'/5'/17'/0'/0'/0
    (
        [9 + H, 5 + H, 17 + H, 0 + H, 0 + H, 0],
        "6bca392f43453b7bc33a9532b69221ce74906a8815281637e0c9d0bee35361fe",
        "03de102ed1fc43cbdb16af02e294945ffaed8e0595d3072f4c592ae80816e6859e",
        "f7da0a2b5cbd4ff6bb2c4d89b67d2f3ffeec0525",
        "dash1krma5z3ttj75la4m93xcndna9ullamq9y5e9n5rs",
        "tdash1krma5z3ttj75la4m93xcndna9ullamq9y5fzq2j7",
    ),
    # Vector 2: m/9'/5'/17'/0'/0'/1
    (
        [9 + H, 5 + H, 17 + H, 0 + H, 0 + H, 1],
        "eef58ce73383f63d5062f281ed0c1e192693c170fbc0049662a73e48a1981523",
        "02269ff766fcd04184bc314f5385a04498df215ce1e7193cec9a607f69bc8954da",
        "a5ff0046217fd1c7d238e3e146cc5bfd90832a7e",
        "dash1kzjl7qzxy9lar37j8r37z3kvt07epqe20ckxfezw",
        "tdash1kzjl7qzxy9lar37j8r37z3kvt07epqe20cxp68nq",
    ),
    # Vector 3: m/9'/5'/17'/0'/1'/0 (key_class' = 1')
    (
        [9 + H, 5 + H, 17 + H, 0 + H, 1 + H, 0],
        "cc05b4389712a2e724566914c256217685d781503d7cc05af6642e60260830db",
        "0317a3ed70c141cffafe00fa8bf458cec119f6fc039a7ba9a6b7303dc65b27bed3",
        "6d92674fd64472a3dfcfc3ebcfed7382bf699d7b",
        "dash1kpkeye606ez89g7lelp7hnldwwpt76va0v3j6x28",
        "tdash1kpkeye606ez89g7lelp7hnldwwpt76va0vp4fcmf",
    ),
]

# DIP-18 P2SH vector (address encoding only, no derivation path)
P2SH_VECTOR = (
    "43fa183cf3fb6e9e7dc62b692aeb4fc8d8045636",
    "dash1sppl5xpu70aka8nacc4kj2htflydspzkxch4cad6",
    "tdash1sppl5xpu70aka8nacc4kj2htflydspzkxc8jtru5",
)


# ---- Self-test ----

if __name__ == "__main__":
    print("=" * 70)
    print("DIP-17 / DIP-18 Test Vector Validation")
    print("=" * 70)

    # BIP-39 mnemonic (test-only)
    mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    passphrase = ""

    print(f"\nMnemonic: {mnemonic}")
    print(f"Passphrase: {'(empty)' if not passphrase else passphrase}")

    # Step 1: Mnemonic to seed
    seed = mnemonic_to_seed(mnemonic, passphrase)
    print(f"Seed: {seed.hex()}")

    all_passed = True

    # Step 2: Validate DIP-17 derivation vectors
    print("\n" + "-" * 70)
    print("DIP-17 Derivation Validation")
    print("-" * 70)

    for i, (path, expected_priv, expected_pub, expected_hash, _, _) in enumerate(DIP17_VECTORS, 1):
        print(f"\nVector {i}: {format_path(path)}")

        # Derive private key
        priv = derive_path(seed, path)
        priv_hex = priv.hex()

        # Derive public key
        pub = priv_to_compressed_pub(priv)
        pub_hex = pub.hex()

        # Compute HASH160
        h160 = hash160(pub)
        h160_hex = h160.hex()

        # Validate
        priv_ok = priv_hex == expected_priv
        pub_ok = pub_hex == expected_pub
        hash_ok = h160_hex == expected_hash

        print(f"  Private Key: {priv_hex}")
        print(f"    Expected:  {expected_priv} {'✓' if priv_ok else '✗ MISMATCH'}")

        print(f"  Public Key:  {pub_hex}")
        print(f"    Expected:  {expected_pub} {'✓' if pub_ok else '✗ MISMATCH'}")

        print(f"  HASH160:     {h160_hex}")
        print(f"    Expected:  {expected_hash} {'✓' if hash_ok else '✗ MISMATCH'}")

        if not (priv_ok and pub_ok and hash_ok):
            all_passed = False

    # Step 3: Validate DIP-18 P2PKH address encoding
    print("\n" + "-" * 70)
    print("DIP-18 P2PKH Address Encoding Validation")
    print("-" * 70)

    for i, (_, _, _, expected_hash, expected_main, expected_test) in enumerate(DIP17_VECTORS, 1):
        h160 = bytes.fromhex(expected_hash)

        mainnet_addr = encode_platform_address(h160, "p2pkh", "mainnet")
        testnet_addr = encode_platform_address(h160, "p2pkh", "testnet")

        main_ok = mainnet_addr == expected_main
        test_ok = testnet_addr == expected_test

        print(f"\nVector {i} (HASH160: {expected_hash[:16]}...):")
        print(f"  Mainnet: {mainnet_addr}")
        print(f"    Expected: {expected_main} {'✓' if main_ok else '✗ MISMATCH'}")
        print(f"  Testnet: {testnet_addr}")
        print(f"    Expected: {expected_test} {'✓' if test_ok else '✗ MISMATCH'}")

        # Verify round-trip decoding
        dec_net_m, dec_type_m, dec_hash_m = decode_platform_address(mainnet_addr)
        dec_net_t, dec_type_t, dec_hash_t = decode_platform_address(testnet_addr)

        assert dec_net_m == "mainnet" and dec_type_m == "p2pkh" and dec_hash_m.hex() == expected_hash
        assert dec_net_t == "testnet" and dec_type_t == "p2pkh" and dec_hash_t.hex() == expected_hash

        if not (main_ok and test_ok):
            all_passed = False

    # Step 4: Validate DIP-18 P2SH address encoding
    print("\n" + "-" * 70)
    print("DIP-18 P2SH Address Encoding Validation")
    print("-" * 70)

    p2sh_hash, p2sh_main_expected, p2sh_test_expected = P2SH_VECTOR
    h160 = bytes.fromhex(p2sh_hash)

    mainnet_addr = encode_platform_address(h160, "p2sh", "mainnet")
    testnet_addr = encode_platform_address(h160, "p2sh", "testnet")

    main_ok = mainnet_addr == p2sh_main_expected
    test_ok = testnet_addr == p2sh_test_expected

    print(f"\nP2SH (HASH160: {p2sh_hash[:16]}...):")
    print(f"  Mainnet: {mainnet_addr}")
    print(f"    Expected: {p2sh_main_expected} {'✓' if main_ok else '✗ MISMATCH'}")
    print(f"  Testnet: {testnet_addr}")
    print(f"    Expected: {p2sh_test_expected} {'✓' if test_ok else '✗ MISMATCH'}")

    # Verify round-trip decoding
    dec_net_m, dec_type_m, dec_hash_m = decode_platform_address(mainnet_addr)
    dec_net_t, dec_type_t, dec_hash_t = decode_platform_address(testnet_addr)

    assert dec_net_m == "mainnet" and dec_type_m == "p2sh" and dec_hash_m.hex() == p2sh_hash
    assert dec_net_t == "testnet" and dec_type_t == "p2sh" and dec_hash_t.hex() == p2sh_hash

    if not (main_ok and test_ok):
        all_passed = False

    # Summary
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All test vectors validated successfully!")
    else:
        print("✗ Some test vectors failed validation!")
        exit(1)
    print("=" * 70)
