<pre>
  DIP: pasta-compact-quorum-proofs
  Title: Compact Quorum Proof Chains for Trustless Platform Verification
  Author(s): PastaPastaPasta
  Special-Thanks:
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2026-01-17
  License: MIT License
</pre>

## Table of Contents

1. [Abstract](#abstract)
1. [Motivation](#motivation)
1. [Prior Work](#prior-work)
1. [Trusted Initial State](#trusted-initial-state)
1. [Quorum Proof Chain Data Structures](#quorum-proof-chain-data-structures)
    1. [ChainlockEntry](#chainlockentry)
    1. [QuorumCommitmentProof](#quorumcommitmentproof)
    1. [QuorumProofChainResponse](#quorumproofchainresponse)
1. [Verification Algorithm](#verification-algorithm)
    1. [Verifier State](#verifier-state)
    1. [ChainLock Verification](#chainlock-verification)
    1. [Quorum Commitment Verification](#quorum-commitment-verification)
    1. [Proof Processing Algorithm](#proof-processing-algorithm)
1. [Proof Construction](#proof-construction)
    1. [ChainLock Selection Strategy](#chainlock-selection-strategy)
    1. [Quorum Commitment Merkle Proof Construction](#quorum-commitment-merkle-proof-construction)
1. [P2P Messages](#p2p-messages)
    1. [GETQUORUMPROOFCHAIN](#getquorumproofchain)
    1. [QUORUMPROOFCHAIN](#quorumproofchain)
1. [gRPC API](#grpc-api)
1. [Proof Size Analysis](#proof-size-analysis)
1. [Security Considerations](#security-considerations)
1. [Backward Compatibility](#backward-compatibility)
1. [Reference Implementation](#reference-implementation)
1. [Copyright](#copyright)

## Abstract

This DIP defines Compact Quorum Proof Chains, a mechanism for trustlessly verifying LLMQ public keys using ChainLocks and the `merkleRootQuorums` field in coinbase transactions. This enables light clients and the Platform SDK to cryptographically verify Platform quorum public keys without trusting any external party.

The key insight is that a ChainLock at height H proves block H, and that block's coinbase transaction contains a `merkleRootQuorums` covering ALL currently active quorums at that height. This allows verification of any active quorum's commitment using a single chainlocked block's data, resulting in compact proofs of approximately 1 KB in typical scenarios.

## Motivation

Platform proof verification currently requires two steps:

1. **GroveDB Proof**: Verify data against a Merkle root (cryptographic)
2. **Tenderdash Signature**: Verify BLS signature from a Platform quorum (requires quorum public key)

The quorum public key is currently obtained via trusted sources:

| Method | Trust Model |
| ------ | ----------- |
| Dash Core RPC | Trust the node operator |
| TrustedHttpContextProvider | Trust centralized quorum servers |

Both methods require trusting an external party, which undermines the trustless nature of the verification.

This DIP enables verification of quorum public keys cryptographically using only:

1. A hardcoded checkpoint (block hash + known quorum keys) embedded in the SDK
2. Proofs provided by any untrusted server (verified client-side)

By leveraging the existing ChainLock infrastructure and `merkleRootQuorums` commitment in each block's coinbase, clients can build a cryptographic chain of trust from a known checkpoint to any currently active quorum.

## Prior Work

* [DIP-0002: Special Transactions](https://github.com/dashpay/dips/blob/master/dip-0002.md)
* [DIP-0004: Simplified Verification of Deterministic Masternode Lists](https://github.com/dashpay/dips/blob/master/dip-0004.md)
* [DIP-0006: Long-Living Masternode Quorums](https://github.com/dashpay/dips/blob/master/dip-0006.md)
* [DIP-0007: LLMQ Signing Requests / Sessions](https://github.com/dashpay/dips/blob/master/dip-0007.md)
* [DIP-0008: ChainLocks](https://github.com/dashpay/dips/blob/master/dip-0008.md)

## Trusted Initial State

Verification requires a trusted starting point embedded in client software. This checkpoint must contain:

1. A block hash and height identifying a known-good block
2. The public keys of active ChainLock quorums at that height (identified by quorum hash and type)

The specific serialization format of this checkpoint is an implementation detail left to client software.

### Quorum Lifespans and Checkpoint Freshness

The effectiveness of this verification scheme depends on overlapping quorum lifespans between the checkpoint and current chain tip.

**Mainnet:**

| Quorum Type | Purpose | DKG Interval | Active Count | Lifespan |
| ----------- | ------- | ------------ | ------------ | -------- |
| LLMQ_400_60 | ChainLocks | 288 blocks (~12 hours) | 4 | ~48 hours |
| LLMQ_100_67 | Platform | 24 blocks (~1 hour) | 24 | ~24 hours |

**Testnet:**

| Quorum Type | Purpose | DKG Interval | Active Count | Lifespan |
| ----------- | ------- | ------------ | ------------ | -------- |
| LLMQ_50_60 | ChainLocks | 288 blocks (~12 hours) | 4 | ~48 hours |
| LLMQ_25_67 | Platform | 24 blocks (~1 hour) | 24 | ~24 hours |

With a checkpoint less than 36 hours old, at least one ChainLock quorum from the checkpoint will still be active, enabling direct verification with a single chainlock. Older checkpoints require bridging through intermediate chainlock quorums.

## Quorum Proof Chain Data Structures

### ChainlockEntry

A ChainLock signature that proves a specific block is canonical.

| Field | Type | Size | Description |
| ----- | ---- | ---- | ----------- |
| height | int32_t | 4 | Height of the chainlocked block |
| blockHash | uint256 | 32 | Hash of the chainlocked block |
| signature | BLSSig | 96 | Recovered threshold signature |
| signingQuorumHash | uint256 | 32 | Hash of the quorum that signed this chainlock |
| signingQuorumType | uint8_t | 1 | LLMQ type of the signing quorum |

Total size: ~165 bytes

**Note**: The signing quorum can be deterministically calculated using `SelectQuorumForSigning` given the height, but including it explicitly simplifies verification and enables the verifier to check if the signing quorum is known before attempting signature verification.

### QuorumCommitmentProof

A proof that a specific quorum commitment is included in a chainlocked block's `merkleRootQuorums`.

| Field | Type | Size | Description |
| ----- | ---- | ---- | ----------- |
| commitment | CFinalCommitment | variable | The quorum final commitment (see [DIP-0006](https://github.com/dashpay/dips/blob/master/dip-0006.md)) |
| chainlockIndex | uint32_t | 4 | Index into the response's chainlocks array |
| quorumMerklePathLength | compactSize uint | 1-9 | Number of hashes in the merkle path |
| quorumMerklePath | uint256[] | 32 * length | Merkle path from commitment hash to `merkleRootQuorums` |
| coinbaseTx | CTransaction | variable | The coinbase transaction containing `merkleRootQuorums` |
| coinbaseMerkleProof | CPartialMerkleTree | variable | Merkle proof that coinbase is in the block |

The `CFinalCommitment` structure is defined in [DIP-0006](https://github.com/dashpay/dips/blob/master/dip-0006.md) and contains the `quorumPublicKey` that this proof ultimately verifies.

Estimated size: ~700-900 bytes (varies by quorum size and tree depth)

### QuorumProofChainResponse

The complete response containing all data needed to verify a target quorum.

| Field | Type | Size | Description |
| ----- | ---- | ---- | ----------- |
| headerCount | compactSize uint | 1-9 | Number of block headers |
| headers | CBlockHeader[] | 80 * count | Block headers for each chainlock |
| chainlockCount | compactSize uint | 1-9 | Number of chainlock entries |
| chainlocks | ChainlockEntry[] | variable | ChainLock signatures in verification order |
| quorumProofCount | compactSize uint | 1-9 | Number of quorum proofs |
| quorumProofs | QuorumCommitmentProof[] | variable | Quorum commitment proofs |

Headers and chainlocks are paired by index: `headers[i]` corresponds to `chainlocks[i]`.

## Verification Algorithm

### Verifier State

The verifier maintains the following state:

```text
H_verified: uint32           // Highest height cryptographically confirmed
Q_known: Map<(uint256, uint8), BLSPubKey>  // Known quorum public keys
                             // Key: (quorumHash, quorumType)
                             // Value: quorumPublicKey
```

Initial state is populated from the checkpoint:

* `H_verified = checkpoint.height`
* `Q_known = checkpoint.chainlockQuorums ∪ checkpoint.platformQuorums`

### ChainLock Verification

To verify a ChainLock against a known quorum:

1. Verify the signing quorum is in `Q_known`
2. Retrieve the quorum's public key from `Q_known`
3. Calculate the message hash:
   `msgHash = SHA256(llmqType, quorumHash, SHA256(height), blockHash)`
4. Verify the BLS signature against the quorum public key and message hash
5. Verify that `hash(header) == blockHash`

If verification succeeds, update `H_verified = max(H_verified, chainlock.height)`.

### Quorum Commitment Verification

To verify a quorum commitment proof:

1. Verify `chainlockIndex` references a chainlock with height <= `H_verified`
2. Retrieve the corresponding coinbase transaction and block header
3. Verify the coinbase merkle proof:
   * The `coinbaseMerkleProof` must prove that `coinbaseTx` is in the block
   * The block's merkle root must match `header.hashMerkleRoot`
4. Extract `merkleRootQuorums` from the coinbase transaction's extra payload
5. Calculate `commitmentHash = SHA256(serialize(commitment))`
6. Verify the quorum merkle path:
   * Compute the merkle root from `commitmentHash` and `quorumMerklePath`
   * The computed root must match `merkleRootQuorums`
7. Verify the commitment's `quorumSig`:
   * This threshold signature proves the quorum members agreed on this public key
   * Verification uses the aggregated public keys from the commitment's `signers` bitvector

If verification succeeds, add the quorum to `Q_known`:
`Q_known[(commitment.quorumHash, commitment.llmqType)] = commitment.quorumPublicKey`

### Proof Processing Algorithm

```text
FUNCTION verify_quorum_proof(checkpoint, proof, targetQuorum) -> Result<BLSPubKey>:

    // Initialize state from checkpoint
    H_verified = checkpoint.height
    Q_known = checkpoint.chainlockQuorums ∪ checkpoint.platformQuorums

    // Process proof iteratively until no more progress
    LOOP:
        made_progress = false

        // 1. Process chainlocks that can now be verified
        FOR i, CL IN enumerate(proof.chainlocks):
            IF CL.height <= H_verified:
                CONTINUE  // Already verified

            IF NOT Q_known.contains((CL.signingQuorumHash, CL.signingQuorumType)):
                CONTINUE  // Cannot verify yet

            // Verify chainlock signature
            quorumPubKey = Q_known[(CL.signingQuorumHash, CL.signingQuorumType)]
            msgHash = SHA256(CL.signingQuorumType, CL.signingQuorumHash,
                            SHA256(CL.height), CL.blockHash)
            VERIFY_BLS(CL.signature, quorumPubKey, msgHash)?

            // Verify header matches chainlock
            header = proof.headers[i]
            ASSERT(hash(header) == CL.blockHash)

            // Extend verified horizon
            H_verified = CL.height
            made_progress = true

        // 2. Learn quorum commitments from verified blocks
        FOR QP IN proof.quorumProofs:
            clHeight = proof.chainlocks[QP.chainlockIndex].height
            IF clHeight > H_verified:
                CONTINUE  // Chainlock not yet verified

            key = (QP.commitment.quorumHash, QP.commitment.llmqType)
            IF Q_known.contains(key):
                CONTINUE  // Already known

            // Verify coinbase is in the chainlocked block
            VERIFY_COINBASE_MERKLE_PROOF(QP.coinbaseTx, QP.coinbaseMerkleProof,
                                          proof.headers[QP.chainlockIndex])?

            // Verify commitment is in merkleRootQuorums
            merkleRootQuorums = extract_merkle_root_quorums(QP.coinbaseTx)
            VERIFY_QUORUM_MERKLE_PATH(QP.commitment, QP.quorumMerklePath,
                                       merkleRootQuorums)?

            // Verify commitment signature (proves DKG validity)
            VERIFY_COMMITMENT_SIGNATURE(QP.commitment)?

            // Add to known quorums
            Q_known[key] = QP.commitment.quorumPublicKey
            made_progress = true

        IF NOT made_progress:
            BREAK

    // 3. Return target quorum if found
    targetKey = (targetQuorum.quorumHash, targetQuorum.quorumType)
    RETURN Q_known.get(targetKey).ok_or(Error::InsufficientProof)
```

## Proof Construction

This section describes how a node constructs proofs for requesting clients.

### ChainLock Selection Strategy

The goal is to find the shortest chain of chainlocks from the checkpoint to the target quorum.

#### Case 1: Checkpoint quorum overlap exists

When the checkpoint is less than approximately 48 hours old:

1. Identify which checkpoint chainlock quorums are still active
2. Find the most recent chainlock signed by any of these quorums
3. This single chainlock can prove all currently active quorums

#### Case 2: No overlap

When the checkpoint is more than approximately 48 hours old:

1. Identify the checkpoint chainlock quorum with the longest remaining lifespan at checkpoint time
2. Find the most recent chainlock signed by that quorum
3. Learn new chainlock quorums from that block's `merkleRootQuorums`
4. Repeat with newly learned quorums until reaching a chainlock whose block contains the target quorum

### Quorum Commitment Merkle Proof Construction

The `merkleRootQuorums` in each coinbase is calculated as follows (per [DIP-0004](https://github.com/dashpay/dips/blob/master/dip-0004.md)):

1. Collect all final commitments from all active LLMQ sets at the block height
2. Calculate `hash = SHA256(serialize(commitment))` for each commitment
3. Sort hashes in ascending order
4. Calculate merkle root from the sorted list

To construct a proof for a specific commitment:

1. Retrieve all active commitments at the chainlock height
2. Compute all commitment hashes and sort them
3. Find the index of the target commitment's hash
4. Construct the merkle path from that index to the root

## P2P Messages

### GETQUORUMPROOFCHAIN

Request a quorum proof chain from a peer.

| Field | Type | Size | Description |
| ----- | ---- | ---- | ----------- |
| checkpointBlockHash | uint256 | 32 | Block hash of the client's checkpoint |
| checkpointHeight | uint32_t | 4 | Height of the checkpoint block |
| checkpointQuorumCount | compactSize uint | 1-9 | Number of known chainlock quorums |
| checkpointQuorums | QuorumEntry[] | variable | Known chainlock quorum entries from checkpoint |
| targetQuorumHash | uint256 | 32 | Hash of the target quorum to prove |
| targetQuorumType | uint8_t | 1 | LLMQ type of the target quorum |

### QUORUMPROOFCHAIN

Response containing the proof chain.

The response uses the `QuorumProofChainResponse` structure defined in [Quorum Proof Chain Data Structures](#quorum-proof-chain-data-structures).

| Field | Type | Size | Description |
| ----- | ---- | ---- | ----------- |
| response | QuorumProofChainResponse | variable | The complete proof chain |

## gRPC API

For Platform SDK integration, the following gRPC endpoint is defined:

```protobuf
service Core {
    rpc GetQuorumProofChain(GetQuorumProofChainRequest)
        returns (GetQuorumProofChainResponse);
}

message QuorumEntry {
    bytes quorum_hash = 1;      // 32 bytes
    uint32 quorum_type = 2;
    bytes quorum_public_key = 3; // 48 bytes
}

message GetQuorumProofChainRequest {
    bytes checkpoint_block_hash = 1;    // 32 bytes
    uint32 checkpoint_height = 2;
    repeated QuorumEntry checkpoint_chainlock_quorums = 3;
    bytes target_quorum_hash = 4;       // 32 bytes
    uint32 target_quorum_type = 5;
}

message ChainlockEntry {
    int32 height = 1;
    bytes block_hash = 2;               // 32 bytes
    bytes signature = 3;                // 96 bytes
    bytes signing_quorum_hash = 4;      // 32 bytes
    uint32 signing_quorum_type = 5;
}

message QuorumCommitmentProof {
    bytes commitment = 1;               // Serialized CFinalCommitment
    uint32 chainlock_index = 2;
    repeated bytes quorum_merkle_path = 3;  // Each 32 bytes
    bytes coinbase_tx = 4;              // Serialized transaction
    bytes coinbase_merkle_proof = 5;    // Serialized CPartialMerkleTree
}

message GetQuorumProofChainResponse {
    repeated bytes headers = 1;         // Each 80 bytes
    repeated ChainlockEntry chainlocks = 2;
    repeated QuorumCommitmentProof quorum_proofs = 3;
}
```

## Proof Size Analysis

### Component Sizes

| Component | Size |
| --------- | ---- |
| Block header | 80 bytes |
| ChainlockEntry | ~165 bytes |
| QuorumCommitmentProof | ~700-900 bytes |

### Per-Chainlock Overhead

Each chainlock in the proof requires:

* 1 ChainlockEntry: ~165 bytes
* 1 Block header: 80 bytes
* **Subtotal: ~245 bytes**

### Scenarios

#### Fresh Checkpoint

When the checkpoint is less than 36 hours old, a checkpoint chainlock quorum is still active. A single chainlock reaches the tip.

| Component | Count | Size Each | Total |
| --------- | ----- | --------- | ----- |
| Chainlock + header | 1 | 245 B | 245 B |
| Target quorum proof | 1 | 800 B | 800 B |
| **Total** | | | **~1 KB** |

#### Stale Checkpoint

When the checkpoint is 2-4 days old, checkpoint quorums have expired. Need 1-2 bridging chainlock quorums.

| Component | Count | Size Each | Total |
| --------- | ----- | --------- | ----- |
| Chainlocks + headers | 2-3 | 245 B | 490-735 B |
| Bridge CL quorum proofs | 1-2 | 800 B | 800-1,600 B |
| Target quorum proof | 1 | 800 B | 800 B |
| **Total** | | | **~2-3 KB** |

#### Very Old Checkpoint

When the checkpoint is 30+ days old, approximately 15 bridging chainlock quorums are needed (one per ~2 day interval).

| Component | Count | Size Each | Total |
| --------- | ----- | --------- | ----- |
| Chainlocks + headers | ~15 | 245 B | ~3,700 B |
| Bridge CL quorum proofs | ~15 | 800 B | ~12,000 B |
| Target quorum proof | 1 | 800 B | 800 B |
| **Total** | | | **~16 KB** |

### Summary

| Checkpoint Age | Proof Size |
| -------------- | ---------- |
| < 36 hours | ~1 KB |
| 2-4 days | ~2-3 KB |
| 30+ days | ~16 KB |

Checkpoints should be updated with each SDK release (monthly recommended) to maintain minimal proof sizes.

## Security Considerations

### Trust Assumptions

| Assumption | Basis |
| ---------- | ----- |
| Checkpoint is correct | Code review, reproducible builds, distribution via official channels |
| BLS signatures unforgeable | Cryptographic hardness of BLS scheme |
| Merkle proofs sound | Collision resistance of SHA-256 |
| ChainLocks are secure | DIP-0008 security analysis |

### Attack Resistance

| Attack | Why It Fails |
| ------ | ------------ |
| Forge chainlock | Requires 240 of 400 masternode operator keys (60% threshold) |
| Forge quorum commitment | `quorumSig` is threshold signature requiring quorum threshold |
| Wrong block hash | Header hash must match chainlock's `blockHash` |
| Tampered coinbase | Coinbase merkle proof verification fails |
| Tampered commitment | Commitment merkle proof verification fails |
| Omit proof data | Verification fails, client retries or tries different server |

### Failure Modes

| Failure | Cause | Resolution |
| ------- | ----- | ---------- |
| No verifiable chainlock | Server omitted required data | Retry or try different server |
| Verification timeout | Large proof on slow device | Increase timeout or use fresher checkpoint |
| Checkpoint too old | SDK not updated in 30+ days | Ship new checkpoint in SDK update |

## Backward Compatibility

This DIP introduces new P2P messages (`GETQUORUMPROOFCHAIN`, `QUORUMPROOFCHAIN`) and gRPC endpoints that do not affect existing functionality. Nodes that do not implement this DIP will not respond to these messages.

Clients implementing trustless verification should fall back to trusted verification methods if:

1. No peers support the new messages
2. Proof verification fails repeatedly
3. The checkpoint is too old to construct a valid proof chain

## Reference Implementation

Reference implementation will be provided in:

* Dash Core: Chainlock indexing and proof generation RPCs
* Platform: `rs-trustless-quorum-verifier` crate for Rust verification
* DAPI: gRPC endpoint wrapping Core RPCs

## Copyright

Copyright (c) 2026 Dash Core Group, Inc. [Licensed under the MIT License](https://opensource.org/licenses/MIT)
