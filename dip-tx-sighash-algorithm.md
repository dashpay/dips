<pre>
DIP: tx-sighash-algorithm
Title: A new transaction signature hash algorithm
Authors: panleone
Status: Draft
Layer: Consensus (hard fork)
Created: 2024-02-24
License: MIT License
</pre>

## Table of Contents

* [Abstract](#abstract)
* [Prior Work](#prior-work)
* [Motivation](#motivation)
* [Specification](#specification)
* [Implementation](#implementation)
* [Deployment](#deployment)
* [Test](#test)
* [Copyright](#copyright)

## Abstract

This DIP describes a new algorithm to compute the sighash of a transaction, which is the sequence of bytes that is signed using ECDSA. Compared to the previous algorithm, this one is faster and requires less data hashing.

## Prior Work

* [BIP-0143: Transaction Signature Verification for Version 0 Witness Program](https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki)
* [DIP-0002: Special Transactions](https://github.com/dashpay/dips/blob/master/dip-0002.md)
* [DIP-0023: Enhanced Hard Fork Mechanism](https://github.com/dashpay/dips/blob/master/dip-0023.md)

## Motivation

There are 4 ECDSA signature verification codes in the original DASH script system: `CHECKSIG`, `CHECKSIGVERIFY`, `CHECKMULTISIG`, `CHECKMULTISIGVERIFY` (“sigops”). According to the sighash type (`ALL`, `NONE`, `SINGLE`, `ANYONECANPAY`), a transaction digest is generated with a double SHA256 of a serialized subset of the transaction, and the signature is verified against this digest with a given public key.

Unfortunately, there are at least 2 weaknesses in the original Signature Hash transaction digest algorithm:

* For the verification of each signature, the amount of data hashing is proportional to the size of the transaction. Therefore, data hashing grows in O(n<sup>2</sup>) as the number of sigops in a transaction increases. This could be fixed by optimizing the digest algorithm by introducing some reusable “midstate”, so the time complexity becomes O(n).
* The algorithm does not involve the amount of Dash being spent by the input. This is usually not a problem for online network nodes as they could request the specified transaction to acquire the output value. For an offline transaction signing device (cold wallet), however, not knowing the input amount makes it impossible to calculate the exact amount being spent and the transaction fee. To cope with this problem, a cold wallet must also acquire the full transaction being spent, which could be a big obstacle in the implementation of a lightweight, air-gapped wallet. By including the input value as part of the transaction digest, a cold wallet may safely sign a transaction by learning the value from an untrusted source. In the case that a wrong value is provided and signed, the signature would be invalid and no funding would be lost. See [SIGHASH_WITHINPUTVALUE: Super-lightweight HW wallets and offline data](https://bitcointalk.org/index.php?topic=181734.0).

## Specification

A new sighash type, `SIGHASH_DIP0143`, will be added and the proposed algorithm must be applied only to individual transaction inputs that contain it. The algorithm consists in computing the signature hash of a transaction as the double SHA256 of the serialization of:

1. nVersion of the transaction (2-byte integer)
2. nType of the transaction (2-byte integer)
3. hashPrevouts (32-byte hash)
4. hashSequence (32-byte hash)
5. outpoint (32-byte hash + 4-byte index)
6. scriptCode of the input (serialized as pk_script inside CTxOuts)
7. value of the output spent by this input (8-byte int64_t)
8. nSequence of the input (8-byte int64_t)
9. hashOutputs (32-byte hash)
10. vExtraPayload of the transaction (only if transaction is [special](https://github.com/dashpay/dips/blob/master/dip-0002.md#special-transactions))
11. nLockTime of the transaction (4-byte uint32_t)
12. sighash type of the signature (4-byte uint32_t)

Items 1, 2, 8, 11, 12 are usual fields of any transaction.

Item 5 is the `outpoint` of the input being signed.

Item 7 is the `value` in dash spent by the input being signed.

Item 10 is the extra payload of a transaction: 
* It must be included only if the transaction is special
* A transaction is special if its `nVersion` is greater or equal to `3` and its `nType` is different from `0`, see  [DIP-0002](https://github.com/dashpay/dips/blob/master/dip-0002.md) for more details.

For item 6 let's call `script` the script being executed, so the `scriptPubKey` of the `UTXO` spent by the input being signed. Then the `scriptCode` is computed as:
* If the `script` does not contain any `OP_CODESEPARATOR`, the `scriptCode` is the `script` serialized as scripts inside `CTxOut`.
* If the `script` contains any `OP_CODESEPARATOR`, the `scriptCode` is the `script` but removing everything up to and including the last executed `OP_CODESEPARATOR` before the signature checking opcode being executed, serialized as scripts inside `CTxOut`.
* Notice that, unlike the previous algorithm, all `OP_CODESEPARATOR` after the last executed one are not removed.

All other items are computed depending on the `sighash` type:

Item 3 `hashPrevouts`:

* If the `ANYONECANPAY` flag is not set, `hashPrevouts` is the double SHA256 of the serialization of all input `outpoints`;
* Otherwise, `hashPrevouts` is a `uint256` of `0x0000......0000`.

Item 4 `hashSequence`:

* If none of the `ANYONECANPAY`, `SINGLE`, `NONE` sighash type is set, `hashSequence` is the double SHA256 of the serialization of `nSequence` of all inputs;
* Otherwise, `hashSequence` is a `uint256` of `0x0000......0000`.

Item 9 `hashOutputs`:

* If the sighash type is neither `SINGLE` nor `NONE`, `hashOutputs` is the double SHA256 of the serialization of all output `values` (8-byte int64_t) paired up with their `scriptPubKey` (serialized as scripts inside `CTxOuts`);
* If sighash type is `SINGLE` and the input `index` is smaller than the number of outputs, `hashOutputs` is the double SHA256 of the output `amount` with `scriptPubKey` of the same `index` as the input;
* Otherwise, `hashOutputs` is a `uint256` of `0x0000......0000`.

## Implementation

The actual implementation of the new algorithm is the following:

```cpp
int32_t n32bitVersion = txTo.nVersion | (txTo.nType << 16);
uint256 hashPrevouts;
uint256 hashSequence;
uint256 hashOutputs;

if (!(nHashType & SIGHASH_ANYONECANPAY)) {
    hashPrevouts = GetPrevoutsHash(txTo);
}

if (!(nHashType & SIGHASH_ANYONECANPAY) && (nHashType & 0x1f) != SIGHASH_SINGLE && (nHashType & 0x1f) != SIGHASH_NONE) {
    hashSequence = GetSequencesHash(txTo);
}

if ((nHashType & 0x1f) != SIGHASH_SINGLE && (nHashType & 0x1f) != SIGHASH_NONE) {
    hashOutputs = GetOutputsHash(txTo);
} else if ((nHashType & 0x1f) == SIGHASH_SINGLE && nIn < txTo.vout.size()) {
    CHashWriter ss(SER_GETHASH, 0);
    ss << txTo.vout[nIn];
    hashOutputs = ss.GetHash();
}

CHashWriter ss(SER_GETHASH, 0);

// Version and type
ss << n32bitVersion;
// Input prevouts/nSequence (none/all, depending on flags)
ss << hashPrevouts;
ss << hashSequence;
// The input being signed (replacing the scriptSig with scriptCode + amount)
// The prevout may already be contained in hashPrevout, and the nSequence
// may already be contain in hashSequence.
ss << txTo.vin[nIn].prevout;
ss << scriptCode;
ss << amount;
ss << txTo.vin[nIn].nSequence;
// Outputs (none/one/all, depending on flags)
ss << hashOutputs;
// Extra payload
if (txTo.IsSpecialTxVersion() && txTo.nType != TRANSACTION_NORMAL) {
    ss << txTo.vExtraPayload;
}
// Locktime
ss << txTo.nLockTime;
// Sighash type
ss << nHashType;

return ss.GetHash();
```

Where the three internal functions are defined as:

```cpp
/** Compute the double SHA256 of the concatenation of all prevouts of a tx. */
uint256 GetPrevoutsHash(const T& txTo){
    CHashWriter ss(SER_GETHASH, 0);
    for (const auto& txin : txTo.vin) {
        ss << txin.prevout;
    }
    return ss.GetHash();
}

/** Compute the double SHA256 of the concatenation of all nSequences of a tx. */
uint256 GetSequencesHash(const T& txTo){
    CHashWriter ss(SER_GETHASH, 0);
    for (const auto& txin : txTo.vin) {
        ss << txin.nSequence;
    }
    return ss.GetHash();
}

/** Compute the double SHA256 of the concatenation of all txouts of a tx. */
uint256 GetOutputsHash(const T& txTo){
    CHashWriter ss(SER_GETHASH, 0);
    for (const auto& txout : txTo.vout) {
        ss << txout;
    }
    return ss.GetHash();
}
```

## Deployment

This DIP will be deployed using an EHF-based hard fork as described in [DIP-0023](https://github.com/dashpay/dips/blob/master/dip-0023.md).
In particular a new script flag `SCRIPT_ENABLE_DIP0143` will be added and will be included in script verification only if the corresponding EHF is active. If the flag is not included, transactions with any input that contains `SIGHASH_DIP0143` must be rejected.

## Test

To ensure consistency in consensus-critical behaviour, developers should test their implementations against the test below.

```text
  The following is an unsigned transaction:
    030001000201168d635fbfd7df3a380a30dda5a4cf2d160ad47cc9614ac9f4e827f8876e260000000000ffffffff012da8dc79c177e8deffc3e95308cda74baac13c5bcfbe4010af709dbe0c2bb10000000000ffffffff0100e87648170000001976a9143c6fcdbbbc624fa338ae6479c90a566c95aace2188ac00000000d101000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff010101010001bfdbab50700059afde9b7ec485793912b78c368182e0c153b845bc7c086b8ee9d2d070b163533faa2d51621ea054dc753095cb2753490d6afbc00aae77f80cefca4d9962bfdbab50700059afde9b7ec485793912b78c368100001976a9143c6fcdbbbc624fa338ae6479c90a566c95aace2188acb319b02a1a470620de59efc71832eea117579e4a80de0db2f3fafd1df0710b3e00
    
    nVersion:      0300
    nType:         0100
    txin:          02 01168d635fbfd7df3a380a30dda5a4cf2d160ad47cc9614ac9f4e827f8876e26   00000000 00 ffffffff
                      012da8dc79c177e8deffc3e95308cda74baac13c5bcfbe4010af709dbe0c2bb1   00000000 00 ffffffff
    txout:         01 00e8764817000000 1976a9143c6fcdbbbc624fa338ae6479c90a566c95aace2188ac
    nLockTime:     00000000
    vExtraPayload: d101000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff010101010001bfdbab50700059afde9b7ec485793912b78c368182e0c153b845bc7c086b8ee9d2d070b163533faa2d51621ea054dc753095cb2753490d6afbc00aae77f80cefca4d9962bfdbab50700059afde9b7ec485793912b78c368100001976a9143c6fcdbbbc624fa338ae6479c90a566c95aace2188acb319b02a1a470620de59efc71832eea117579e4a80de0db2f3fafd1df0710b3e00
  
  Both input comes from an ordinary P2PKH and they have the same scriptPubKey and value:
    scriptPubKey : 210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798ac
    value:         50000000000
    
  Let's sign the first input with a nHashType of 1 + 64 (SIGHASH_ALL | SIGHASH_DIP0143):
  
  hashPrevouts:
    dSHA256(01168d635fbfd7df3a380a30dda5a4cf2d160ad47cc9614ac9f4e827f8876e2600000000012da8dc79c177e8deffc3e95308cda74baac13c5bcfbe4010af709dbe0c2bb100000000)
  = b319b02a1a470620de59efc71832eea117579e4a80de0db2f3fafd1df0710b3e
  
  hashSequence:
    dSHA256(ffffffffffffffff)
  = 752adad0a7b9ceca853768aebb6965eca126a62965f698a0c1bc43d83db632ad
  
  hashOutputs:
    dSHA256(00e87648170000001976a9143c6fcdbbbc624fa338ae6479c90a566c95aace2188ac)
  = 4718f33fc0431a07c1dedd83a209093c217643cc61d7880c5780039f6b0d1fc8
  
  hash preimage: 03000100b319b02a1a470620de59efc71832eea117579e4a80de0db2f3fafd1df0710b3e752adad0a7b9ceca853768aebb6965eca126a62965f698a0c1bc43d83db632ad01168d635fbfd7df3a380a30dda5a4cf2d160ad47cc9614ac9f4e827f8876e260000000023210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798ac00743ba40b000000ffffffff4718f33fc0431a07c1dedd83a209093c217643cc61d7880c5780039f6b0d1fc8d101000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff010101010001bfdbab50700059afde9b7ec485793912b78c368182e0c153b845bc7c086b8ee9d2d070b163533faa2d51621ea054dc753095cb2753490d6afbc00aae77f80cefca4d9962bfdbab50700059afde9b7ec485793912b78c368100001976a9143c6fcdbbbc624fa338ae6479c90a566c95aace2188acb319b02a1a470620de59efc71832eea117579e4a80de0db2f3fafd1df0710b3e000000000041000000
  
    nVersion:      0300
    nType:         0100
    hashPrevouts:  b319b02a1a470620de59efc71832eea117579e4a80de0db2f3fafd1df0710b3e
    hashSequence:  752adad0a7b9ceca853768aebb6965eca126a62965f698a0c1bc43d83db632ad
    outpoint:      01168d635fbfd7df3a380a30dda5a4cf2d160ad47cc9614ac9f4e827f8876e2600000000
    scriptCode:    23210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798ac
    amount:        00743ba40b000000
    nSequence:     ffffffff
    hashOutputs:   4718f33fc0431a07c1dedd83a209093c217643cc61d7880c5780039f6b0d1fc8
    vExtraPayload: d101000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff010101010001bfdbab50700059afde9b7ec485793912b78c368182e0c153b845bc7c086b8ee9d2d070b163533faa2d51621ea054dc753095cb2753490d6afbc00aae77f80cefca4d9962bfdbab50700059afde9b7ec485793912b78c368100001976a9143c6fcdbbbc624fa338ae6479c90a566c95aace2188acb319b02a1a470620de59efc71832eea117579e4a80de0db2f3fafd1df0710b3e00
    nLockTime:     00000000
    nHashType:     41000000
    
  sigHash:      fa269593a2ad3130a07591abff4c973f0ddb0da5651c2e072594586ec1f3811c
  signature:    473044022013d7705c458dea1d1b125d1f8b1c46aa567f8e94eb2e1255d2cc0f774fee8875022054a7f616049ef7e61abf8c9792a49c22412186629674b81f08c6a88a5a14c64b41
    
  The serialized signed transaction is: 030001000201168d635fbfd7df3a380a30dda5a4cf2d160ad47cc9614ac9f4e827f8876e260000000048473044022013d7705c458dea1d1b125d1f8b1c46aa567f8e94eb2e1255d2cc0f774fee8875022054a7f616049ef7e61abf8c9792a49c22412186629674b81f08c6a88a5a14c64b41ffffffff012da8dc79c177e8deffc3e95308cda74baac13c5bcfbe4010af709dbe0c2bb10000000000ffffffff0100e87648170000001976a9143c6fcdbbbc624fa338ae6479c90a566c95aace2188ac00000000d101000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff010101010001bfdbab50700059afde9b7ec485793912b78c368182e0c153b845bc7c086b8ee9d2d070b163533faa2d51621ea054dc753095cb2753490d6afbc00aae77f80cefca4d9962bfdbab50700059afde9b7ec485793912b78c368100001976a9143c6fcdbbbc624fa338ae6479c90a566c95aace2188acb319b02a1a470620de59efc71832eea117579e4a80de0db2f3fafd1df0710b3e00
  
    nVersion:      0300
    nType:         0100
    txin:          02 01168d635fbfd7df3a380a30dda5a4cf2d160ad47cc9614ac9f4e827f8876e26 00000000 48473044022013d7705c458dea1d1b125d1f8b1c46aa567f8e94eb2e1255d2cc0f774fee8875022054a7f616049ef7e61abf8c9792a49c22412186629674b81f08c6a88a5a14c64b41 ffffffff
                      012da8dc79c177e8deffc3e95308cda74baac13c5bcfbe4010af709dbe0c2bb1 00000000 00 ffffffff
    txout:         01 00e8764817000000 1976a9143c6fcdbbbc624fa338ae6479c90a566c95aace2188ac
    vExtraPayload: d101000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff010101010001bfdbab50700059afde9b7ec485793912b78c368182e0c153b845bc7c086b8ee9d2d070b163533faa2d51621ea054dc753095cb2753490d6afbc00aae77f80cefca4d9962bfdbab50700059afde9b7ec485793912b78c368100001976a9143c6fcdbbbc624fa338ae6479c90a566c95aace2188acb319b02a1a470620de59efc71832eea117579e4a80de0db2f3fafd1df0710b3e00
    nLockTime:     00000000
```

## Copyright

This document is licensed under the [MIT License](https://opensource.org/licenses/MIT).