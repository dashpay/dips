<pre>
DIP: 00xx
Title: Making InstantSend Deterministic using Quorum Cycles
Author: Samuel Westrich, UdjinM6
Special-Thanks: Thephez, Virgile Bartolo
Comments: No comments yet.
Status: Draft
Layer: Consensus (hard fork)
Created: 2020-08-02
License: MIT License
</pre>

## Abstract

This DIP aims to improve InstantSend messages to make them deterministically verifiable.

## Motivation

LLMQ based InstantSend was introduced in DIP10. In that implementation InstantSend locks are only
verifiable by recent quorums because the InstantSend lock does not include any block or time based
information. In Dash Platform InstantSend Locks are used to add credit to Identities as they provide
input finality. When blocks are replayed on the Platform Chain, all State Transitions need to be
re-validated and it is possible that InstantSend signatures will need to be rechecked. However, to
recheck them one needs to know the quorum that signed them. In this DIP we will provide a mechanism
to that end.

## Previous work

* [DIP-0006: Long-Living Masternode Quorums](https://github.com/dashpay/dips/blob/master/dip-0006.md)
* [DIP-0007: LLMQ Signing Requests / Sessions](https://github.com/dashpay/dips/blob/master/dip-0007.md)
* [DIP-0010: LLMQ InstantSend](https://github.com/dashpay/dips/blob/master/dip-0010.md)

## Versioning of ISLock messages

Since `islock` messages were never versioned, a new `ISDLOCK` message will be created and the
`islock` message will be deprecated. ISD stands for InstantSend Deterministic. The version of the
`ISDLOCK` used in this document will be `1`. We will still refer to `islock` messages, even though
the message name has been changed.

## QuorumHash vs CycleHash

The naive approach to fixing this problem would be to include the `quorumHash` in the `islock`
message. An `islock` would then be easily verifiable since the quorum that signed it would always be
known. The drawback of this approach is that any quorum could sign any `islock` even if it were not
responsible to do so for that quorum cycle.

A quorum cycle begins at a `quorumBlock` (as per
[DIP-0006](https://github.com/dashpay/dips/blob/master/dip-0006.md#parametersvariables-of-a-llmq-and-dkg))
and lasts for a number of blocks that is equal to the `quorumDkgInterval`. During this time the set
of valid quorums are not modified for a given `quorumType`. If the `quorumDkgInterval` is set to 24
blocks then from block 100 to block 124 quorums of that type stay the same. During this period the
quorum that is in charge of signing a specific `islock` will also always be the same. CycleHash is
the `blockHash` of the first block in a cycle.

By adding the `cycleHash` to the `islock` message, any node can follow the steps required to
determine the appropriate `quorumHash` and verify the signature.

## Verification of the signature

To calculate which LLMQ was responsible for the `islock`, the verifier should perform the following:

1. Take the LLMQ set that corresponds to the quorum cycle defined by the cycle hash in the `islock`
   message
2. Calculate the RequestID from data in the `islock` message by calculating `SHA256("islock",
   inputCount, prevTxHash1, prevTxOut1, prevTxHash2, prevTxOut2, ...)`
3. For each LLMQ of this quorum cycle’s set, calculate `SHA256(quorumType, quorumHash, requestId)`
4. Sort the list of LLMQs based on the result of step 3 in ascending order
5. Use the first entry of the sorted list as the responsible LLMQ
6. Create the SignID by calculating `SHA256(quorumHash, requestId, txHash)`
7. Use the public key of the responsible LLMQ and verify the signature against the SignID

Nodes receiving `islock` messages should verify them by using the above steps. Only `ISDLOCK`
messages with valid signatures should be propagated further using the inventory system.

## The new ISDLock message

When a masternode receives a recovered signature for a signing request in the quorum where it is
active, it should use the signature to create a new p2p message, which is the `ISDLOCK` message. To
figure out the cycle hash, take the quorum hash corresponding to the LLMQ that created the recovered
signature. Then find the last known block where this quorum was responsible for signing the `islock`
message. Often this is the current block, but in rare situations it might be a prior one if quorums
have just cycled. From this last known block, find the first block of that cycle. This is the last
block before quorums changed for the quorum type used for `islock` messages.

It is possible that a quorum is active before and after quorum cycling. It is also possible that the
quorum responsible for a signing request before and after cycling is the same. This could lead to
the creation of two `islock` messages, distinct only by the fact that their cycle hash is different.

The new message has the following structure (fields in bold are not present in the previously used
`islock` message):

| Field | Type | Size | Description |
|-|-|-|-|
| **version** | uint8 | 1 |  The version of the islock message |
| inputCount | compactSize uint | 1 - 9 | Number of inputs in the transaction |
| inputs | COutpoint[] | `inputCount` * 36 | Inputs of the transaction. COutpoint is a uint256 (hash of previous transaction) and a uint32 (output index) |
| txid | uint256 | 32 | Transaction id (hash of the transaction) |
| **cycleHash** | uint256 | 32 | Block hash of first block of the cycle in which the quorum signing this `islock` is active |
| sig | BLSSig | 96 | Recovered signature from the signing request/session |

### **Choosing the active LLMQ to perform signing**

Choosing the active LLMQ to perform signing should follow the same steps as defined in [DIP-0007 -
Choosing the active LLMQ to perform
signing](https://github.com/dashpay/dips/blob/master/dip-0007.md#choosing-the-active-llmq-to-perform-signing).
