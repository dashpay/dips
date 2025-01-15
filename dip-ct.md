<pre>
  DIP: XXX
  Title: Confidential Transactions
  Author: Duke Leto
  Comments-Summary: No comments yet.
  Status: In Progress
  Type: Consensus
  Created: 2024-08-13
  License: MIT License
</pre>

## Table of Contents

1. [Abstract](#abstract)
1. [Motivation](#motivation)
1. [Conventions](#conventions)
1. [Prior Work](#prior-work)
1. [Consensus Protocol Changes](#consensus-protocol-changes)
1. [References](#references)
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

One of the large differences between Dash and Monero is the Elliptic Curve each is based on. Dash uses secp256k1 (defined by `y^2 = x^3 + 7` in "Standards For Efficient Cryptography")
which is inherited from Bitcoin Core while Monero uses the Curve25519 curve defined by `y^2 = x^3 + 486662*x^2 + x` created by Daniel J. Berstein. To quote the original Bulletproof paper "Bulletproofs are zero-knowledge arguments of knowledge" i.e. they are a generalized mathematical tool that can be used in many different ways with many different cryptographic systems. In particular, they do not require a specific elliptic curve to be used with them. This is why both Bitcoin and Monero can use Bulletproofs even though they use different elliptic curves. There exists a fork of libsecp256k1 called libsecp256k1-zkp which contains code to do Bulletproofs on the secp256k1 curve that the Dash community most likely will want to use.

## Details

This DIP documents how Dash can add CTs using Bulletproofs (BPs). The type of CT we propose using has two main parts, a signature and a Bulletproof. The Bulletproof (a type of range proof) proves that the signature is valid, in particular, that it's values are in between a certain valid range. This prevents an underflow or overflow of values that could be used to subvert the system. Bulletproofs are a type of Non-Interactive Zero Knowledge proof. They prove that the values are valid or invalid without leaking any information about the values themselves.

### Confidential addresses (CT addresses)

New Dash CTs will need a new type of address, a confidential address, to send and receive CT transactions. This means that the Dash full node will require new RPCs to create, validate, list and import confidential addresses. A prefix of `Dash` will be used for these addresses so they can easily be differentiated from other Dash addresses and from Confidential Addresses on other blockchains. These addresses will be new data in wallet.dat and the code which reads and writes wallet.dat will need to also be updated to store and retrieve this data. The code which rescans blockchain history for transactions belonging to the current wallet will also need to be updated. To detect if a UTXO is owned by the current wallet, full nodes will use the Confidential Address public key along with the salt corresponding to that public key to inspect every UTXO to see if is an output owned by the wallet.

These new CT addresses require a different base58 prefix to identify them as different from traditional Dash addresses and the prefix `Dash` is proposed.

The exact structure of a CT address is as follows. It contains the following data:

  * salt (AKA blinding key) . 32 byte random value
  * pk . The compressed public key, a 33 byte secp256k1 curve point.

For HD wallets, a master 32 byte salt (blinding key) is stored from which all blinding keys for generated addresses are derived.

To clarify, the public key can actually be stored in 32 bytes and one bit, because a point on the curve is a pair of 32 byte numbers (x,y). If x is known, y is almost uniquely identified, since for each `x` there are two `y` values, for exactly the same reason why `x^2 = 4` has two solutions, +2 and -2 . Since secp256k1 is symmetric about the x-axis, one bit can be used to say if the y value is above or below the x axis.

  The salt is 32 bytes because it is used to "blind" the x value of a (x,y) point on the curve which is 32 bytes. The compressed public key is 33 bytes (or 32 bytes and one bit) as described above and in the "Compressed Public Keys" section of Chapter 4 of "Mastering Bitcoin".


A base58 CT address can be then generated via

```
address = base58( RIPEMD160( SHA256( salt + pk ) ) )
```

where `+` denotes concatenation. This is described in more detail in the section "Legacy Addresses for P2PKH" of Chapter 4 of "Mastering Bitcoin". This assumes Confidential UTXOs will be stored in P2PKH format.

### Confidential transactions

A Confidential Transaction contains the following data :

  * A 33 byte Pedersen commitment to the amount being transferred for each output
  * A BP rangeproof for each output that ensures the amount transferred is inside a certain interval between 0 and 2^N - 1
    * To support all potential value transfers between 0 and 21M the BP rangeproof needs N equal to 52
    * The exact size of the proof depends on the number of inputs and outputs
  * An explicit fee, since the fee cannot be computed by the network since the amount is hidden
  * A list of input UTXOs
  * A list of one or more output addresses
    * These may be normal or CT addresses

This DIP proposes using DIP-2 Special Transactions to store and implement Confidential Transactions. This means storing data in the `extra_payload` field of existing Dash transactions and Special Transaction `type` of 10, the currently next unused value of this field. If a transaction contains any non-Confidential inputs or outputs then that data is stored in normal (non-Special) transaction data. The following describes how the confidential inputs and outputs of a transaction can be stored via `extra_payload`. 

#### Variable Length Integer (VarInt)

This data type is derived from Bitcoin, and allows an integer to be encoded with a variable length (which depends on the represented value), in order to save space.
Variable length integers always precede a vector of a type of data that may vary in length and are used to indicate this length.
Longer numbers are encoded in little-endian.

| Value | Size | Format | Example |
| ----- | ---- | ------ | ------- |
| < `0xFD` | 1 byte | `uint8_t` | `0x0F` = 15 |
| <= `0xFFFF` | 3 bytes | `0xFD` followed by the number as a `uint16_t` | `0xFD 00FF` = 65 280 |
| <= `0xFFFF FFFF` | 5 bytes | `0xFE` followed by the number as a `uint32_t` | `0xFE 0000 00FF` = 4 278 190 080 |
| <= `0xFFFF FFFF FFFF FFFF` | 9 bytes | `0xFF` followed by the number as a `uint64_t` | `0xFF 0000 0000 0000 00FF` = 18 374 686 479 671 623 680 |

#### Vector\<Type\>

Each `Vector` begins with a `VarInt` describing the number of items it contains.

If the vector is of type `hex`, then the size / structure of each individual item is not known in advance. In this case, each item begins with a `VarInt` describing its size `s` in bytes, followed by `s` bytes which should be interpreted as the item itself.
Otherwise, size prefixes are omitted, and each item should be interpreted in accordance with the vector's type.

In other words, the vector is serialized as follows: `[Length (n)][Item #1][Item #2][...][Item #n]`.

#### extra_payload

The structure of `extra_payload` is :

| Field | Type | Size | Description |
| ----- | ---- | ---- | ----------- |
|numTxInputs| VarInt | varies | Number of confidential inputs|
| txInputs| Vector<TxInput>| 33*numTxInputs bytes| Confidential transaction inputs |
|numTxOutputs| VarInt | varies | Number of confidential outputs |
| txOutputs | Vector<TxOutput>| 33*numTxOutputs bytes| Confidential transaction outputs |
| proof |ConfidentialProof| Varies | Confidential proof data |

The structure of `txInputs` is : 

...

The structure of `txOutputs` is : 

| Field | Type | Size | Description |
| ----- | ---- | ---- | ----------- |
| amount|ConfidentialAmount| 33 bytes| The confidential amount being transferred |
| nonce |ConfidentialNonce| 33 bytes| The confidential nonce |
| proof |ConfidentialProof| Varies | The rangeproof that the confidential amount being transferred is valid |

The following data structures have been adapted from the Elements Project Transaction format:

#### ConfidentialAmount

| Field | Required | Size | Data Type | Encoding | Notes |
| ----- | -------- | ---- | --------- | -------- | ----- |
| Header | Yes | 1 byte | | | A header byte of `0x08` or `0x09` indicates a blinded value encoded as a compressed elliptic curve point. With the least significant bit of the header byte denoting the least significant bit of the y-coordinate, and the remaining 32 bytes denoting the x-coordinate (big-endian). The point must be a point on the secp256k1 curve. |
| Value | If header byte is not `0x00` | 8 or 32 bytes | `hex` | Big-endian | |

#### ConfidentialNonce

| Field | Required | Size | Data Type | Encoding | Notes |
| ----- | -------- | ---- | --------- | -------- | ----- |
| Header | Yes | 1 byte | | | A header byte of `0x02` or `0x03` indicates a compressed elliptic curve point. With the least significant bit of the header byte denoting the least significant bit of the y-coordinate, and the remaining 32 bytes denoting the x-coordinate (big-endian). This point is not required to be on the curve. |
| Value | If header byte is not `0x00` | 32 bytes | `hex` | Big-endian | |

#### ConfidentialProof

| Field | Required | Size | Data Type | Encoding | Notes |
| ----- | -------- | ---- | --------- | -------- | ----- |
| Length | Yes | Varies | `VarInt` | | `0x00` → null. |
| Value | If header byte is not `0x00` | Varies | `hex` | Big-endian | Bulletproof which proves that the ConfidentialAmount is within the range of 0 and `2^52 - 1` |


#### Pedersen Commitments

A Pedersen commitment can be thought of as a sealed box which is tamper-proof and contains a secret. A physical example of this would be for Alice to seal a message `M` inside an envelope along with a peice of carbon paper, then getting Bob to sign the outside of the envelope, so that the carbon paper copies his signature onto the message `M`. Later on Alice can open the envelope and both Alice and Bob can be assured that the secret message `M` was not changed.

Mathematically a Pedersen commitment (written in additive notation) is defined as

```
P(v,s) = v*G + s*Q
```

where

  * P(v,s) means P is a function of the variables v and s
  * v is a value to be committed
  * s is a salt AKA blinding factor
  * G and Q are elliptic curve points on secp256k1 both known to committer and verifier
      * The committer is the creator of a transaction
      * The verifier is any node which processes the transaction to see if it is valid
  * x*Y means multiplication of value x by curve point Y
    * In some references multiplication is implicit, i.e. x*Y = xY
   
In multiplicative notation the above would be `P(v,s) = G^v*Q^s` where `^` denotes exponentiation. Both notations are describing the exact same equivalent mathematics where additive notation is using `+` as the group operator while multiplicative notation is using `*`. In additive notation `n*G` is equivalent to `G^n` in multiplicative notation. 

Capital letters are curve points (P, G, Q, Y above) while lowercase letters are arbitrary integers (v, s and x above). Some references including the original paper by Pedersen use multiplicative notation. Additive notation is usually used with Abelian Groups, i.e. those where `A + B = B + A` or `A*B=B*A`. Given two points on the elliptic curve secp256k1 `G` and `Q`, we can add them in any order, which is to say `G + Q = Q + G`.

G and Q MUST be randomly chosen curve points such that the `d` in

```
Q = d*G
```

is unknown, which is equivalent to

```
d = Log Q
```

is unknown. In multiplicative notation: 
```
Q = G^d
```

and taking the discrete logarithm with respect to `G` of both sides we get `Log Q = Log (G^d) = d*Log(G) = d` where we have used the facts that `Log(a^b) = b*Log(a)` and `Log(G) = 1` in base `G`.

`d` is called the Discrete Logarithm of `Q` with respect to `G` (or the Discrete Logarithm of `Q` in base `G`). We use the notation `Log` instead of `log` to denote the fact that a discrete logarithm is a different function from the traditional logarithm denoted `log` . The function `Log` and `log` share the same types of properties and identities which is why `Log` is considered the discrete analog of `log`.

The Discrete Logarithm Problem (DLP) means that if `Q = d*G` (or `Q = G^d` in multiplicative notation) then while `d` does exist, it is computationally infeasible to calculate it. The security of Pedersen commitments is based on the hardness assumption that the DLP on appropriately chosen elliptic curves have no efficient algorithm to find a solution.


### New consensus rules for CTs

The activation of these new consensus rules will be block height activated, i.e. a block height which enables Confidential Transactions will be chosen, which we will call `heightCT`. If the block height of the full node is less than `heightCT` then the following consensus rules will not be active. When the block reaches `heightCT` these rules will become active.

  * If height is at least `heightCT` and if at least one input of a CT is confidential, at least one of the outputs must also be confidential. This prevents metadata leaking about the exact amount in a confidential output. A confidential output may have an amount equal to zero.
  * If height is at least `heightCT` and if all inputs are public, i.e. not confidential, the number of confidential outputs must be zero or greater than or equal to two, i.e. having all public inputs with a single confidential output is not allowed, as it leaks the metadata about exactly how much value is in the confidential output.
  * If height is less than `heightCT` then Special Transaction type 10 is invalid


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
  * Elements Confidential Transactions https://github.com/ElementsProject/elements/blob/master/doc/elements-confidential-transactions.md
  * Elements Confidential Addresses https://elementsproject.org/features/confidential-transactions/addresses
  * "SLIP-0077 : Deterministic blinding key derivation for Confidential Transactions"
https://github.com/satoshilabs/slips/blob/master/slip-0077.md
  * "Non-Interactive and Information-Theoretic Secure Verifiable Secret Sharing" Advances in Cryptology 1991, Torben Pryds Pedersen https://link.springer.com/chapter/10.1007/3-540-46766-1_9
  * What Are Pedersen Commitments And How They Work https://www.rareskills.io/post/pedersen-commitment
  * Mastering Bitcoin, Chapter 4, Keys https://github.com/bitcoinbook/bitcoinbook/blob/develop/ch04_keys.adoc
  * secp256k1 "Standards For Efficient Cryptography" https://www.secg.org/sec2-v2.pdf
  * Curve25519, Daniel J Bernstein https://cr.yp.to/ecdh/curve25519-20060209.pdf
  * Cryptanalysis Of Number Theoretic Ciphers. Samuel S. Wagstaff, Jr. 2003

## Copyright

[Licensed under MIT License](https://opensource.org/licenses/MIT)
