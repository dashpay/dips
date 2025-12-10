#!/usr/bin/env python3
"""
DIP-18 Bech32m address encoding for Dash Platform, with full DIP-17 test vector validation.

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
import hashlib
import hmac

from ecdsa import SECP256k1, SigningKey

# ---- Generic bech32m implementation (BIP-350) ----

# 32-character Bech32 alphabet
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
CHARSET_REV = {c: i for i, c in enumerate(CHARSET)}

# Generator constants for the polymod function
GENERATOR = [0x3b6a57b2,
             0x26508e6d,
             0x1ea119fa,
             0x3d4233dd,
             0x2a1462b3]

# Bech32m constant from BIP-350
BECH32M_CONST = 0x2bc830a3


def _polymod(values) -> int:
    """Internal: compute Bech32/Bech32m polymod checksum."""
    chk = 1
    for v in values:
        top = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            if (top >> i) & 1:
                chk ^= GENERATOR[i]
    return chk


def _hrp_expand(hrp: str):
    """Expand the HRP into values for checksum computation."""
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _create_checksum_bech32m(hrp: str, data):
    """Create a Bech32m checksum for given HRP and data."""
    values = _hrp_expand(hrp) + list(data) + [0, 0, 0, 0, 0, 0]
    polymod = _polymod(values) ^ BECH32M_CONST
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def _verify_checksum_bech32m(hrp: str, data) -> bool:
    """Verify Bech32m checksum for a given HRP and data+checksum."""
    return _polymod(_hrp_expand(hrp) + list(data)) == BECH32M_CONST


def bech32m_encode(hrp: str, data) -> str:
    """
    Encode HRP + data (5-bit values) into a Bech32m string.
    `data` should NOT contain the checksum yet.
    """
    if not hrp or any(ord(c) < 33 or ord(c) > 126 for c in hrp):
        raise ValueError("invalid HRP")

    # Enforce lowercase for output
    hrp = hrp.lower()

    checksum = _create_checksum_bech32m(hrp, data)
    combined = list(data) + checksum
    return hrp + "1" + "".join(CHARSET[d] for d in combined)


def bech32m_decode(addr: str) -> Tuple[str, list]:
    """
    Decode a Bech32m string into (hrp, data_without_checksum).
    Raises ValueError if invalid or checksum fails.
    """
    if any(ord(c) < 33 or ord(c) > 126 for c in addr):
        raise ValueError("invalid characters")

    # Reject mixed case
    if addr.lower() != addr and addr.upper() != addr:
        raise ValueError("mixed case not allowed")

    addr = addr.lower()

    # Overall length constraints from BIP-173/350
    if len(addr) < 8 or len(addr) > 90:
        raise ValueError("invalid length")

    # Separator must be present and not at extremes
    pos = addr.rfind("1")
    if pos == -1 or pos < 1 or pos + 7 > len(addr):
        raise ValueError("invalid separator position")

    hrp = addr[:pos]
    data_part = addr[pos + 1:]

    if not hrp:
        raise ValueError("empty HRP")

    data = []
    for c in data_part:
        if c not in CHARSET_REV:
            raise ValueError("invalid character in data part")
        data.append(CHARSET_REV[c])

    if not _verify_checksum_bech32m(hrp, data):
        raise ValueError("invalid Bech32m checksum")

    # Strip checksum (last 6 symbols)
    return hrp, data[:-6]


def convertbits(data, frombits: int, tobits: int, pad: bool = True):
    """
    General power-of-2 base conversion.
    Used to convert 8-bit bytes <-> 5-bit Bech32 values.

    `data` is an iterable of integers.
    """
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1

    for value in data:
        if value < 0 or (value >> frombits) != 0:
            raise ValueError("convertbits: invalid value")
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)

    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    else:
        if bits >= frombits:
            # leftover bits are enough to encode a full symbol → invalid
            raise ValueError("convertbits: invalid padding")
        if (acc << (tobits - bits)) & maxv:
            # leftover bits would encode a non-zero symbol → invalid
            raise ValueError("convertbits: non-zero padding")

    return ret


# ---- Dash Platform address encoding on top of Bech32m ----

Network = Literal["mainnet", "testnet"]
AddrType = Literal["p2pkh", "p2sh"]

NETWORK_TO_HRP = {
    "mainnet": "dashevo",
    "testnet": "tdashevo"
}

HRP_TO_NETWORK = {v: k for k, v in NETWORK_TO_HRP.items()}

TYPE_TO_BYTE = {
    "p2pkh": 0x00,
    "p2sh": 0x01,
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

    return bech32m_encode(hrp, data5)


def decode_platform_address(addr: str) -> Tuple[Network, AddrType, bytes]:
    """
    Decode a Dash Platform Bech32m address into (network, addr_type, hash160).

    :param addr: Bech32m-encoded Dash Platform address
    :return: (network, "p2pkh"/"p2sh", 20-byte hash160)
    """
    hrp, data_no_checksum = bech32m_decode(addr)

    if hrp not in HRP_TO_NETWORK:
        raise ValueError(f"unknown HRP '{hrp}' for Dash Platform")

    network = HRP_TO_NETWORK[hrp]

    # Convert back to 8-bit payload, without padding
    payload_bytes = bytes(convertbits(data_no_checksum, 5, 8, pad=False))

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
        "dashevo1qrma5z3ttj75la4m93xcndna9ullamq9y5smxxxm",
        "tdashevo1qrma5z3ttj75la4m93xcndna9ullamq9y5aawfeu",
    ),
    # Vector 2: m/9'/5'/17'/0'/0'/1
    (
        [9 + H, 5 + H, 17 + H, 0 + H, 0 + H, 1],
        "eef58ce73383f63d5062f281ed0c1e192693c170fbc0049662a73e48a1981523",
        "02269ff766fcd04184bc314f5385a04498df215ce1e7193cec9a607f69bc8954da",
        "a5ff0046217fd1c7d238e3e146cc5bfd90832a7e",
        "dashevo1qzjl7qzxy9lar37j8r37z3kvt07epqe20clcut89",
        "tdashevo1qzjl7qzxy9lar37j8r37z3kvt07epqe20cj75ycz",
    ),
    # Vector 3: m/9'/5'/17'/0'/1'/0 (key_class' = 1')
    (
        [9 + H, 5 + H, 17 + H, 0 + H, 1 + H, 0],
        "cc05b4389712a2e724566914c256217685d781503d7cc05af6642e60260830db",
        "0317a3ed70c141cffafe00fa8bf458cec119f6fc039a7ba9a6b7303dc65b27bed3",
        "6d92674fd64472a3dfcfc3ebcfed7382bf699d7b",
        "dashevo1qpkeye606ez89g7lelp7hnldwwpt76va0vcv050v",
        "tdashevo1qpkeye606ez89g7lelp7hnldwwpt76va0v428mst",
    ),
]

# DIP-18 P2SH vector (address encoding only, no derivation path)
P2SH_VECTOR = (
    "43fa183cf3fb6e9e7dc62b692aeb4fc8d8045636",
    "dashevo1q9pl5xpu70aka8nacc4kj2htflydspzkxckndrac",
    "tdashevo1q9pl5xpu70aka8nacc4kj2htflydspzkxcm49vzl",
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
