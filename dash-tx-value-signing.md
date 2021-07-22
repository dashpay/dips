<pre>
DIP: tx-value-signing
Title: Transaction value signing analogous to BIP143 as implemented in Bitcoin Cash
Authors: greatwolf, mayoree
Status: Draft
Layer: Consensus (hard fork)
Created: 2021-07-03
License: MIT License
</pre>

# Table of Contents

* [Abstract](#abstract)
* [Motivation](#motivation)
* [Specification](#specification)
* [Implementation](#implementation)
* [Test](#test)
* [References](#references)
* [Copyright](#copyright)

# Abstract

This DIP describes a digest algorithm that implements the signature covers value when signing Dash transactions. It opens the path for more efficient signing of Dash transactions on hardware wallets.

The proposed digest algorithm is adapted from BIP143[[1]](#bip143) as it minimizes redundant data hashing in verification, covers the input value by the signature and is already implemented in a wide variety of applications[[2]](#bip143Motivation).

# Motivation

There are 4 ECDSA signature verification codes in the original DASH script system: `CHECKSIG`, `CHECKSIGVERIFY`, `CHECKMULTISIG`, `CHECKMULTISIGVERIFY` (“sigops”). According to the sighash type (`ALL`, `NONE`, `SINGLE`, `ANYONECANPAY`), a transaction digest is generated with a double SHA256 of a serialized subset of the transaction, and the signature is verified against this digest with a given public key.

Unfortunately, there are at least 2 weaknesses in the original Signature Hash transaction digest algorithm:

* For the verification of each signature, the amount of data hashing is proportional to the size of the transaction. Therefore, data hashing grows in O(n<sup>2</sup>) as the number of sigops in a transaction increases. This could be fixed by optimizing the digest algorithm by introducing some reusable “midstate”, so the time complexity becomes O(n).
* The algorithm does not involve the amount of DASH being spent by the input. This is usually not a problem for online network nodes as they could request for the specified transaction to acquire the output value. For an offline transaction signing device (cold wallet"), however, the unknowing of input amount makes it impossible to calculate the exact amount being spent and the transaction fee. To cope with this problem a cold wallet must also acquire the full transaction being spent, which could be a big obstacle in the implementation of lightweight, air-gapped wallet. By including the input value of part of the transaction digest, a cold wallet may safely sign a transaction by learning the value from an untrusted source. In the case that a wrong value is provided and signed, the signature would be invalid and no funding might be lost. <ref>[https://bitcointalk.org/index.php?topic=181734.0 SIGHASH_WITHINPUTVALUE: Super-lightweight HW wallets and offline data]</ref>

# Specification

The proposed digest algorithm computes the double SHA256 of the serialization of:

1. nVersion of the transaction (2-byte uint16_t)
2. hashPrevouts (32-byte hash)
3. hashSequence (4-byte hash)
4. outpoint (32-byte hash + 4-byte index)
5. scriptCode of the input (serialized as pk_script inside CTxOuts)
6. value of the output spent by this input (8-byte int64_t)
7. nSequence of the input (8-byte int64_t)
8. hashOutputs (32-byte hash)
9. nLockTime of the transaction (4-byte uint32_t)
10. sighash type of the signature (4-byte uint32_t)

## nVersion

* This is the transaction number; currently version `3`.

## hashPrevouts

* If the `ANYONECANPAY` flag is not set, `hashPrevouts` is the double SHA256 of the serialization of all input `outpoints`;
* Otherwise, `hashPrevouts` is a `uint256` of `0x0000......0000`.

## hashSequence

* If none of the `ANYONECANPAY`, `SINGLE`, `NONE` sighash type is set, `hashSequence` is the double SHA256 of the serialization of `nSequence` of all inputs;
* Otherwise, `hashSequence` is a `uint256` of `0x0000......0000`.

## outpoint

* Single transactions can include multiple outputs.
* The `outpoint` structure includes both a `TXID` and an output `index` number to refer to specific output.

## scriptCode

* If the `script` does not contain any `OP_CODESEPARATOR`, the `scriptCode` is the `script` serialized as scripts inside `CTxOut`.
* If the `script` contains any `OP_CODESEPARATOR`, the `scriptCode` is the `script` but removing everything up to and including the last executed `OP_CODESEPARATOR` before the signature checking opcode being executed, serialized as scripts inside CTxOut.

## value

* The 8-byte `value` of the `amount` of `duffs` the input contains.

## nSequence

* This is the `sequence` number.
* Default is `0xffffffff`.

## hashOutputs

* If the sighash type is neither `SINGLE` nor `NONE`, `hashOutputs` is the double SHA256 of the serialization of all output `values` (8-byte int64_t) paired up with their `scriptPubKey` (serialized as scripts inside `CTxOuts`);
* If sighash type is `SINGLE` and the input `index` is smaller than the number of outputs, `hashOutputs` is the double SHA256 of the output `amount` with `scriptPubKey` of the same `index` as the input;
* Otherwise, `hashOutputs` is a `uint256` of `0x0000......0000`.

## nLockTime

* Time (Unix epoch time) or block number.

## sighash type

````cpp
  ss << nHashType;
````

# Implementation

Addition to `SignatureHash` :

```cpp
  uint256 hashPrevouts;
  uint256 hashSequence;
  uint256 hashOutputs;
  
  if (!(nHashType & SIGHASH_ANYONECANPAY)) {
      hashPrevouts = GetPrevoutHash(txTo);
  }
  
  if (!(nHashType & SIGHASH_ANYONECANPAY) && (nHashType & 0x1f) != SIGHASH_SINGLE && (nHashType & 0x1f) != SIGHASH_NONE) {
       hashSequence = GetSequenceHash(txTo);
  }
  
  if ((nHashType & 0x1f) != SIGHASH_SINGLE && (nHashType & 0x1f) != SIGHASH_NONE) {
       hashOutputs = GetOutputsHash(txTo);
  } else if ((nHashType & 0x1f) == SIGHASH_SINGLE && nIn < txTo.vout.size()) {
     CHashWriter ss(SER_GETHASH, 0);
      ss << txTo.vout[nIn];
      hashOutputs = ss.GetHash();
  }
  
  CHashWriter ss(SER_GETHASH, 0);
  // Version
  ss << txTo.nVersion;
  // Input prevouts/nSequence (none/all, depending on flags)
  ss << hashPrevouts;
  ss << hashSequence;
  // The input being signed (replacing the scriptSig with scriptCode + amount)
  // The prevout may already be contained in hashPrevout, and the nSequence
  // may already be contain in hashSequence.
  ss << txTo.vin[nIn].prevout;
  ss << static_cast<const CScriptBase&>(scriptCode);
  ss << amount;
  ss << txTo.vin[nIn].nSequence;
  // Outputs (none/one/all, depending on flags)
  ss << hashOutputs;
  // Locktime
  ss << txTo.nLockTime;
  // Sighash type
  ss << nHashType;
  
  return ss.GetHash();
````

Computation of midstates:

````cpp
uint256 GetPrevoutHash(const CTransaction &txTo) {
  CHashWriter ss(SER_GETHASH, 0);
  for (unsigned int n = 0; n < txTo.vin.size(); n++) {
    ss << txTo.vin[n].prevout;
  }

  return ss.GetHash();
}

uint256 GetSequenceHash(const CTransaction &txTo) {
  CHashWriter ss(SER_GETHASH, 0);
  for (unsigned int n = 0; n < txTo.vin.size(); n++) {
    ss << txTo.vin[n].nSequence;
  }

  return ss.GetHash();
}

uint256 GetOutputsHash(const CTransaction &txTo) {
  CHashWriter ss(SER_GETHASH, 0);
  for (unsigned int n = 0; n < txTo.vout.size(); n++) {
    ss << txTo.vout[n];
  }

  return ss.GetHash();
}
````

# Test

To ensure consistency in consensus-critical behaviour, developers should test their implementations against the test below.

````text
  The following is an unsigned transaction:
    0100000002fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f0000000000eeffffffef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a0100000000ffffffff02202cb206000000001976a9148280b37df378db99f66f85c95a783a76ac7a6d5988ac9093510d000000001976a9143bde42dbee7e4dbe6a21b2d50ce2f0167faa815988ac11000000
    
    nVersion:  01000000
    txin:      02 fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f 00000000 00 eeffffff
                  ef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a 01000000 00 ffffffff
    txout:     02 202cb20600000000 1976a9148280b37df378db99f66f85c95a783a76ac7a6d5988ac
                  9093510d00000000 1976a9143bde42dbee7e4dbe6a21b2d50ce2f0167faa815988ac
    nLockTime: 11000000
  
  The input comes from an ordinary P2PK:
    scriptPubKey : 2103c9f4836b9a4f77fc0d81f7bcb01b7f1b35916864b9476c241ce9fc198bd25432ac value: 6.25
    private key  : bbc27228ddcb9209d7fd6f36b02f7dfa6252af40bb2f1cbc7a557da8027ff866
    
  To sign it with a nHashType of 1 (SIGHASH_ALL):
  
  hashPrevouts:
    dSHA256(fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f00000000ef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a01000000)
  = 96b827c8483d4e9b96712b6713a7b68d6e8003a781feba36c31143470b4efd37
  
  hashSequence:
    dSHA256(eeffffffffffffff)
  = 52b0a642eea2fb7ae638c36f6252b6750293dbe574a806984b8e4d8548339a3b
  
  hashOutputs:
    dSHA256(202cb206000000001976a9148280b37df378db99f66f85c95a783a76ac7a6d5988ac9093510d000000001976a9143bde42dbee7e4dbe6a21b2d50ce2f0167faa815988ac)
  = 863ef3e1a92afbfdb97f31ad0fc7683ee943e9abcf2501590ff8f6551f47e5e5
  
  hash preimage: 0100000096b827c8483d4e9b96712b6713a7b68d6e8003a781feba36c31143470b4efd3752b0a642eea2fb7ae638c36f6252b6750293dbe574a806984b8e4d8548339a3bef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a010000001976a9141d0f172a0ecb48aee1be1f2687d2963ae33f71a188ac0046c32300000000ffffffff863ef3e1a92afbfdb97f31ad0fc7683ee943e9abcf2501590ff8f6551f47e5e51100000001000000
  
    nVersion:     01000000
    hashPrevouts: 96b827c8483d4e9b96712b6713a7b68d6e8003a781feba36c31143470b4efd37
    hashSequence: 52b0a642eea2fb7ae638c36f6252b6750293dbe574a806984b8e4d8548339a3b
    outpoint:     ef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a01000000
    scriptCode:   1976a9141d0f172a0ecb48aee1be1f2687d2963ae33f71a188ac
    amount:       0046c32300000000
    nSequence:    ffffffff
    hashOutputs:  863ef3e1a92afbfdb97f31ad0fc7683ee943e9abcf2501590ff8f6551f47e5e5
    nLockTime:    11000000
    nHashType:    01000000
    
  sigHash:      c37af31116d1b27caf68aae9e3ac82f1477929014d5b917657d0eb49478cb670
  signature:    304402203609e17b84f6a7d30c80bfa610b5b4542f32a8a0d5447a12fb1366d7f01cc44a0220573a954c4518331561406f90300e8f3358f51928d43c212a8caed02de67eebee
    
  The serialized signed transaction is: 01000000000102fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f00000000494830450221008b9d1dc26ba6a9cb62127b02742fa9d754cd3bebf337f7a55d114c8e5cdd30be022040529b194ba3f9281a99f2b1c0a19c0489bc22ede944ccf4ecbab4cc618ef3ed01eeffffffef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a0100000000ffffffff02202cb206000000001976a9148280b37df378db99f66f85c95a783a76ac7a6d5988ac9093510d000000001976a9143bde42dbee7e4dbe6a21b2d50ce2f0167faa815988ac000247304402203609e17b84f6a7d30c80bfa610b5b4542f32a8a0d5447a12fb1366d7f01cc44a0220573a954c4518331561406f90300e8f3358f51928d43c212a8caed02de67eebee0121025476c2e83188368da1ff3e292e7acafcdb3566bb0ad253f62fc70f07aeee635711000000
  
    nVersion:  01000000
    marker:    00
    flag:      01
    txin:      02 fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f 00000000 494830450221008b9d1dc26ba6a9cb62127b02742fa9d754cd3bebf337f7a55d114c8e5cdd30be022040529b194ba3f9281a99f2b1c0a19c0489bc22ede944ccf4ecbab4cc618ef3ed01 eeffffff
                  ef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a 01000000 00 ffffffff
    txout:     02 202cb20600000000 1976a9148280b37df378db99f66f85c95a783a76ac7a6d5988ac
                  9093510d00000000 1976a9143bde42dbee7e4dbe6a21b2d50ce2f0167faa815988ac
    nLockTime: 11000000
````

# References

<a name="bip143">[1]</a> https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki

<a name="bip143Motivation">[2]</a> https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki#Motivation

# Copyright

This document is licensed under the [MIT License](https://opensource.org/licenses/MIT).


