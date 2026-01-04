<pre>
  DIP: XXXX
  Title: State Transition Signing Request URI Scheme
  Author(s): PastaPastaPasta
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2026-01-03
  License: MIT License
</pre>

## Table of Contents

1. [Abstract](#abstract)
1. [Motivation](#motivation)
1. [Prior Work](#prior-work)
1. [Specification](#specification)
    1. [URI Scheme](#uri-scheme)
    1. [URI Format](#uri-format)
    1. [Parameters](#parameters)
    1. [State Transition Encoding](#state-transition-encoding)
    1. [Response Format](#response-format)
    1. [Examples](#examples)
1. [Wallet Behavior](#wallet-behavior)
1. [Security Considerations](#security-considerations)
1. [Copyright](#copyright)

# Abstract

This DIP defines a URI scheme (`dash-st:`) for requesting the signing of Dash Platform state transitions. The scheme enables dApps and services to present unsigned state transitions to wallet applications via QR codes or copy-paste, supporting both online wallets that broadcast directly and air-gapped signers that return signed bytes.

# Motivation

Dash Platform state transitions require signatures from Identity keys before they can be broadcast to the network. Currently, there is no standardized mechanism for a dApp or service to request that an external wallet sign a state transition. This creates friction in user experience and limits the development of:

1. **Web-based dApps** that cannot hold private keys but need to create state transitions
2. **Cross-device signing** where a desktop dApp requests signing from a mobile wallet via QR code
3. **Air-gapped signing** for high-security Identity key management
4. **Hardware wallet integration** where signing must happen on a separate device

By defining a URI scheme similar to [BIP-0021](https://github.com/bitcoin/bips/blob/master/bip-0021.mediawiki) (Bitcoin) and [EIP-681](https://eips.ethereum.org/EIPS/eip-681) (Ethereum), this DIP enables interoperability between dApps and any compliant Dash wallet.

# Prior Work

* [BIP-0021: URI Scheme](https://github.com/bitcoin/bips/blob/master/bip-0021.mediawiki)
* [EIP-681: URL Format for Transaction Requests](https://eips.ethereum.org/EIPS/eip-681)
* [DIP-0002: Special Transactions](https://github.com/dashpay/dips/blob/master/dip-0002.md)
* [DIP-0011: Identities](https://github.com/dashpay/dips/blob/master/dip-0011.md)
* [DIP-0013: Identities in HD Wallets](https://github.com/dashpay/dips/blob/master/dip-0013.md)

# Specification

## URI Scheme

The URI scheme is `dash-st` (Dash State Transition).

## URI Format

```text
dash-st:<st-data>[?<parameters>]
```

Where:

* `st-data` is the Base58-encoded state transition bytes
* `parameters` is an optional query string of key-value pairs

### ABNF Grammar

```abnf
dash-st-uri     = "dash-st:" st-data [ "?" parameters ]
st-data         = *base58char
parameters      = parameter *( "&" parameter )
parameter       = key "=" value
key             = 1*qchar
value           = *qchar
qchar           = unreserved / pct-encoded
base58char      = %x31-39 / %x41-48 / %x4A-4E / %x50-5A / %x61-6B / %x6D-7A
                  ; 1-9, A-H, J-N, P-Z, a-k, m-z (excludes 0, I, O, l)
```

## Parameters

### Request Parameters

| Parameter | Required | Type | Description |
| --------- | -------- | ---- | ----------- |
| `n` | Yes | string | Network identifier: `m` (mainnet), `t` (testnet), or `d` (devnet) |
| `v` | Yes | integer | URI format version. Currently `1`. |
| `id` | No | string | Base58-encoded 32-byte Identity ID hint for signer selection |
| `k` | No | integer | Key ID within the Identity (per [DIP-0011](https://github.com/dashpay/dips/blob/master/dip-0011.md) Identity Public Key `id`) |
| `l` | No | string | URL-encoded human-readable label for display (max 64 characters) |

### Response Parameters

Response URIs use the same `dash-st:` scheme with additional parameters:

| Parameter | Required | Type | Description |
| --------- | -------- | ---- | ----------- |
| `s` | Yes | string | Status: `1` (signed), `r` (rejected), or `e` (error) |
| `e` | Conditional | string | URL-encoded error message (required if `s=r` or `s=e`) |

## State Transition Encoding

The state transition bytes are encoded using Base58. This encoding is consistent with how Dash Platform Identifiers are encoded and is URL-safe.

The bytes represent the state transition serialized via `PlatformSerializable::serialize_to_bytes()`:

* For **request URIs**: The unsigned state transition (signature fields set to null/default)
* For **response URIs**: The signed state transition (signature and signature_public_key_id populated)

## Response Format

Response URIs use the same `dash-st:` scheme. The presence of the `s` parameter distinguishes a response from a request:

* `s=1`: Signed successfully. The state transition data contains the signed bytes.
* `s=r`: Rejected by user. The state transition data may be empty.
* `s=e`: Error occurred. The `e` parameter contains the error message.

## Examples

### Request URI (minimal)

```text
dash-st:3R1gPL8wMT4h7vnJqWmzECBpK6gYx9vNmF?n=m&v=1
```

### Request URI (with hints)

```text
dash-st:3R1gPL8wMT4h7vnJqWmzECBpK6gYx9vNmF?n=m&v=1&id=8ZT1B8XWK&k=2&l=Sign%20contact%20request
```

### Response URI (signed)

```text
dash-st:4K2hQL9xNT5i8woKrXnzFDBqL7hZy0wOoG?n=m&v=1&s=1
```

### Response URI (rejected)

```text
dash-st:?n=m&v=1&s=r&e=User%20cancelled
```

### Response URI (error)

```text
dash-st:?n=m&v=1&s=e&e=Invalid%20key%20ID
```

# Wallet Behavior

## Request Processing

Wallets receiving a `dash-st:` URI MUST:

1. **Parse and validate** the URI format according to this specification
2. **Decode** the Base58 state transition data
3. **Deserialize** the state transition bytes using the Platform serialization format
4. **Verify network** matches the wallet's active network; reject with error if mismatch
5. **Display preview** to user showing at minimum:
    * State transition type (e.g., "Document Batch", "Identity Update")
    * Network
    * Signing Identity
6. **Await user confirmation** before signing
7. **Select signing key**:
    * If `k` parameter is provided, use that key ID. Reject if invalid.
    * Otherwise, select an appropriate key based on the state transition type's security level requirements per [DIP-0011](https://github.com/dashpay/dips/blob/master/dip-0011.md)
8. **Sign** the state transition
9. **Complete** the flow:
    * **Online wallet**: Broadcast to Dash Platform and show result to user
    * **Air-gapped wallet**: Display response URI as QR code for scanning

# Security Considerations

## Cross-Network Attack Prevention

The required `n` parameter prevents accidental signing of mainnet transactions on testnet wallets or vice versa. Wallets MUST verify the network parameter matches their active network and reject mismatches.

## Replay Protection

State transitions include nonces and Identity revisions that provide replay protection at the protocol level. This DIP does not introduce additional replay vectors.

## User Consent

Wallets MUST require explicit user confirmation before signing any state transition. The confirmation dialog MUST display at minimum the state transition type, network, and signing identity.

## High-Risk Transition Warnings

Wallets SHOULD display additional warnings for high-risk state transitions:

* **IdentityUpdate**: Key additions or removals affect Identity security
* **IdentityCreditWithdrawal**: Funds leaving the Identity
* **IdentityCreditTransfer**: Credits sent to another Identity

## Invalid Parameters

If the `k` parameter specifies a key ID that does not exist or is not appropriate for the state transition type, the wallet MUST reject the request with an error rather than falling back to a different key.

# Copyright

Copyright 2026 Dash Core Group, Inc. Licensed under the MIT License.
