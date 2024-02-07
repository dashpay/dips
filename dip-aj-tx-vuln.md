<pre>
  DIP: aj-tx-vuln
  Title: Enforce Secure Deterministic Transaction Indexing
  Authors: coolaj86
  Special-Thanks: Rion Gull
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2023-06-27
  License: CC0-1.0
</pre>

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Abstract](#abstract)
- [Prior Art](#prior-art)
- [Motivation](#motivation)
  - [Transaction Index Vulnerability](#transaction-index-vulnerability)
- [Specification](#specification)
  - [Enforce Secure Deterministic Transaction Indexing](#enforce-secure-deterministic-transaction-indexing)
- [Copyright](#copyright)

## Abstract

This DIP proposes to block transactions from insecure software written with a
security vulnerability by which the indexes of inputs and outputs in a
transaction expose information about the sender(s) and receiver(s).

## Prior Art

- [Lexicographical Indexing of Transaction Inputs and Outputs](https://github.com/bitcoin/bips/blob/master/bip-0069.mediawiki)

## Motivation

I've personally written vulnerable transaction software (on accident), modeling
after transactions that exist in the wild.

I was able to broadcast insecure transactions without any error messages are
warnings.

I've also seen broadcasts which follow an alternate form of lexicographical sort
for outputs (`pubkeyhash` first, rather than amount first)

### Transaction Index Vulnerability

A naive implementation of code that creates transactions leaks data, which then
becomes available to malicious parties / bad actors.

The vulnerability is known, but no protection against it is enforced, so many
applications implementation transaction in a way that exposes a portion of
confidential user details via the list position (array index) of the consumed
inputs and generated outputs.

A typical transaction in vulnerable software is always constructed in this form:

```text
version: 3
inputs: 3
    0.2 pkh1...
    0.5 pkh2...
    1.5 pkh3...
outputs: 3
    1.0 recipient 1 or xpub 1
    0.7 recipient 2 or xpub 1
    0.5 change back to sender
locktime: 0
```

The construction of the transaction includes information related to the user's
actions:

- which addresses likely belong to the recevier(s)
- which XPub-generated addresses are likely linked
- which address is likely change back to the sender
- other statistically related information about the inputs
- the selection algorithm used by the client

A naive algorithm may constructed as follows:

- selection algorithm reveals its sorting (time-based, amount-based, etc)
- receiver address(es) are always the first outputs
- when XPubs are used, addresses related to the same XPub are placed adjacently
- when change is generated, the change address is always in the final position

For example, consider
[598fa5c477ebef8ab74979c8a51d159d8c028b332af973020ec58ec807f009cc](https://insight.dash.org/insight/tx/598fa5c477ebef8ab74979c8a51d159d8c028b332af973020ec58ec807f009cc),
which was selected while sampling transactions at random just minutes ago, and
found to be produced by vulnerable software:

We can know, with very high confidence that:

- there are two recipients
- the sender's change address is `Xf7JKrFdbQaWTZszRsQthm2s4xXCX2uZRb`

## Specification

The default transaction version byte should be bumped from 3 to 4.

All software that verifies transactions should assert that the inputs and
outputs are sorted, completely deterministically, as specified in
"Lexicographical Indexing of Transaction Inputs and Outputs".

Transactions with version 3 or lower SHOULD print a warning and MUST return an
error when vulnerable transactions are detected.

All transactions version 4 or higher MUST be rejected with an error.

### Enforce Secure Deterministic Transaction Indexing

As a recap of "Lexicographical Indexing of Transaction Inputs and Outputs",
although some statistically relevant information is always conveyed in a
transaction, there is a mathematically perfect solution to maximally limit how
much information is made available without any breaking changes to existing
Master Nodes:

Before a transaction is signed:

1. All inputs MUST be sorted ASCENDING by

- previous transaction id `txId`, in (Big-Endian) byte order \
  (NOTE: this is the _REVERSE_ byte order from how they are stored in a transaction)
- previous transaction `vout`, as INTEGER

2. All outputs MUST be sorted ASCENDING by

- `amount` as an INTEGER
- The `script` (a.k.a. 'lock script', 'locking script', 'pubkey script') \
  (NOTE: this is compared in the _SAME_ byte order as written in the transaction)
- The length SHOULD be checked before comparing

As a side benefit, this also makes it possible to index transactions for
efficiently, as all inputs and outputs are pre-sorted in manner compatible with
binary search and JIT-optimization.

Obviously, we can't stop all of this information from being revealed as some of
it is necessary for the transaction, however, this DIP along with other
data-leak vulnerability-focused DIPs can significantly decrease the attack
vector for malicious actors using tools to statistically analysis correlated
data and metadata.

### Example

[63add7757a336b1d9956d0d042956ebad2f643cbd47086738226625da319b698](https://insight.dash.org/insight/tx/63add7757a336b1d9956d0d042956ebad2f643cbd47086738226625da319b698)
is an example of a transaction with multiple inputs and outputs that follow this
algorithm:

```text
version: 2

inputs: 5
    # sorts as 0453f3..., 7
    f8d756d408985d7b eabe611457d3cd08 f847a8c33198dd86 0a57ff10baf35304 (7)

    # sorts as 378dc7..., 4
    2ecc8bacb0fce212 0f7ce2ec99ea7d97 57a15d427601b433 4251bdd0a6c78d37 (4)

    # sorts as bf0d8f..., 3
    7e6e14793b18d458 e0ae8d34f60f35a5 8ab7d43fc11838c0 0b1af6f4ba8f0dbf (3)

    # these two sorts as fd3b22..., 1, 3
    b947c3b1a56556fc 0f8c84e4938becb5 3840da1d1b5f0a44 482a580c20223bfd (1)
    b947c3b1a56556fc 0f8c84e4938becb5 3840da1d1b5f0a44 482a580c20223bfd (3)

outputs: 5
    # sorts as 1000010000 sats, 19 76a9 14 121f...
    10f19a3b00000000
    # Script Size, Script Meta, Script
    19 76a9 14 121f6b8cde5fe2163899 6d4a756ac90b64671c75 88ac

    # sorts as 1000010000 sats, 19 76a9 14 30fde...
    10f19a3b00000000
    19 76a9 14 30fde3dc06aae6075952 fa42a0d1a6b4d0f390d5 88ac

    # sorts as 1000010000 sats, 19 76a9 14 4855...
    10f19a3b00000000
    19 76a9 14 485597ef2b6d53a94d38 4a1ad4c31da87ccfac61 88ac

    # sorts as 1000010000 sats, 19 76a9 14 6930...
    10f19a3b00000000
    19 76a9 14 6930a94e354467dbb6e0 96c0ec6650bad3878c4f 88ac

    # sorts as 1000010000 sats, 19 76a9 14 7b3e...
    10f19a3b00000000
    19 76a9 14 7b3ec1a2370d82e72921 af6a418cc125651404b3 88ac

locktime: 0
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
