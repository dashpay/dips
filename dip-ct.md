<pre>
  DIP: XXX
  Title: Confidential Transactions
  Author: Duke Leto
  Comments-Summary: No comments yet.
  Status: In Progress
  Type: Standard
  Created: 2024-08-13
  License: MIT License
</pre>

## Table of Contents

1. [Abstract](#abstract)
1. [Motivation](#motivation)
1. [Conventions](#conventions)
1. [Prior Work](#prior-work)
1. [Consensus Protocol Changes](#consensus-protocol-changes)
1. [Observation](#observation)
1. [Copyright](#copyright)

## Abstract

We outline a Confidential Transaction scheme for Dash. After deployment and
activation, Dash will be able to make transactions which do not leak
the amount being transferred.

## Motivation

Currently Dash transactions can optionally use CoinJoin to increase the privacy of transactions but it
leaves much to be desired. This is because CoinJoin is a mixing protocol which
is based on amount obfuscation which leaves addresses as public data.

CoinJoin transactions leaks large amounts of transaction metadata which is
accessible via public blockchain data and requires users to learn about various
details and advanced options to use it in a privacy-preserving way. The current
CoinJoin implementation also requires users to wait longer for
increased privacy via more mixing rounds. Most users will have no idea how many rounds they should use or what the implications of this choice will be. This incentivizes users to use fewer mixing
rounds to save time, reducing their privacy as well as the privacy of
all users utilizing CoinJoins.

## Conventions

We will use these abbreviations:
  * BP - Bulletproof, a type of size-optimized rangeproof
  * BP+ - Bulletproof+
  * BP++ - Bulletproof++
  * CT - Confidential Transaction

## Scope

This DIP describes how CT can be implemented via the Dash Full Node,
the implementation details of light wallet servers and clients and other nodes is out of scope.

## Prior Work

There are many different types of CTs. The term originally was used in the context
of Bitcoin in 2013 and has grown to a research field with many flavors of CTs. Monero
currently uses RingCT with Bulletproof+ optimizations and the purpose of this DIP is
to decide exactly which kind of CT is appropriate for Dash. Monero first implemented
RingCT in 2017 and then added Bulletproofs in 2018 which allow for an 80% reduction
in size of transactions, reducing blockchain bloat as well as reducing transaction fees.
A further improvement called Bulletproofs+ was completed in 2022 which further reduces
transaction size by roughly 5-10% and improves speed by 10%. Yet another improvement
called Bulletproofs++ is currently being worked on which further reduces transaction
size and speeds up runtime. Since BP++ is still being actively worked on and has not
yet been merged into Monero and BP+ are still not widely used it is currently recommended for Dash to use BPs.

## Consensus Protocol Changes

This DIP proposes a new transaction type as well as new address types and therefore is a consensus change.

## Overview

One of the large differences between Dash and Monero is the Elliptic Curve each is based on. Dash uses secp256k1
which is inherited from Bitcoin Core while Monero uses the Curve25519 curve. Bulletproofs are curve-agnostic, they can be used with any elliptic curve, but when considering exactly how the code will be implemented and which low-level libraries to use, this becomes important. The Monero implementation of Bulletproofs is specific to the elliptic curve they use and can not easily be ported or used in the Dash codebase.

## Details

This DIP documents how Dash can add CTs using Bulletproofs (BPs). The type of CT we propose using has two main parts, a signature and a Bulletproof. The Bulletproof proves that the signature is valid, in particular, that it's values are in between a certain valid range. This prevents an underflow or overflow of values that could be used to subvert the system. Bulletproofs are a type of Non-Interactive Zero Knowledge proof. They prove that the values are valid or invalid without leaking any information about the values themselves.

### Confidential addresses (CT addresses)

New Dash CTs will need a new type of address, a confidential address, to send and receive CT transactions. This means that the Dash full node will require new RPCs to create, validate, list and import confidential addresses. A prefix will need to be decided upon for these addresses so they can easily be differentiated from other Dash addresses. These addresses will be new data in wallet.dat and the code which reads and writes wallet.dat will need to also be updated to store and retrieve this data. The code which rescans blockchain history for transactions belonging to the current wallet will also need to be updated.

These new CT addresses require a different base58 prefix to identify them as different from traditional Dash addresses.

The exact structure of a CT address is as follows. It contains the following data:

  * salt (AKA blinding factor) . 32 byte random value
  * pk . The public key, a 33 byte secp256k1 curve point

A CT address can be then generated via

```
address = base58( RIPEMD160( SHA256( salt + pk ) ) )
```

where `+` denotes concatenation. 

### Confidential transactions

A confidential transaction contains the following data :

  * A 33 byte Pederson commitment to the amount being transferred
  * A BP rangeproof that ensures the amount transferred is inside a certain interval between 0 and 2^N - 1
    * To support all potential value transfers between 0 and 21M the BP rangeproof needs N equal to 52
    * The exact size of the proof depends on the number of inputs and outputs
  * An explicit fee, since the fee cannot be computed by the network since the amount is hidden
  * A list of input UTXOs
  * A list of one or more output addresses
    * These may be normal or CT addresses

This DIP proposes using DIP-2 Special Transactions to store and implement Confidential Transactions. This means storing data in the `extra_payload` field of existing Dash transactions and Special Transaction `type` of 10, the currently next unused value of this field.

The structure of `extra_payload` is :

| Field | Type | Size | Description |
| ----- | ---- | ---- | ----------- |
| amount|ConfidentialAmount| 9 or 33 bytes| ... |
| nonce |ConfidentialNonce| 33 bytes| ... |
| proof |ConfidentialProof| Varies | ... |

#### ConfidentialAmount

| Field | Required | Size | Data Type | Encoding | Notes |
| ----- | -------- | ---- | --------- | -------- | ----- |
| Header | Yes | 1 byte | | | A header byte of `0x00` indicates a “null” value with no subsequent bytes.<br><br>A header byte of `0x01` indicates an “explicit” value with the following 8 bytes denoting a 64-bit value (big-endian).  This value must be between 0 and `MAX_MONEY` inclusive.<br><br>A header byte of `0x08` or `0x09` indicates a blinded value encoded as a compressed elliptic curve point. With the least significant bit of the header byte denoting the least significant bit of the y-coordinate, and the remaining 32 bytes denoting the x-coordinate (big-endian). The point must be a point on the curve. |
| Value | If header byte is not `0x00` | 8 or 32 bytes | `hex` | Big-endian | |

#### ConfidentialNonce

| Field | Required | Size | Data Type | Encoding | Notes |
| ----- | -------- | ---- | --------- | -------- | ----- |
| Header | Yes | 1 byte | | | A header byte of `0x00` indicates a “null” value with no subsequent bytes.<br><br>A header byte of `0x01` indicates an “explicit” value with the following 32 bytes denoting a value (big-endian).<br><br>A header byte of `0x02` or `0x03` indicates a compressed elliptic curve point. With the least significant bit of the header byte denoting the least significant bit of the y-coordinate, and the remaining 32 bytes denoting the x-coordinate (big-endian). This point is not required to be on the curve. |
| Value | If header byte is not `0x00` | 32 bytes | `hex` | Big-endian | |

#### ConfidentialProof

| Field | Required | Size | Data Type | Encoding | Notes |
| ----- | -------- | ---- | --------- | -------- | ----- |
| Length | Yes | Varies | `VarInt` | | `0x00` → null. |
| Value | If header byte is not `0x00` | Varies | `hex` | Big-endian | Bulletproof which proves that the ConfidentialAmount is within the range of 0 and `MAX_MONEY`|


#### Pederson Commitments

A Pederson commitment can be thought of as a sealed box which is tamper-proof and contains a secret. Mathematically a Pederscon commitment is defined as

```
P(v,s) = v[G] + s[Q]
```

where

  * P(v,s) means P is a function of the variables v and s
  * v is a value to be committed
  * s is a salt AKA blinding factor
  * [G] and [Q] are elliptic curve points on secp256k1 both known to committer and verifier
      * The committer is the creator of a transaction
      * The verifier is any node which processes the transaction to see if it is valid
  * x[Y] means multiplication of value x by curve point [Y]

[G] and [Q] MUST be randomly chosen curve points such that

```
[Q] = d[G]
```

is unknown, which is equivalent to

```
log[G]
```

is unknown. This is known as the Discrete Logarithm Problem (DLP) and the security of Pederson commitments is based on the hardness assumption that the DLP on appropriately chosen elliptic curves have no efficient algorithm to find a solution.


### New consensus rules for CTs

  * If at least one input of a CT is confidential, at least one of the outputs must also be confidential. This prevents metadata leaking about the exact amount in a confidential output. A confidential output may have an amount equal to zero.
  * If all inputs are public, i.e. not confidential, the number of confidential outputs must be zero or greater than or equal to two, i.e. having all public inputs with a single confidential output is not allowed, as it leaks the metadata about exactly how much value is in the confidential output.

## References

  * Original post about Confidential Transactions https://bitcointalk.org/index.php?topic=305791.0
  * RingCT https://eprint.iacr.org/2015/1098
  * BP https://eprint.iacr.org/2017/1066.pdf
  * BP+ https://eprint.iacr.org/2020/735
  * BP++ https://eprint.iacr.org/2022/510
  * BP++ CCS https://ccs.getmonero.org/proposals/bulletproofs-pp-peer-review.html
  * BP++ Audit by CypherStack https://github.com/cypherstack/bppp-review
  * libsecp256k1 https://github.com/bitcoin-core/secp256k1
  * libsecp256k1 Bulletproofs: https://github.com/BlockstreamResearch/secp256k1-zkp/tree/master/src/modules/rangeproof
  * Example of bulletproof API in libsecp256k1 https://github.com/guillaumelauzier/Bulletproofs-libsecp256k1/blob/main/src.cpp
  * Elements Transaction Format https://github.com/ElementsProject/elements/blob/master/doc/elements-tx-format.md

## Copyright

[Licensed under MIT License](https://opensource.org/licenses/MIT)
