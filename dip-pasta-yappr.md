<pre>
  DIP: pasta-yappr
  Title: Dash Platform Application Key Exchange and State Transition Signing
  Author(s): Pasta
  Special-Thanks:
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Applications
  Created: 2026-03-10
  License: MIT License
</pre>

# Table of Contents

1. [Abstract](#abstract)
1. [Motivation](#motivation)
1. [Prior Work](#prior-work)
1. [Terminology](#terminology)
1. [Overview](#overview)
1. [Key Exchange Protocol](#key-exchange-protocol)
    * [dash-key: URI Format](#dash-key-uri-format)
        * [Binary Payload Layout](#binary-payload-layout)
        * [Network Identifiers](#network-identifiers)
    * [URI Validation Rules](#uri-validation-rules)
    * [Cryptographic Flow](#cryptographic-flow)
        * [Login Key Derivation](#login-key-derivation)
        * [Shared Secret Derivation](#shared-secret-derivation)
        * [Login Key Encryption](#login-key-encryption)
        * [Application-Side Key Derivation](#application-side-key-derivation)
1. [Key Exchange Contract](#key-exchange-contract)
    * [Document Schema](#document-schema)
    * [Indices](#indices)
    * [Polling](#polling)
1. [State Transition Signing Protocol](#state-transition-signing-protocol)
    * [dash-st: URI Format](#dash-st-uri-format)
    * [Query Parameters](#query-parameters)
    * [Supported Encodings](#supported-encodings)
    * [Wallet Validation and Signing](#wallet-validation-and-signing)
1. [First-Time Login Key Registration](#first-time-login-key-registration)
1. [Security Considerations](#security-considerations)
1. [Copyright](#copyright)

# Abstract

This DIP defines two complementary URI-based protocols that enable secure interaction between Dash
Platform applications and wallet software. The **Key Exchange Protocol** (`dash-key:`) allows web
applications to obtain deterministic login keys from a wallet via QR code scanning, using ECDH key
agreement and AES-256-GCM encryption with Dash Platform as the communication channel. The **State
Transition Signing Protocol** (`dash-st:`) allows applications to request that a wallet sign and
broadcast unsigned state transitions. Together, these protocols enable wallet-based authentication
for Platform applications without requiring users to manually handle private keys.

# Motivation

Dash Platform applications require users to authenticate with cryptographic keys tied to their
Platform identity. Current authentication methods require users to manually enter or manage private
keys, which is both error-prone and a poor user experience. Users accustomed to modern login flows
(e.g., scanning a QR code with a mobile device) expect a simpler mechanism.

This DIP addresses the following problems:

1. **Key management burden**: Users should not need to copy, paste, or store raw private keys to use
   Platform applications.
2. **Deterministic authentication**: A wallet should derive the same login key for a given
   application every time, enabling stateless re-authentication across devices and sessions.
3. **Per-application isolation**: Each application should receive a unique key, so compromise of one
   application's key does not affect others.
4. **First-time onboarding**: New users need a way to register application-specific keys on their
   identity without manually constructing state transitions.
5. **Decentralized communication**: The protocol should not rely on any centralized server; Dash
   Platform itself serves as the communication channel between the application and the wallet.

# Prior Work

* [BIP-0032: Hierarchical Deterministic
  Wallets](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki)
* [BIP-0044: Multi-Account Hierarchy for Deterministic
  Wallets](https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki)
* [DIP-0009: Coin Specific Feature Derivation
  Paths](https://github.com/dashpay/dips/blob/master/dip-0009.md)
* [DIP-0011: Identities](https://github.com/dashpay/dips/blob/master/dip-0011.md)
* [DIP-0013: Identities in Hierarchical Deterministic
  Wallets](https://github.com/dashpay/dips/blob/master/dip-0013.md)
* [DIP-0015: DashPay](https://github.com/dashpay/dips/blob/master/dip-0015.md)

# Terminology

| Term | Definition |
| ---- | ---------- |
| Application | A Dash Platform application (e.g., a web app) that needs to authenticate a user via their Platform identity |
| Wallet | Software that holds the user's HD wallet seed and Platform identity keys (e.g., Dash Evo Tool) |
| Login Key | A 32-byte deterministic key derived by the wallet for a specific application and identity |
| Ephemeral Keypair | A temporary secp256k1 keypair generated for a single key exchange session |
| Key Exchange Contract | A Dash Platform data contract that stores `loginKeyResponse` documents |
| Hash160 | The composition RIPEMD-160(SHA-256(data)), producing a 20-byte hash |

# Overview

The protocol operates in two phases. In the first phase, the application generates an ephemeral
keypair and encodes a key exchange request as a `dash-key:` URI, typically displayed as a QR code.
The user scans this with their wallet, which derives a deterministic login key, encrypts it using
ECDH-derived shared secret, and publishes the encrypted response to Dash Platform. The application
polls Platform for the response, decrypts the login key, and derives authentication and encryption
keys from it.

If the user's identity does not yet have the necessary application keys registered, the application
enters a second phase: it constructs an unsigned `IdentityUpdateTransition` that adds the required
keys, encodes it as a `dash-st:` URI, and displays it as a QR code. The wallet signs and broadcasts
the transition to complete key registration.

```text
APPLICATION                         DASH PLATFORM                     WALLET
═══════════                         ═════════════                     ══════

 1. Generate ephemeral keypair
    (app_priv, app_pub)
 2. Encode app_pub + contractId
    + label into dash-key: URI
 3. Display URI as QR code
                                                           4. Scan QR / paste URI
                                                              Parse and validate payload
                                                           5. User selects identity and
                                                              approves the request
                                                           6. Derive login key from wallet
                                                              seed (BIP32 path + HKDF with
                                                              identity, contract, key index)
                                                           7. Generate wallet ephemeral
                                                              keypair (wallet_priv, wallet_pub)
                                                           8. Compute shared secret:
                                                              ECDH(wallet_priv, app_pub) → HKDF
                                                           9. Encrypt login key with shared
                                                              secret using AES-256-GCM
                                                          10. Create loginKeyResponse document
                                                              with wallet_pub + encrypted payload
                                           ◄───────────────────
                                    11. Document stored
                                        on Platform
12. Poll Platform for document
    matching contractId +
    Hash160(app_pub)
13. Document found; extract
    wallet_pub and encrypted payload
14. Compute same shared secret:
    ECDH(app_priv, wallet_pub) → HKDF
15. Decrypt login key using
    shared secret and AES-256-GCM
16. Derive auth key and encryption
    key from login key via HKDF
17. Check if derived keys are
    registered on the identity
    ├─ YES: Login complete
    └─ NO:  First-time login;
            continue to key registration

18. Build unsigned IdentityUpdate
    transition adding auth +
    encryption keys
19. Encode as dash-st: URI
    and display QR code
                                                          20. Scan dash-st: QR
                                                              Review transition details
                                                          21. User approves; wallet signs
                                                              with existing auth key
                                                          22. Broadcast signed transition
                                           ◄───────────────────
                                    23. Identity updated
                                        on Platform
24. Poll identity for new keys
25. Keys found; login complete
```

# Key Exchange Protocol

## dash-key: URI Format

A key exchange request is encoded as a URI with the following structure:

```text
dash-key:<base58_payload>?n=<network>&v=<version>
```

| Component | Description |
| --------- | ----------- |
| `dash-key:` | URI scheme prefix |
| `<base58_payload>` | Base58-encoded binary payload (see below) |
| `n` | Network identifier (required) |
| `v` | Protocol version (optional). When present, the wallet MUST verify it matches the version byte in the payload. The current protocol version is `1`. |

### Binary Payload Layout

The Base58-decoded payload has the following structure:

| Offset | Size (bytes) | Field | Description |
| ------ | ------------ | ----- | ----------- |
| 0 | 1 | version | Protocol version; must be `0x01` |
| 1 | 33 | appEphemeralPubKey | Compressed secp256k1 public key (prefix `0x02` or `0x03`) |
| 34 | 32 | contractId | Dash Platform data contract identifier for the application |
| 66 | 1 | labelLength | Length of the label field in bytes (0–64) |
| 67 | 0–64 | label | UTF-8 encoded application label |

Minimum payload size: 67 bytes (no label). Maximum payload size: 131 bytes (64-byte label).

### Network Identifiers

| Value | Network |
| ----- | ------- |
| `m`, `mainnet`, `dash` | Mainnet |
| `t`, `testnet` | Testnet |
| `d`, `devnet` | Devnet |
| `r`, `regtest` | Regtest (local) |

## URI Validation Rules

A wallet implementation MUST validate the following before processing a `dash-key:` URI:

1. The URI begins with the `dash-key:` prefix.
2. The Base58 payload decodes successfully.
3. The payload is at least 67 bytes.
4. The version byte at offset 0 equals `0x01`. Any other version MUST be rejected.
5. The ephemeral public key at offset 1 is a valid compressed secp256k1 point (first byte is `0x02`
   or `0x03`).
6. The label length byte at offset 66 does not exceed 64.
7. The total payload length equals `67 + labelLength`.
8. The label bytes (if any) are valid UTF-8.
9. If the query parameter `v` is present, it matches the version byte in the payload.
10. The network parameter `n` matches the wallet's active network.

## Cryptographic Flow

### Login Key Derivation

The wallet derives a deterministic login key from its HD seed for a given identity, contract, and
key index. The derivation proceeds in two stages.

#### Stage 1: BIP32 Base Key Derivation

Derive a private key at the following HD path:

```text
m / 9' / coin_type' / 21' / account'
```

| Path Level | Value |
| ---------- | ----- |
| 9' | Feature purpose (per [DIP-0009](https://github.com/dashpay/dips/blob/master/dip-0009.md)) |
| coin_type' | `5` (mainnet) or `1` (testnet/devnet/regtest) per [BIP-0044](https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki) |
| 21' | Key exchange feature index |
| account' | Wallet account index for the selected identity (default `0`) |

#### Stage 2: HKDF Key Derivation

Apply HKDF-SHA256 ([RFC 5869](https://www.rfc-editor.org/rfc/rfc5869)) to the BIP32-derived private
key:

| Parameter | Value |
| --------- | ----- |
| Hash | SHA-256 |
| IKM | 32-byte private key from Stage 1 |
| Salt | 32-byte identity identifier |
| Info | `contractId (32 bytes) ‖ keyIndex (4 bytes, little-endian)` |
| Output length | 32 bytes |

The `keyIndex` is determined by querying Platform for an existing `loginKeyResponse` document owned
by this identity for the target contract. If a document exists, its stored `keyIndex` is reused. If
no document exists, `keyIndex` is `0`. This ensures the same login key is derived on every
authentication for the same identity and contract.

### Shared Secret Derivation

Both the application and the wallet independently derive the same shared secret using ECDH:

1. Perform ECDH multiplication on secp256k1: multiply the local ephemeral private key by the
   remote ephemeral public key.
2. Extract the x-coordinate of the resulting point (32 bytes).
3. Apply HKDF-SHA256:

| Parameter | Value |
| --------- | ----- |
| Hash | SHA-256 |
| IKM | 32-byte x-coordinate from ECDH |
| Salt | `dash:key-exchange:v1` (UTF-8, 20 bytes) |
| Info | empty |
| Output length | 32 bytes |

The output is the 32-byte symmetric key used for AES-256-GCM encryption.

### Login Key Encryption

After deriving the login key and the shared secret, the wallet encrypts the login key so it can be
safely published to Platform. Only the application — which holds the other half of the ECDH
ephemeral keypair — can decrypt it.

The wallet generates a random 12-byte nonce and encrypts the 32-byte login key using AES-256-GCM
with the shared secret as the symmetric key. No associated data is used.

The resulting encrypted payload is serialized as a single byte sequence:

| Offset | Size (bytes) | Field | Description |
| ------ | ------------ | ----- | ----------- |
| 0 | 12 | nonce | Random nonce used for AES-256-GCM |
| 12 | 32 | ciphertext | Encrypted login key |
| 44 | 16 | tag | Message authentication code produced by AES-GCM; used during decryption to verify the ciphertext has not been modified |

Total encrypted payload size: 60 bytes. This byte sequence is stored in the `encryptedPayload`
field of the `loginKeyResponse` document published to Platform.

To decrypt, the application extracts the nonce from the first 12 bytes, uses its own copy of the
shared secret as the AES-256-GCM key, and decrypts the remaining 48 bytes (ciphertext + tag) to
recover the 32-byte login key.

### Application-Side Key Derivation

After decrypting the login key, the application derives two keys using HKDF-SHA256:

**Authentication key:**

| Parameter | Value |
| --------- | ----- |
| IKM | 32-byte login key |
| Salt | 32-byte identity identifier |
| Info | `auth` (UTF-8, 4 bytes) |
| Output length | 32 bytes |

**Encryption key:**

| Parameter | Value |
| --------- | ----- |
| IKM | 32-byte login key |
| Salt | 32-byte identity identifier |
| Info | `encryption` (UTF-8, 10 bytes) |
| Output length | 32 bytes |

These derived keys are deterministic: the same login key and identity always produce the same
authentication and encryption keys.

# Key Exchange Contract

The key exchange protocol uses a Dash Platform data contract to communicate responses from the
wallet to the application. This contract is deployed once and shared by all applications using the
protocol.

## Document Schema

The contract defines a single document type: `loginKeyResponse`.

| Field | Type | Size (bytes) | Description |
| ----- | ---- | ------------ | ----------- |
| contractId | Identifier | 32 | The target application's data contract identifier |
| appEphemeralPubKeyHash | Bytes | 20 | Hash160 of the application's ephemeral public key |
| walletEphemeralPubKey | Bytes | 33 | Wallet's compressed secp256k1 ephemeral public key |
| encryptedPayload | Bytes | 1–4096 | Encrypted login key (nonce ‖ ciphertext ‖ tag; typically 60 bytes) |
| keyIndex | Integer | 4 | The key index used in login key derivation |

All fields are required.

## Indices

The contract defines two unique indices:

### Index 1: byOwnerAndContract

| Property | Order |
| -------- | ----- |
| $ownerId | ascending |
| contractId | ascending |

This index ensures a wallet identity can have at most one response per target contract. Subsequent
key exchanges for the same identity and contract update the existing document.

### Index 2: byContractAndEphemeralKey

| Property | Order |
| -------- | ----- |
| contractId | ascending |
| appEphemeralPubKeyHash | ascending |

This index enables the application to poll for a response using its ephemeral public key hash,
without needing to know the wallet's identity in advance.

## Polling

The application polls for a response by querying the key exchange contract with the following
conditions:

* `contractId` equals the application's own contract identifier
* `appEphemeralPubKeyHash` equals Hash160 of the application's ephemeral public key

The recommended polling interval is 3 seconds with a 120-second timeout. When a matching document is
found, the application extracts `walletEphemeralPubKey` and `encryptedPayload` to complete the
decryption. The wallet identity is discovered from the document's `$ownerId` field.

## Document Lifecycle

When a wallet processes a key exchange request:

1. Query for an existing `loginKeyResponse` document matching `($ownerId, contractId)`.
2. If a document exists, update it with the new ephemeral key hash, wallet ephemeral public key,
   encrypted payload, and key index. Bump the document revision.
3. If no document exists, create a new one with all required fields.
4. On revision conflict during update, retry up to 3 times with a 500ms delay between attempts,
   re-querying the document on each attempt.

# State Transition Signing Protocol

The `dash-st:` protocol allows an application to request that a wallet sign and broadcast an
unsigned state transition. While general-purpose, its primary use in the key exchange flow is for
first-time key registration.

## dash-st: URI Format

```text
dash-st:<encoded_transition>?n=<network>&v=<version>[&id=<identity>][&k=<key_id>][&l=<label>]
```

| Component | Description |
| --------- | ----------- |
| `dash-st:` | URI scheme prefix |
| `<encoded_transition>` | Encoded unsigned state transition bytes |
| `n` | Network identifier (required; see [Network Identifiers](#network-identifiers)) |
| `v` | Protocol version (required; must be `1`) |

## Query Parameters

| Parameter | Required | Description |
| --------- | -------- | ----------- |
| `n` | Yes | Network identifier (`m`, `t`, `d`, or `r`) |
| `v` | Yes | Protocol version; must be `1` |
| `id` | No | Base58-encoded identity identifier (32 bytes); wallet should pre-select this identity |
| `k` | No | Key ID hint (integer); wallet should pre-select this signing key |
| `l` | No | URL-encoded application label (max 64 characters) |

The state transition type is determined by deserializing the encoded bytes. The serialization format
is self-describing and includes a type discriminator, so no external type hint is needed.

## Supported Encodings

The state transition bytes MUST be encoded using Base58, consistent with the `dash-key:` protocol.

## Wallet Validation and Signing

A wallet MUST perform the following before signing a `dash-st:` state transition:

1. **Deserialize** the state transition bytes from their self-describing binary format.
2. **Validate network**: The `n` parameter MUST match the wallet's active network. A mismatch MUST
   prevent signing.
3. **Display transition details**: The wallet MUST show the user a human-readable summary of the
   state transition, including:
   * The transition type
   * The owner identity
   * A JSON representation of the full transition for inspection
4. **High-risk warnings**: The wallet SHOULD display prominent warnings for state transitions that
   modify identity keys (`IdentityUpdate`), withdraw credits (`IdentityCreditWithdrawal`), or
   transfer credits (`IdentityCreditTransfer`).
5. **Identity hint validation**: If the `id` parameter is provided, the wallet MUST verify that the
   selected signing identity matches the hint.
6. **Key hint validation**: If the `k` parameter is provided, the wallet MUST verify that the
   selected signing key ID matches the hint.
7. **User approval**: The wallet MUST require explicit user approval before signing. The user
   selects the signing identity and authentication key.
8. **Sign and broadcast**: Upon approval, the wallet signs the state transition with the selected
   authentication key and broadcasts it to Dash Platform.

# First-Time Login Key Registration

When a user authenticates with an application for the first time, the application-derived keys may
not yet be registered on the user's Platform identity. The application detects this by fetching the
identity's public keys and checking for keys matching the expected authentication and encryption key
data.

If the keys are not present, the application constructs an unsigned `IdentityUpdateTransition` that
adds two keys:

**Authentication key:**

| Property | Value |
| -------- | ----- |
| Purpose | AUTHENTICATION |
| Security Level | HIGH |
| Key Type | ECDSA_HASH160 |
| Data | Hash160 of the authentication public key (20 bytes) |

**Encryption key:**

| Property | Value |
| -------- | ----- |
| Purpose | ENCRYPTION |
| Security Level | MEDIUM |
| Key Type | ECDSA_HASH160 |
| Data | Hash160 of the encryption public key (20 bytes) |

The key IDs are assigned sequentially starting from the identity's current maximum key ID plus one.
The identity revision and nonce are incremented from their current Platform values.

The unsigned transition is encoded as a `dash-st:` URI and displayed as a QR
code. The wallet scans, reviews, signs with an existing authentication key, and broadcasts the
transition.

ECDSA_HASH160 keys store only the hash of the public key rather than the full public key. This
prevents public key disclosure during key registration, as ownership signatures (which would reveal
the full public key) are not required for this key type.

The application polls the identity for the new keys at a recommended interval of 5 seconds with a
5-minute timeout.

# Security Considerations

## Ephemeral Key Cleanup

Application implementations MUST zero ephemeral private key material from memory immediately after
the shared secret has been derived. Retaining ephemeral private keys beyond their use window expands
the attack surface for memory disclosure vulnerabilities.

## Per-Contract Key Isolation

The login key derivation includes the target contract identifier and key index in the HKDF info
parameter. This ensures that different applications receive different login keys even when
authenticating the same identity from the same wallet. Compromise of one application's login key does
not reveal keys for any other application.

## Per-Identity Key Isolation

The identity identifier is used as the HKDF salt during login key derivation and again during
authentication and encryption key derivation. Different identities produce entirely different key
trees even when using the same wallet seed.

## Network Isolation

Different networks use different coin types in the BIP32 derivation path (`5` for mainnet, `1` for
testnet/devnet/regtest). Both `dash-key:` and `dash-st:` URIs include a network parameter, and
wallet implementations MUST reject requests that do not match the active network.

## ECDH Forward Secrecy

Each key exchange session uses fresh ephemeral keypairs on both sides. The ephemeral keys are not
stored after the exchange completes. Even if the wallet's HD seed is later compromised, past key
exchange sessions cannot be replayed because the wallet's ephemeral private keys no longer exist.
However, the login keys themselves are deterministic from the seed, so seed compromise does reveal
login keys.

## State Transition Review

The `dash-st:` protocol requires wallets to fully deserialize, display, and obtain explicit user
approval before signing any state transition. High-risk transitions (identity key modifications,
credit withdrawals, credit transfers) require prominent warnings. This prevents malicious
applications from tricking users into signing harmful transitions.

## Hash160 Key Type

Using ECDSA_HASH160 for registered application keys avoids exposing the full public key on-chain.
The public key is only revealed when a transaction is signed with it, rather than at registration
time.

## Nonce Race Condition

The `IdentityUpdateTransition` uses a nonce fetched from Platform and incremented locally. If
another transaction for the same identity is broadcast between the fetch and the wallet's broadcast,
the nonce becomes stale and Platform will reject the transition. Implementations SHOULD handle this
by allowing the user to retry the key registration flow.

# Copyright

Copyright (c) 2026 Dash Core Group, Inc. [Licensed under the MIT
License](https://opensource.org/licenses/MIT)
