<pre>
  DIP: aj-wallet-id
  Title: Wallet, XPub, & HD Key IDs
  Authors: coolaj86
  Special-Thanks: Rion Gull
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2023-07-14
  License: CC0-1.0
</pre>

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Abstract](#abstract)
- [Prior Art](#prior-art)
- [Motivation](#motivation)
- [Specification](#specification)
  - [Example](#example)
  - [Pseudocode](#pseudocode)
- [Copyright](#copyright)

## Abstract

In a single-wallet application an HD Path (`m/44'/5'/0'`) is sufficient for
identifying an account/contact, or address/private key.

However, in multi-Wallet and multi-XPub systems (using multiple Wallet Phrases
or XPubs from multiple contacts) there must be deterministic IDs to associate
the Wallet or XPub to which the HD Path should be applied.

keywords: \
 hdpath, HD Path, recovery phrase, wallet phrase, seed, \
 XPub, X Pub, XPrv, X Prv, HDKey, HD Key, XKey, X Key

## Prior Art

- [Key Identifiers of Hierarchical Deterministic Wallets](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#key-identifiers)
- [Mnemonic code for generating deterministic keys](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
- [Multi-Account Hierarchy for Deterministic Wallets](https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki)
- [Base 64 Encoding with URL and Filename Safe Alphabet](https://datatracker.ietf.org/doc/html/rfc4648#section-5)
- [Crockford Base32](https://www.crockford.com/base32.html)
- [Base 16 Encoding](https://datatracker.ietf.org/doc/html/rfc3548#section-6)

## Motivation

Dash Incubator is working on multiple user- and merchant-focused projects where
multiple wallets may need to be cached offline locally and synchronized online.

Similarly, as mentioned in
[Hierarchical Deterministic Wallets: Key Identifiers](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#key-identifiers),
the 32-bit "Key Identifiers" are prone to collusion and, as such, are not
suitable for these types of applications. \
(also, RIPEMD160 has been found weak and removed from - or never added to - popular
crypto libraries such as `WebCrypto` and `libssl3`)

As such, we need a deterministic, conflict-free Wallet and XPub identifiers to
use pairwise with HD Paths in order to unambiguously identify contacts and
payment addresses.

## Specification

The Wallet ID is a 64-bit integer derived from the SHA-256 hash of the Wallet
Phrase's HD Seed Key (depth-0, level `m`).

This format maintain uniqueness while also providing space- and
compute-efficient compatibility and embedability with wide variety of indexes
and databases.

The ID is NOT suitable as cryptographically secure input for derivation or
encryption.

### For Wallets

1. Produce the `seed` bytes from the Wallet Phrase as per
   [Mnemonic code for generating deterministic keys](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
2. Produce the depth-0 (level `m`) HD Key from the wallet seed.
3. Continue with "For HD Keys"

### For XPubs (& XPrvs)

1. Decode the raw HD Key bytes from the `XPub` (or `XPrv`) `base58check` string
2. Continue with "For HD Keys"

### For HD Keys

1. Take the SHA-256 hash of the `XPub` bytes as per
   [Serialization Format](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#serialization-format)
2. The ID is a slice of the first 8 bytes (64 bits) of the hash.
3. Continue with "Canonical & Acceptable Encodings"

### Canonical & Acceptable Encodings

- The canonical encoding of the ID is URL-safe Base64.
- The following encodings are acceptable for use-case specific formatting:
  - Int64 (Big-Endian bytes)
  - Crockford Base32
  - Hexadecimal

### Example Wallet

Wallet Phrase:

```text
zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong
```

Wallet Salt:

```text
TREZOR
```

Wallet Seed: \
(newlines added for readability)

```text
ac27495480225222079d7be181583751
e86f571027b0497b5b5d11218e0a8a13
332572917f0f8e5a589620c6f15b11c6
1dee327651a14c34e18231052e48c069
```

Wallet Seed Hash:

```text
2a389a901f9b9f726a32740b4954969c
97e677c144564522339f0ce80f2f0428
```

Wallet ID:

```text
64-Bit Int:  7387163383112745200n
Hex:         668479f5443540f0
CB32:        CT27KXA46N0F0
Base64Url:   ZoR59UQ1QPA
```

### Example HD Key

Wallet `ZoR59UQ1QPA @ m/44'/5'/0'/0`

```text
XPrv: xprvA2L7qar7dyJNhxnE47gK5J6cc1oEHQuAk8WrZLnLeHTtnkeyP4w6E
          o6Tt65trtdkTRtx8opazGnLbpWrkhzNaL6ZsgG3sQmc2yS8AxoMjfZ

XPub: xpub6FKUF6P1ULrfvSrhA9DKSS3MA3digsd27MSTMjBxCczsfYz7vcFLn
          bQwjP9CsAfEJsnD4UwtbU43iZaibv4vnzQNZmQAVcufN4r3pva8kTz
```

XPub ID (HD Key ID):

```text
64-Bit Int:  13572668744561724463
Hex:         bc5bce4fe5a60c2f
CB32:        QHDWWKZ5MR62Y
Base64Url:   vFvOT-WmDC8
```

### Pseudocode

- `walletToId`
- `xkeyToId`
- `bytesToId`

```js
/**
 * Convert Wallet Phrase to Seed Bytes and print IDs
 */
async function walletToId(phrase, salt) {
  let seedBytes = await DashPhrase.toSeed(phrase, salt);

  let hdkey = await DashHd.fromSeed(seedBytes);
  let xpubBytes = await DashHd.toXPubBytes(hdkey);

  await bytesToId(seedBytes);
}

/**
 * Convert XPrv or XPub (XKey) to XPub Bytes and print IDs
 */
async function xkeyToId(xkey) {
  let hdkey = await DashHd.fromXKey(xkey);
  let xpubBytes = await DashHd.toXPubBytes(hdkey);

  await bytesToId(xpubBytes);
}

async function bytesToId(bytes) {
  let hashBuffer = await crypto.subtle.digest("SHA-256", bytes);

  let idBuffer = hashBuffer.slice(0, 8);
  let idBytes = new Uint8Array(idBuffer);

  let id = bytesToBase64Url(idBytes);
  let idBase32Crock = base32crockford.encode(idBytes);
  let idHex = bytesToHex(idBytes);
  let idInt64 = BigInt(`0x${idHex}`);

  console.log(id);
  console.log(idBase32Crock);
  console.log(idHex);
  console.log(idInt64);
}
```

```js
let phrase = "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong";
let salt = "TREZOR";

walletToId(phrase, salt);
```

```js
// XPub @ m/44'/5'/0'/0 of the "Zoomonic" Wallet above
let xpub =
  "xpub6FKUF6P1ULrfvSrhA9DKSS3MA3digsd27MSTMjBxCczsfYz7vcFLnbQwjP9CsAfEJsnD4UwtbU43iZaibv4vnzQNZmQAVcufN4r3pva8kTz";

xkeyToId(xpub);
```

## Copyright

Copyright 2023 AJ ONeal.

DIP to Secure Transactions - Patch Data Leak Vulnerability via Deterministic
Index Ordering

Written in 2023 by AJ ONeal <coolaj86@proton.me> \
To the extent possible under law, the author(s) have dedicated all copyright \
and related and neighboring rights to this software to the public domain \
worldwide. This software is distributed without any warranty. \

You should have received a copy of the CC0 Public Domain Dedication along with \
this software. If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.
