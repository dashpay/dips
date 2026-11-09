<!-- cspell:ignore bech HKDF AEAD dpns -->
<pre>
  DIP: pasta-app-connect
  Title: App Connect: Wallet Sign-In and Transition Signing for Platform Applications
  Author(s): Pasta
  Special-Thanks:
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2026-03-10
  License: MIT License
</pre>

# Table of Contents

1. [Abstract](#abstract)
1. [Motivation](#motivation)
1. [Prior Work](#prior-work)
1. [Conventions and Terminology](#conventions-and-terminology)
1. [Overview](#overview)
1. [URIs](#uris)
    * [Rules Shared by Both Verbs](#rules-shared-by-both-verbs)
    * [connect URI](#connect-uri)
    * [sign URI](#sign-uri)
    * [Transitional dash-key Carrier](#transitional-dash-key-carrier)
1. [Request Body](#request-body)
    * [Layout](#layout)
    * [Fields](#fields)
        * [Field Rules](#field-rules)
    * [Authentication Bindings](#authentication-bindings)
    * [Encryption Bindings](#encryption-bindings)
1. [App Identity](#app-identity)
1. [Wallet Processing of connect](#wallet-processing-of-connect)
    * [Decoding and Identity Choice](#decoding-and-identity-choice)
    * [What an App May Request](#what-an-app-may-request)
    * [Security Levels](#security-levels)
    * [Limits](#limits)
    * [Session Keys](#session-keys)
    * [Encryption Keys](#encryption-keys)
        * [Rotation](#rotation)
    * [Identity Updates](#identity-updates)
    * [Publishing the Response](#publishing-the-response)
    * [Return Link](#return-link)
    * [Approval Sheet](#approval-sheet)
    * [Disconnect](#disconnect)
1. [Response](#response)
    * [Response Contract](#response-contract)
    * [Encryption Envelope](#encryption-envelope)
    * [Payload](#payload)
1. [App Processing of connect](#app-processing-of-connect)
1. [Transition Signing](#transition-signing)
1. [Status Codes](#status-codes)
1. [Security Considerations](#security-considerations)
1. [Deployment and Compatibility](#deployment-and-compatibility)
1. [Test Vectors](#test-vectors)
    * [Vector Inputs](#vector-inputs)
    * [Request Vector](#request-vector)
    * [Session Key Leaf Vectors](#session-key-leaf-vectors)
    * [Response Vector](#response-vector)
    * [Key Derivation Vectors](#key-derivation-vectors)
1. [Reference Implementations](#reference-implementations)
1. [Copyright](#copyright)

# Abstract

This DIP defines App Connect, the protocol a Dash wallet uses to sign a user in to an application
built on Dash Platform, and to sign individual state transitions for that application.

To sign in, the application shows a request as a QR code or a `dashpay://connect` link. The wallet
derives fresh keys for the user's identity and registers them on Platform. Each key is bounded to
the application's contracts and carries a credit budget and an expiry. The wallet then hands the
private keys to the application through an encrypted response document in the App Connect system
contract. Platform enforces every key's bounds, budget and expiry, so the application never holds a
key that can move the user's credits, change their identity or outlive its grant.

For anything those keys cannot do, the application asks the wallet to sign a single state
transition with a `dashpay://sign` link. The wallet decodes it, shows the user what it does, and
signs and broadcasts it with one of the identity's own keys.

This DIP replaces an earlier draft of the same name that defined the `dash-key:` and `dash-st:`
protocols.

# Motivation

Platform applications sign state transitions with keys of the user's identity. Asking users to paste
private keys into a web page is unsafe, and the first wallet login protocol (the `dash-key:` v1
draft this DIP replaces) had structural problems:

* **One shared secret.** The wallet sent the application a login secret from which the application
  derived its own keys. Anyone who obtained that secret could derive every key the application
  would ever use for that identity.
* **Keys outside Platform's control.** The application registered its own keys, so the wallet could
  not limit what they did, how much they spent or how long they lived.
* **Two scans.** A first login needed one QR code for the key exchange and another to register the
  keys.
* **Hard-coded applications.** Wallets carried each application's key set in their own code.

Platform protocol version 14 added what a better design needs:

* contract bounds on authentication keys (a single contract, a document type, or a contract group);
* per-key credit budgets and expiry;
* bounded encryption and decryption keys;
* index-only document types, used here for the response.

App Connect uses these so that the wallet decides and registers every key, and Platform enforces what
each key may do.

# Prior Work

* [DIP-0009: Feature Derivation Paths](https://github.com/dashpay/dips/blob/master/dip-0009.md)
* [DIP-0013: Identities in Hierarchical Deterministic Wallets](https://github.com/dashpay/dips/blob/master/dip-0013.md),
  with the application session authentication (`6'`) and application encryption (`7'`)
  sub-features added by [dashpay/dips#191](https://github.com/dashpay/dips/pull/191)
* [DIP-0014: Extended Key Derivation using 256-Bit Unsigned Integers](https://github.com/dashpay/dips/blob/master/dip-0014.md)
* [DIP-0015: DashPay](https://github.com/dashpay/dips/blob/master/dip-0015.md), which defines the
  `dashpay:` URI scheme this DIP extends and the bounded encryption key pairs this DIP reuses
* The App Connect system contract on Dash Platform (`docs/protocol/app-connect.md` in
  `dashpay/platform`)

# Conventions and Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY" and
"OPTIONAL" in this document are to be interpreted as described in
[RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

| Term | Meaning |
| --- | --- |
| app | A Platform application that wants to act for a user |
| wallet | Software holding the user's identity keys and recovery phrase |
| `appId` | The 32-byte id of a data contract that identifies the app |
| request | A `connect` request from the app, carried in a URI |
| binding | One key the request asks for: what it is bound to, and its limits |
| grant | The keys a wallet registered and handed to the app for one request |
| session key | An authentication key the wallet grants for one binding |
| encryption key | A bounded ENCRYPTION or DECRYPTION key the wallet grants for one encryption binding |
| `hash160(x)` | RIPEMD-160(SHA-256(x)) |
| `hash256(x)` | SHA-256(SHA-256(x)) |
| `u8(n)`, `u64(n)` | `n` as one byte, or as eight bytes big-endian |
| base58 | The Bitcoin base58 alphabet, without a checksum |
| base64url | [RFC 4648](https://www.rfc-editor.org/rfc/rfc4648) section 5, without padding |

All integers are big-endian. A "block time" is Platform block time in milliseconds since the Unix
epoch.

# Overview

```text
App                                    Wallet                               Platform
 | fresh ephemeral key pair              |                                     |
 | show dashpay://connect (QR or link) ->|                                     |
 |                                       | decode, check, show approval sheet  |
 |                                       | derive keys, IdentityUpdate ------->|
 |                                       | wait for confirmation <-------------|
 |                                       | publish loginKeyResponse ---------->|
 | poll loginKeyResponse by hash160(appEphPub) <------------------------------|
 | decrypt, verify every key on chain    |                                     |
 | sign writes with the session keys ---------------------------------------->|
 |                                       |                                     |
 | dashpay://sign (one transition) ----->| decode, describe, sign, broadcast ->|
 | watch the chain for the effect <-------------------------------------------|
```

1. The app makes a fresh secp256k1 key pair and shows a `connect` request as a QR code and a link.
1. The wallet decodes the request, checks it, and shows an approval sheet.
1. On approval, the wallet derives one session key per granted authentication binding and the
   encryption keys the request asks for, registers the new ones in MASTER-signed identity updates,
   and waits until they are confirmed.
1. The wallet publishes a `loginKeyResponse` document under the identity, with the private keys
   encrypted to the app's ephemeral key.
1. The app polls for responses to its request, decrypts them, and checks every granted key on chain
   before it treats anyone as signed in.
1. The app signs its own writes with the session keys. For a transition they cannot sign, it sends
   the wallet a `sign` request.

# URIs

The `dashpay:` scheme is defined by DIP-15, which uses it for contact invitations. This DIP defines
two more verbs, `connect` and `sign`, as URI hosts. `dash:` remains the BIP 21 payment scheme and is
not used here.

## Rules Shared by Both Verbs

* **Scheme and host.** The scheme is `dashpay` and the host is the verb. Emitters MUST write both in
  lowercase. Wallets MUST compare them case-insensitively. A wallet that does not know a verb
  SHOULD say that the link needs a newer wallet version rather than show a generic error.
* **Shape.** The path is empty (a single `/` is ignored), with no userinfo, port or fragment.
* **Query.** Split on `&` and form-decode names and values. A repeated known parameter makes the URI
  invalid. Unknown parameters are ignored. Emitters SHOULD write parameters in the order shown below,
  so that test vectors are byte-exact. Wallets MUST accept any order.
* **`v`.** Exactly `2` for both verbs. Any other value is `unsupported`.
* **`n`.** The network: `m` mainnet, `t` testnet, `d` devnet. It MUST equal the wallet's current
  network, and the wallet MUST check it before any network read. A refusal SHOULD name both
  networks.
* **Binary values** are canonical base64url: `=`, `+` and `/` are refused, a length of 1 mod 4 is
  refused, and non-zero trailing bits are refused, so each value has exactly one encoding.
* **Ids** are base58, at most 45 characters, decoding to exactly 32 bytes.
* **`cb`** is an OPTIONAL return link on both verbs. See [Return Link](#return-link).

## connect URI

```text
dashpay://connect?v=2&n=<m|t|d>&r=<base64url(body)>[&cb=<percent-encoded https URL>]
```

| Part | Rule | Refusal |
| --- | --- | --- |
| Whole URI | At most 4,096 bytes of UTF-8, checked on the raw string before decoding | `invalid` |
| `r` | REQUIRED. Canonical base64url of the [request body](#request-body), at most 1,366 characters, decoding to at most 1,024 bytes | `invalid` |
| body | Decoded under every rule of this DIP | `unsupported` or `invalid` |

There is no expiry parameter. Freshness comes from the body's `CREATED_AT`, so two clock fields can
never disagree.

## sign URI

```text
dashpay://sign?v=2&n=<m|t|d>&exp=<unix seconds>&st=<base64url(unsigned transition)>[&app=<base58 appId>][&cb=<percent-encoded https URL>]
```

| Part | Rule | Refusal |
| --- | --- | --- |
| Whole URI | At most 8 KiB when read by the wallet's own scanner; at most 28 KiB when the operating system delivers it (a tapped link or a system camera scan) | `invalid` |
| `exp` | ASCII digits, at most 11, Unix seconds. Refused when not in the future, or more than one hour plus two minutes ahead. Checked again right before signing | `stale` |
| `st` | REQUIRED. Canonical base64url of one unsigned, serialized state transition of 1 to 20,480 bytes | `invalid` |
| `app` | OPTIONAL app id, used only for display ("requested by …"). It MUST NOT be used to skip any check | `invalid` if malformed |

## Transitional dash-key Carrier

Before this DIP, wallets accepted the same request body in a `dash-key:` URI:

```text
dash-key:<base58(body)>?n=<m|t|d>&v=2[&cb=<percent-encoded https URL>]
```

`n`, `v` and `cb` follow the rules above, and each may appear once. A wallet MAY accept this
carrier on testnet and devnet while apps move to `dashpay://connect`. A wallet MUST NOT accept it on
mainnet. A request decoded from either carrier is processed identically, and a grant does not
depend on the carrier it was made through.

The `dash-key:` v1 and `dash-st:` URIs of the earlier draft are obsolete. Wallets MUST NOT accept
them on mainnet and SHOULD remove them.

# Request Body

## Layout

```text
body  = 0x02 ‖ appEphPub (33) ‖ appId (32) ‖ labelLen (1) ‖ label (labelLen) ‖ field*
field = type (1) ‖ length (1) ‖ value (length)
```

| Part | Rule |
| --- | --- |
| version | `0x02`. Any other value is `unsupported` |
| `appEphPub` | A compressed secp256k1 point, fresh for every request |
| `appId` | The app's id: a data contract id. See [App Identity](#app-identity) |
| label | UTF-8, at most 64 bytes, with no C0 or C1 control characters, no U+007F, and no Unicode `Bidi_Control` characters. The app writes it and nothing verifies it |

A body is at most 1,024 bytes on every carrier. The request hash is `hash160(appEphPub)`. It identifies the request on Platform.

## Fields

After the label, the body is a list of fields. Each field is a TLV (type, length, value): one byte
naming the field, one byte giving the value's length, then the value. Because every field states its
length, a wallet can step over a field it does not know.

| Type | Name | Count | Value |
| --- | --- | --- | --- |
| `0x01` | `IDENTITY_HINT` | 0–1 | The identity id (32 bytes) the app expects to answer |
| `0x02` | `AUTH_BINDING` | 1–4 | See [Authentication Bindings](#authentication-bindings) |
| `0x03` | `CONNECTION_ID` | 0–1 | 16 random bytes, one per app installation and network, kept across sign-outs |
| `0x04` | `ENC_BINDING` | 0–8 | See [Encryption Bindings](#encryption-bindings) |
| `0x05` | `MODE` | 0–1 | `1` means renew. Absent means login. Any other value is `invalid` |
| `0x06` | `CREATED_AT` | 1 | `u64`, milliseconds since the Unix epoch, when the app made the request |

Count is how many times the field may appear. `CREATED_AT` and at least one `AUTH_BINDING` are
REQUIRED.

For example, the [request vector](#request-vector) carries five fields after its label `Yappr`:

| Bytes | Field |
| --- | --- |
| `02 32 …` | `AUTH_BINDING`, 50 bytes: a contractGroup key at CRITICAL |
| `02 3a …` | `AUTH_BINDING`, 58 bytes: a documentType key for DashPay `profile` |
| `03 10 …` | `CONNECTION_ID`, 16 bytes |
| `04 21 …` | `ENC_BINDING`, 33 bytes: an ENCRYPTION key for `appId` |
| `06 08 …` | `CREATED_AT`, 8 bytes |

This DIP does not define the semantics of `MODE = 1`. A wallet MAY process a renew request as a
login. Apps renew by sending a new login request with the same `CONNECTION_ID` and an
`IDENTITY_HINT`.

### Field Rules

* **Unknown fields.** A later revision can add fields. An odd type is optional: a wallet that does
  not know it MUST skip it, so a new hint or display detail does not break older wallets. An even
  type changes what the user would grant: a wallet that does not know it MUST refuse the request as
  `unsupported`, rather than grant less than the app asked for without saying so.
* **One encoding.** Fields appear in non-decreasing type order, so repeated fields are adjacent. A
  field whose count is 0–1 or 1 appears at most once. So no request can be encoded two ways, and two
  implementations cannot disagree about whether a request is valid.
* **Invalid input.** A field out of order, appearing more times than its count allows, missing
  when REQUIRED, with the wrong length or an invalid value, or running past the end of the body
  makes the request `invalid`. An unknown odd type may repeat.
* **Integers.** `CREATED_AT` MUST be non-zero. `CREATED_AT` and `expiresAt` values above 2^53 − 1 are
  `invalid`, so that implementations whose integers are IEEE 754 doubles, such as JavaScript, read
  them the same way as the others.

## Authentication Bindings

```text
AUTH_BINDING = kind (1) ‖ securityLevel (1) ‖ id (32) ‖ totalBudget (u64) ‖ expiresAt (u64) [‖ nameLen (1) ‖ name]
```

| Part | Rule |
| --- | --- |
| kind | `0` singleContract, `1` documentType, `2` contractGroup (the bincode tags of Platform's `ContractBounds`). An unknown kind is `unsupported` |
| securityLevel | `1` CRITICAL or `2` HIGH, on any kind. Anything else is `invalid` |
| id | The contract id, or the group id for a contractGroup binding |
| totalBudget | Proposed lifetime budget in credits. `0` means no proposal. A contractGroup binding MUST carry a non-zero budget |
| expiresAt | Proposed expiry as a block time. `0` means no proposal |
| name | documentType only: the document type name, 1–64 bytes of `[A-Za-z0-9_-]`. Absent on the other kinds |

The first `AUTH_BINDING` is the primary binding. Two bindings with the same kind, id and name make
the request `invalid`.

A binding's index among the request's `AUTH_BINDING` fields, from 0 to 3, is its `bindingIndex`.

## Encryption Bindings

```text
ENC_BINDING = contractId (32) ‖ purpose (1)
```

| Part | Rule |
| --- | --- |
| contractId | The data contract the key is bound to |
| purpose | `1` ENCRYPTION, `2` DECRYPTION. Anything else is `invalid` |

An app asks for an ENCRYPTION key, a DECRYPTION key, or both, for each contract it encrypts data
in. Platform's encrypted documents (for example DashPay contact requests, DIP-15) use a pair: the
sender's ENCRYPTION key and the recipient's DECRYPTION key. Two bindings with the same contract and
purpose make the request `invalid`.

# App Identity

An app is its `appId` and nothing more. There is no manifest, registry or verified name.

A manifest could not show that an app is genuine. Anyone can deploy a contract and publish a record
that calls itself by a well-known name, which proves who wrote the record and not who they are.
What protects the user is seeing the app id and every scope, budget and expiry before approving,
and Platform enforcing each key's bounds, budget and expiry afterwards.

A wallet:

* MUST NOT refuse a request because it does not recognise the `appId`;
* MUST present the request's label, wherever it shows it, as the app's own claim, never as a
  verified name;
* MAY map well-known app ids to friendlier names, but MUST NOT let that map change which requests
  are accepted, which keys are granted or which limits apply.

# Wallet Processing of connect

## Decoding and Identity Choice

1. The wallet MUST decode the request under every rule of [URIs](#uris) and
   [Request Body](#request-body), and refuse with `unsupported` or `invalid`.
1. The wallet MUST refuse a request whose `CREATED_AT` is more than 10 minutes behind the wallet's
   clock, or more than 2 minutes ahead of it, as `stale`.
1. A wallet that holds several identities MUST ask which one signs in, and MUST NOT pick one
   silently. With an `IDENTITY_HINT`, it MUST offer only that identity, and refuse if it does not
   hold it.

## What an App May Request

The app asks and the wallet grants what was asked for, subject to these rules. A request that
breaks one is `invalid`.

* `appId` MUST be an existing data contract. A contractGroup binding's group MUST exist.
* **Owner consistency.** A contractGroup binding's group, and a singleContract binding's contract,
  MUST be owned by the identity that owns `appId`. A request therefore cannot show one app while
  asking for authentication keys on another owner's contracts, except the one foreign document type
  below. Encryption bindings are not limited this way.
* **Foreign document types.** A documentType binding on a contract owned by anyone else is allowed
  only for DashPay `profile`. Wallets MUST NOT allow any other, and in particular never DashPay
  `contactRequest` or any DPNS document type. A documentType binding naming a document type the
  contract does not have is `invalid`.
* **System contracts.** A system contract MUST NOT be the `appId`.
* **Encryption bindings.** An `ENC_BINDING` MAY name any data contract whose contract-level
  `requiresIdentityEncryptionBoundedKey` (for ENCRYPTION) or `requiresIdentityDecryptionBoundedKey`
  (for DECRYPTION) is `0` (unique) or `2` (multiple, reference to latest). It need not be owned by
  `appId`'s owner. A contract without that setting, with the value `1` (which keeps no current key),
  or with the requirement only on a document type, is `invalid`. An `ENC_BINDING` MAY name a system
  contract that meets these conditions, and the wallet SHOULD then warn that the app will be able to
  read that feature's data in every app the user uses it in. DashPay does not qualify: it sets the
  requirement on its `contactRequest` document type only, so DIP-15's keys cannot be requested
  through App Connect.

The user MAY decline any binding except the primary one. Declining the primary binding declines the
request.

## Security Levels

* A session key has the level its binding asks for: CRITICAL or HIGH. Platform requires CRITICAL
  for batches that contain token transitions, and for document types that demand it. A CRITICAL
  key is still bounded, so it can act only within its binding's contract, document type or group.
* Encryption keys are MEDIUM.
* A wallet MUST NOT grant a MASTER key, a TRANSFER key, or any authentication key without contract
  bounds through `connect`.

## Limits

* Every session key MUST be registered with a budget and an expiry. A binding that proposes none
  still gets both.
* The binding's budget and expiry are proposals. The wallet MAY lower or raise them and SHOULD let
  the user choose from presets. It MUST NOT drop a limit the binding asked for, and MUST refuse a
  binding whose proposed expiry has already passed as `invalid`.
* Presets and caps are wallet policy. Wallets SHOULD agree on them, so users see the same choices
  on every platform. Current wallets use budget presets of 0.1, 0.5 and 2 DASH with a cap of 5
  DASH, and lifetime presets of 30, 90 and 365 days with a default of 90 and a cap of 365.

## Session Keys

The wallet derives one fresh secp256k1 key per granted authentication binding, at the DIP-13
application session authentication sub-feature:

```text
m / 9' / coin' / 5' / 6' / 0' / identityId' / requestId'
requestId = hash256(appEphPub ‖ u8(bindingIndex))
```

* `coin'` is `5'` on mainnet and `1'` on testnet and devnet.
* `identityId'` and `requestId'` are 256-bit hardened DIP-14 indexes.
* `appEphPub` is the request's 33-byte compressed key. `bindingIndex` is the binding's index among
  the request's `AUTH_BINDING` fields, counting declined bindings, so a key does not depend on what
  the user declined.
* `hash256(appEphPub)` without the index byte is reserved for the earlier one-key protocol, so a key
  derived under this DIP never collides with one.

This derivation is normative. It makes every session key distinct from every other key on the
identity, and makes a retry of the same request (a second tap, or a crash before the update was
confirmed) derive the same keys instead of adding new ones.

If a derived session key is already on the identity, the wallet MUST reuse it only if it is
enabled and its bounds, level, budget and expiry equal what this approval grants. Otherwise the
wallet answers `failed`, and the app makes a fresh request.

Session keys are never recovered from the recovery phrase, and wallets do not scan this path when
restoring identities.

A wallet SHOULD register session keys as ECDSA_SECP256K1, and MAY register them as ECDSA_HASH160.
Apps MUST accept both. Measured on a protocol version 14 devnet, registering one ECDSA_SECP256K1
session key cost 17.0 M credits against 19.6 M for ECDSA_HASH160, and each signature costs
slightly less, while every session key signs at least once.

## Encryption Keys

The wallet derives encryption keys at the DIP-13 application encryption sub-feature:

```text
m / 9' / coin' / 5' / 7' / 0' / identityId' / contractId' / purpose' / rotation'
```

* `contractId'` is the bound contract's id as a 256-bit hardened DIP-14 index.
* `purpose'` is `1'` for ENCRYPTION and `2'` for DECRYPTION.
* `rotation'` is a 31-bit hardened index (`ser32(rotation + 2^31)`, as in DIP-13): `0'` for the
  first key and one higher for each [rotation](#rotation).
* The key is registered as ECDSA_SECP256K1 (peers need the point), MEDIUM, bound
  `singleContract(contractId)`.

This derivation is normative: the user's other devices, other wallets and other apps on the same
contract must find the same key.

The identity's **current key** for a (contract, purpose) is the key Platform records as current for
that contract and purpose, if it is enabled. Platform keeps that record even after the key is
disabled: permanently when the contract's requirement is `0` (unique), and until a newer key is
added when it is `2`. An identity has at most one current key per (contract, purpose).

Rotations are registered in order, so a wallet finds the keys at this path by deriving rotations
`0'`, `1'`, `2'`, … and stopping at the first one whose key is not on the identity in any state.

For each granted encryption binding, in this order:

1. If the identity has a current key for that contract and purpose, the wallet registers nothing.
   If it holds that key's private key, whether at this path or at another path it derives the
   identity's keys on, it SHOULD send it and MAY omit the slot instead. Otherwise it MUST omit the
   slot.
1. Otherwise, if any key is on the identity for that contract and purpose, the wallet MUST omit
   the slot. None of them is current: the key Platform records as current is disabled, though an
   older key may still be enabled. Under the requirement `0` Platform would refuse a second key,
   and under `2` a new key would be a rotation, which is never part of a login.
1. Otherwise, the wallet MUST register rotation `0'` and send it.

A wallet MUST NOT send a key that is not the identity's current key for the binding's contract and
purpose, and a login never registers a key next to a current one.

### Rotation

Rotation replaces the current key with a new one, so that apps holding the old key cannot read
what is encrypted to the new one. A wallet MAY offer it. It MUST be an explicit action the user
takes in the wallet, and never part of a login or an approval sheet.

Rotation is possible only for a contract whose requirement is `2`. Under `0`, Platform keeps the
first key in the slot even after it is disabled and refuses any other, so a wallet MUST NOT offer
rotation for such a contract, and MUST NOT disable its key.

To rotate a (contract, purpose), the wallet derives the next rotation after the highest one on the
identity at this path (`0'` if there is none) and registers it in one MASTER-signed `IdentityUpdate`
that also disables the current key. Platform makes the newer key current.

* Anyone holding an earlier key can still read data that was encrypted to it.
* Apps receive the new key at their next login, under the rules above.
* An app MUST check that an encryption key is still the identity's current key before encrypting
  to it, and MUST stop using a key that is no longer current. Peers SHOULD encrypt to the
  recipient's current key, not to a key id they cached. A rotation protects new data only as far
  as apps follow these rules.
* ENCRYPTION and DECRYPTION keys rotate separately. To cut an app off from a contract, the user
  rotates every (contract, purpose) it was granted.
* A wallet restored from seed derives every rotation, so it can still read the old data. On
  testnet and devnet it SHOULD also derive the earlier path without the rotation level (see
  [Deployment and Compatibility](#deployment-and-compatibility)), or it cannot read data encrypted
  to such a key and has to omit it at login.

## Identity Updates

* The wallet adds the new keys with MASTER-signed `IdentityUpdate` transitions. Platform limits how
  many keys one update may add (6 at the time of writing). When a grant needs more, the wallet MAY
  use several updates.
* New key ids are allocated from the highest existing id plus one. A duplicate key id or a stale
  revision means another device updated the identity concurrently: the wallet SHOULD re-read the
  identity and rebuild once, then fail.
* A wallet MAY, in the same update, disable the session keys of its previous grant for the same
  (identity, `appId`, `CONNECTION_ID`). Without a `CONNECTION_ID` it SHOULD NOT disable anything.
  This keeps session keys from piling up on the identity, but it is not required: a session key
  stops working at its expiry regardless.
* The wallet MUST wait until every new key is confirmed on Platform before it publishes the
  response. If an update fails, the wallet MUST NOT publish a response. Keys from updates that did
  land stay on the identity; a retry of the same request reuses them under the rules above.

## Publishing the Response

1. The wallet SHOULD delete the previous `loginKeyResponse` it published for this identity and app,
   with an index-only delete carrying all three original values. The delete is best effort and
   MUST NOT block the login.
1. The wallet creates the new response (see [Response](#response)).

The response and any delete are separate transitions, because Platform allows one transition per
document batch. They are signed by an AUTHENTICATION key of the identity at HIGH or CRITICAL that
has no contract bounds, budget or expiry. Deleting a response does not revoke keys.

## Return Link

`cb` is an absolute `https` URL without userinfo, at most 512 characters after decoding. A `cb`
that breaks these rules makes the request `invalid`.

Opening `cb` is the wallet's decision. The app MUST NOT depend on it, and polls either way. A
wallet that opens it:

* SHOULD show its host on the approval sheet before the user decides;
* SHOULD open it only after the user has approved or declined, and only for a request that arrived
  as a link on the same device;
* SHOULD NOT open it for a request scanned by the wallet's own scanner, since the app is then
  usually on another device;
* when there is nothing to approve (a refused request, or one that failed to parse), SHOULD show
  the reason and open a valid `cb` only if the user taps an explicit "Return to `<host>`" action;
* MUST append `ac=<status>` (see [Status Codes](#status-codes)), keeping any existing query.

`cb` carries nothing but the status.

## Approval Sheet

The sheet's content is wallet policy. It SHOULD say in plain words what the app will be able to
do, what it may spend and for how long, and what it cannot do. In particular, it SHOULD show:

* the `appId`, shortened, with the full id and a copy action one step away;
* the request's label in quotes, marked as given by the app. A wallet's own name for a well-known
  app id MAY be shown next to it, never instead of it;
* one line per binding, with each binding but the primary one as an option the user can turn off;
* each budget in DASH and each expiry as a date;
* for a contractGroup key, that it also covers contracts added to the group later;
* for a CRITICAL key, a clear warning that it can do everything its bounds allow at that level,
  including moving the user's tokens on those contracts;
* for each encryption binding, which contract's encrypted data the app will be able to read,
  whether that contract belongs to the app's owner, and a warning for a system contract such as
  DashPay;
* what the app cannot do, such as move credits, register names or change keys;
* how long ago the request was made.

## Disconnect

A wallet SHOULD let the user disconnect an app. Disconnecting disables the app's live session keys
on Platform. It MUST NOT disable encryption keys, which other devices and apps may rely on, so an
app keeps any encryption key it was given. Where the contract allows it, the user can
[rotate](#rotation) the key so that the app cannot read what is encrypted afterwards.

# Response

## Response Contract

The wallet publishes the response in the App Connect system contract, which activates at Platform
protocol version 14.

| Item | Value |
| --- | --- |
| Contract id | `H8F9mP1BM55TE1ShsxPZHzhyinaMdY9bMmP85mkDhcJJ` |
| Document type | `loginKeyResponse` (immutable, deletable, index-only) |
| Index | `byRequest`: `(appEphemeralPubKeyHash, $ownerId)` |

| Property | Value |
| --- | --- |
| `appEphemeralPubKeyHash` | `hash160(appEphPub)` (20 bytes) |
| `walletEphemeralPubKey` | The wallet's fresh compressed ephemeral key for this response (33 bytes) |
| `encryptedPayload` | `nonce (12) ‖ ciphertext ‖ tag (16)`, 60 to 572 bytes |

The index allows one response per request per identity, so an observer who sees the request cannot
block the wallet's response by writing first.

## Encryption Envelope

```text
shared = ECDH(walletEphPriv, appEphPub).x                                   (32 bytes)
key    = HKDF-SHA256(ikm = shared, salt = "dash:key-exchange:v1", info = "app-connect:v2", L = 32)
aad    = "dash:app-connect:v2" ‖ hash160(appEphPub) ‖ ownerId                (19 + 20 + 32 bytes)
body   = AES-256-GCM(key, nonce, aad, slot₀ ‖ slot₁ ‖ … ‖ slotₙ₋₁)
```

* `ownerId` is the raw 32-byte id of the identity that publishes the response, so a response copied
  under another identity does not decrypt.
* The nonce is 12 random bytes, fresh for every response.
* The strings are ASCII without a terminator.

## Payload

Each slot is a 32-byte secp256k1 private key. Slots are in this order: the granted authentication
bindings in request order, then the granted encryption bindings in request order. A declined or
omitted binding has no slot. The payload is `28 + 32n` bytes, where `n` is at least 1 and at most
the number of bindings.

# App Processing of connect

**Polling.** The app queries `loginKeyResponse` with `appEphemeralPubKeyHash == hash160(appEphPub)`,
ordered by `$ownerId`, and pages after the last owner. With an `IDENTITY_HINT` it adds
`$ownerId == hint`. It SHOULD poll every few seconds, immediately when it regains focus or receives
the return link, and give up after about 10 minutes or 20 candidates.

**Verification.** An app MUST accept a candidate only if all of these hold, using proved reads:

1. With an `IDENTITY_HINT`, the candidate's `$ownerId` equals it.
1. The payload is `28 + 32n` bytes with `n` no larger than the number of bindings, and it decrypts
   under the envelope above.
1. Every slot is a key on `$ownerId` (by point for ECDSA_SECP256K1, by `hash160` of the point for
   ECDSA_HASH160) that is not disabled.
1. Every session key has bounds equal to one requested authentication binding, a level allowed for
   it, and every limit the binding asked for.
1. Every encryption key is MEDIUM, ECDSA_SECP256K1, bound `singleContract` to a requested encryption
   binding's contract with the same purpose, and is that contract's current key for the purpose.
1. No key is MASTER, unbound, of another purpose, or bound to anything not requested, and no binding
   has two keys.
1. The primary binding is granted.
1. No key expires within one hour of the latest block time, and every budgeted key has budget left.

An app MAY also reject a session key that has no budget or no expiry, since wallets are required to
set both.

Anything else rejects the whole candidate. Since the slot order is fixed but slots may be omitted,
the app classifies each key by finding it on chain, not by its position. A key that is not yet
visible SHOULD be retried for a few seconds, because the app's node may lag the wallet's.

**Identity confirmation.** Anyone who sees the request can answer it, with their own identity. With
an `IDENTITY_HINT` only that identity is accepted. Without one, the app MUST ask the user to confirm
the identity (for example "Continue as @alice?") before treating them as signed in, and SHOULD offer
a choice when several candidates verify.

**Contract groups.** A key bound to a contract group can sign for every contract the group ever
contains. An app that requests one SHOULD check, before showing the request, that the group's owner,
administrators and members are the ones it expects.

**Signing.** The app SHOULD sign each write with the narrowest granted key that covers it, and route
anything its keys cannot sign to the wallet with a `sign` request. It renews by sending a new login
request when a key nears its expiry or its budget runs out.

# Transition Signing

`sign` asks the wallet to sign one state transition the app built and cannot sign itself: for
example a credit transfer, a DPNS registration, a DashPay contact request, a token purchase, or an
identity update that needs the MASTER key.

1. **Decode.** The wallet MUST decode the transition with a bounded decoder, and refuse what does not
   decode, or is already signed (its own signature field is non-empty), as `invalid`. Signatures
   the transition carries for keys it adds are not its own signature.
1. **Scope.** This verb covers transitions signed by an identity key. A transition with no identity
   signer (identity create, identity top-up, or one funded from addresses) is `unsupported`.
1. **Identity.** The transition MUST be for the identity active in the wallet. If it is for another
   identity the wallet holds, the wallet MUST name it and ask the user to switch, and MUST NOT
   switch silently. The wallet MUST check again after the user authenticates.
1. **Every kind.** A wallet MUST accept every state transition type signed by an identity key, and
   MUST NOT refuse a transition because of its kind. The user decides.
1. **Describe.** The wallet SHOULD describe the transition in plain words: what it does, which
   identity and key sign it, every key an identity update adds or disables (with their purposes,
   levels, bounds and limits, and a warning when a MASTER key is involved), every token amount and
   recipient, and any non-zero `userFeeIncrease`. Where the wallet cannot describe a kind or a field
   completely, it MUST show the decoded fields rather than a summary that hides them, and MUST NOT
   offer approval from a summary line alone.
1. **Choose the key.** The wallet MUST sign with an enabled key of the identity that has no contract
   bounds, budget or expiry, so never with an App Connect session key, and with the purpose and
   level Platform requires for that kind. Among the eligible keys it SHOULD prefer the lowest level
   Platform accepts, then the lowest key id. With no eligible key it says so and answers `failed`.
1. **Sign as given.** The wallet signs the transition's canonical bytes, setting the signing key's
   id itself, and broadcasts them. A retry re-broadcasts the identical bytes; if the first copy
   landed, Platform refuses the second as a used nonce. A stale nonce or revision is `stale`, and
   the app rebuilds the transition.
1. **Result.** There is no response document. The app watches Platform for the transition's effect
   until `exp` plus a few minutes. `cb`, when present, follows [Return Link](#return-link).

# Status Codes

The `ac` value appended to a return link:

| `ac` | `connect` | `sign` |
| --- | --- | --- |
| `ok` | Keys registered and the response published | Signed, and the broadcast was accepted |
| `declined` | The user declined | The user declined |
| `stale` | `CREATED_AT` too old or too far ahead | `exp` passed, or the nonce or revision is out of date |
| `unsupported` | An unknown version, even field type or binding kind, an unknown `v`, or bindings the wallet does not support yet (see [Deployment and Compatibility](#deployment-and-compatibility)) | An unknown `v`, or a transition not signed by an identity key |
| `invalid` | Malformed, or breaks a rule of this DIP | Malformed or already signed |
| `failed` | Wrong network, no identity matching `IDENTITY_HINT`, a derived key already on the identity with other limits, or approved but registering or publishing failed | Wrong network or identity, no eligible key, or anything else |

An app MUST treat an unknown `ac` value as `failed`, and keep polling.

# Security Considerations

**The request is a bearer request.** Whoever scans a request can answer it. A page can show a
request it copied from another site, and the identity confirmation step is what stops a user from
being signed in as someone else. Apps MUST NOT treat a verified response as a login until the user
has confirmed the identity, or the response's owner matches the `IDENTITY_HINT`.

**Phishing for scope.** Any page can show a request naming any `appId` and asking for the largest
scope and budget that app's owner could grant. The wallet shows the app id and every scope, budget
and expiry; Platform enforces them; and the wallet's caps bound the budget. The owner consistency
rule stops a request from showing one app while asking for authentication keys on another owner's
contracts (apart from DashPay `profile`). It does not apply to encryption bindings; see below. There
is no manifest, for the reason given in [App Identity](#app-identity): it could not tell a genuine
app from a copy.

**Labels are claims.** The label is chosen by whoever made the request. Wallets show it as the
app's claim, next to the app id.

**Contract groups grow.** A contractGroup key covers every contract its group ever contains. The
group's owner and administrators can add contracts after the grant. Wallets SHOULD say so on the
approval sheet, and apps SHOULD check their group before requesting such a key.

**CRITICAL keys.** A CRITICAL session key can sign token transitions, and writes to document types
that require CRITICAL, within its bounds. Its credit budget limits fees, not the number of tokens it
moves. It is acceptable only because it is bounded; a wallet never grants an unbounded
authentication key. Wallets SHOULD warn clearly before granting one.

**Encryption keys are shared by everyone using a contract.** The key for a (contract, purpose) is
the same whichever app asks for it. That is what lets the user read their data on another device or
in another app on the same contract. It also means any app given the key can read that data,
whichever app it was written through. What a key exposes depends on the contract's scheme: under
DIP-15's pairing, the ENCRYPTION key exposes what the user sends and the DECRYPTION key what the
user receives.

**Encryption keys cannot be taken back, only rotated.** Disconnect does not disable them, so an app
that received one keeps it and can read everything encrypted to it. A [rotation](#rotation), where
the contract allows one, protects data encrypted afterwards, as far as apps and peers encrypt only
to current keys. Under the requirement `0` a key can never be replaced.
Since an encryption binding may name a contract the app's owner does not control, a request for the keys of a popular messaging contract is the obvious phishing target.
Wallets SHOULD show which contracts' data an app will be able to read, clearly flag contracts not
owned by the app's owner, and warn most strongly for system contracts.

**Return links.** A wallet that opens `cb` does so right after the user approved something, which
is a natural moment for a fake follow-up page. `cb` carries only a status. Wallets SHOULD show the
host before the user decides, and SHOULD NOT open it for requests scanned in the wallet, where the
app is usually on another device.

**Response binding.** The envelope's associated data binds the ciphertext to the request and to the
publishing identity, so a response copied under another identity does not decrypt, and the index
lets each identity respond without anyone reserving its entry.

**Hardened derivation.** Session and encryption keys are hardened children. An app that holds them
learns nothing about the identity's other keys or the recovery phrase.

**Keys accumulate.** Platform keeps disabled and expired keys on the identity. Wallets MAY disable
a previous grant's keys at the next login for the same connection, and apps SHOULD read only the
keys they need rather than the whole identity.

**Signing.** A `sign` request is built by the app and is untrusted. The wallet decodes it with
bounded resources, refuses transitions for another identity, sets the signing key itself, and never
signs with a session key, so a request cannot make the wallet sign with a key the user did not
expect.

# Deployment and Compatibility

* App Connect requires Platform protocol version 14 or later, for the response contract and for
  bounded, budgeted and expiring keys.
* The `dash-key:` v2 carrier is transitional. Wallets MAY accept it on testnet and devnet and MUST
  NOT accept it on mainnet. The `dash-key:` v1 and `dash-st:` URIs MUST NOT be accepted on mainnet.
* A wallet MAY at first support a subset of the bindings: encryption bindings for `appId` only and
  at most two of them, and CRITICAL only on contractGroup bindings. Such a wallet MUST refuse a
  request that asks for more as `unsupported`, and MUST NOT grant less than was asked instead. Apps
  SHOULD assume that a wallet reached through `dash-key:` supports only this subset. There is no
  way for an app to learn in advance what a wallet supports, so apps SHOULD ask for no more than
  they need, and SHOULD tell the user, when a wallet refuses a request as `unsupported`, that the
  wallet needs an update. Wallets built before this DIP refuse CRITICAL on another binding kind as
  `invalid`.
* Apart from naming a system contract as `appId`, which earlier wallets did not refuse, a request
  that is valid under the earlier rules is valid under this DIP, and a grant made by an earlier
  wallet keeps working.
* Wallets built before this DIP derived encryption keys at
  `m/9'/coin'/5'/7'/0'/identityId'/contractId'/purpose'`, without the rotation level, on testnet
  and devnet only. Such a key is a current key at another path the wallet derives on, so under
  [Encryption Keys](#encryption-keys) a wallet MAY keep sending it. A wallet that wants it at this
  DIP's path [rotates](#rotation) it.

# Test Vectors

The vectors below are generated by the reference app implementation and are also in
[dip-pasta-app-connect/vectors.json](dip-pasta-app-connect/vectors.json). Implementations SHOULD
reproduce them byte for byte. Long hex values are wrapped; join the lines.

## Vector Inputs

| Input | Value |
| --- | --- |
| app ephemeral private key | `83adc3b5a48a1f3938969be4e3d674210d09aec8a2c2cb2b43b22972afca8682` |
| `appId` | `Hj6B9qRVHcVB97LZGEQvKm7zFsCP85cuSkEAssc1XWL7` |
| group id | `CsPWxFwNvLPjACBCQBSXJLHAimU44DDFimzA2Jbxm9GK` |
| DashPay contract id | `Bwr4WHCPz5rFVAD87RqTs3izo4zpzwsEdKPWUT1NS1C7` |
| owner (responding identity) | `AsDve9GcVemmG7hRFkVMpX2UVQupcoFo7EAg33m8PcTA` |
| `CONNECTION_ID` | `a69b1b4f666681453dec3734667a5ab2` |
| `CREATED_AT` | `1791676800000` |
| `expiresAt` (both bindings) | `1799452800000` |
| wallet ephemeral private key | `d1772740bcf476137df337bbe42122e82da08e11b632d6c3ff0d7281576e4127` |
| nonce | `22bb26ec9e0d316c4fb36be2` |
| slot private keys | `7df2f40f15e6079e514d7e5cb9cb1861b89986906ed820e158c3144272df9586`, `3a992d9275d082af7540d1333a134ff0572c2bb79567437daa88dee55af1571f`, `b37bb0ae8d6bbf01b38e843470570d5158d1939762a88673dd6cdf71bc144753` |

The slot private keys are fixed inputs, not derived. The request has label `Yappr`, a
`CONNECTION_ID`, no `IDENTITY_HINT`, and three bindings: a contractGroup binding on the group at CRITICAL
with a budget of 50,000,000,000 credits; a documentType binding on DashPay `profile` at HIGH with a
budget of 1,000,000,000 credits; and an ENCRYPTION binding on `appId`.

## Request Vector

```text
appEphPub           03e83cb927e85f96ae50a95ca3be21cc7a3755139a941b15d99b01af4fecf0d270
hash160(appEphPub)  d77dc0da9df83a47755a15c42c5d9db9d7a7fd62

body (247 bytes)
0203e83cb927e85f96ae50a95ca3be21cc7a3755139a941b15d99b01af4fecf0d270f8833c7a2d58ab816c24ae915fe2aa94
676588b467ba1e9f2b24c1a3df7fdb7805596170707202320201b0590e59269c6885acf71d27ddfce85187e2cc9736c42e95
8127cd35be6d38e80000000ba43b7400000001a2f7beb400023a0102a2a1b4ac6fef22ea2a1a68e8123644b357875f6b412c
18109281c146e7b271bc000000003b9aca00000001a2f7beb4000770726f66696c650310a69b1b4f666681453dec3734667a
5ab20421f8833c7a2d58ab816c24ae915fe2aa94676588b467ba1e9f2b24c1a3df7fdb78010608000001a128425c00
```

As a `connect` URI on devnet, with the return link `https://yap.pr/connect?r=d77dc0da9df83a47755a15c42c5d9db9d7a7fd62`:

```text
dashpay://connect?v=2&n=d&r=AgPoPLkn6F-WrlCpXKO-Icx6N1UTmpQbFdmbAa9P7PDScPiDPHotWKuBbCSukV_iqpRnZYi0Z7oenyskwaPff9t4BVlhcHByAjICAbBZDlkmnGiFrPcdJ9386FGH4syXNsQulYEnzTW-bTjoAAAAC6Q7dAAAAAGi9760AAI6AQKiobSsb-8i6ioaaOgSNkSzV4dfa0EsGBCSgcFG57JxvAAAAAA7msoAAAABove-tAAHcHJvZmlsZQMQppsbT2ZmgUU97Dc0ZnpasgQh-IM8ei1Yq4FsJK6RX-KqlGdliLRnuh6fKyTBo99_23gBBggAAAGhKEJcAA&cb=https%3A%2F%2Fyap.pr%2Fconnect%3Fr%3Dd77dc0da9df83a47755a15c42c5d9db9d7a7fd62
```

The same request on the transitional carrier is the `request.uri` value in the vectors file. The
file also holds `renewRequest`: the same app with `MODE = 1` and an `IDENTITY_HINT` for the owner,
on testnet, without a return link. Its `response.sessionKey` field is the HKDF key, not a session
key.

## Session Key Leaf Vectors

```text
requestId for bindingIndex 0  a0ad9d4647bd9296611258b8f47db92b06bdaee8782fd28e51632403d8a66a1e
requestId for bindingIndex 1  27a2c59bcf28894aee77c809c3c0e94201db08b66648c16fdfa689e6926b4f52
hash256(appEphPub), reserved  18f020830ef82d97c975df563a075665dc2679003ce6f985a4448a0dc607234a
```

## Response Vector

```text
walletEphemeralPubKey  02ee49ae562aa74ea28f95094da6800db9244b1addc1499439ffc7382cd7862d5a
HKDF key               b9837f16975f02d7c06df91441bbf3dad51ca7d65016178f34084247dd1b703f

aad
646173683a6170702d636f6e6e6563743a7632d77dc0da9df83a47755a15c42c5d9db9d7a7fd629296d642338cb3bfceeb55
4285462719e15f004d0579ce53ea77fb6d86cd9ab9

encryptedPayload (124 bytes)
22bb26ec9e0d316c4fb36be20e3f2a358cce3609d09094351ce5e78f08e5253b0f9258616374753411c97faecb1fbde336c0
1d7f08380095a0a7ffe3fe207f80e92a7adb7bd8731dffe3b96a6b2c363aa1302c4e82d60f75419aa1f6f3ac5522453f2b76
1495fb3b7816ea8bfe66a210e14fdad8b7f7c15ffb3ef39b

slot public keys
03ad37affe6d1018d4c4f24429a749e64be98650a76935f0094d2b74577b3e64be  hash160 6a584cee34f9db5658af56dbb4ae4afd9da41f0e
029029b4134dc7b49071545ddd3b5743a41ea831c647defe988fa2663c57b6ef9e  hash160 ccb3641d29579908ef4bb127a9490431de470c7a
022dfa00c086d19058f0b80d7d6eb4caa4a65e8f3f50dbabcf675dbc165096b7f5  hash160 c53b46c1ccc8e7e58920e6e010be233fa3166ae0
```

## Key Derivation Vectors

From the BIP 39 phrase `abandon abandon abandon abandon abandon abandon abandon abandon abandon
abandon abandon about` with an empty passphrase. `0x35…`, `0x6b…`, `asc` and `desc` are 32-byte
DIP-14 indexes: every byte `0x35`, every byte `0x6b`, bytes `00 01 … 1f`, and bytes `ff fe … e0`.

| Path | Public key |
| --- | --- |
| `m/9'/1'/5'/6'/0'/0x35…'/0x6b…'` | `022c8b2e806244482374b1caf8306146dc03aad3b99a5954efd5e70a0eddd37a5d` |
| `m/9'/5'/5'/7'/0'/0x35…'/0x6b…'/1'/0'` | `031a882c119e2b1f8e0349b444d877afa2599efeef49a26930fd25518cb6e9d57a` |
| `m/9'/5'/5'/7'/0'/0x35…'/0x6b…'/1'/1'` | `03d0f6f0f48d968b9554d8e7fe467d7135bacf29d5c4994ca593bd10ebeed696f6` |
| `m/9'/1'/5'/6'/0'/asc'/desc'` | `0278ad78c1a220924bf0e06e1111c61422efeace068f30efa825604b436970b230` |
| `m/9'/5'/5'/7'/0'/asc'/desc'/1'/0'` | `02dfed57ddaaea8c0758e8da44513520038eb8d6b0b92109953c14d6ab1087259b` |
| `m/9'/5'/5'/7'/0'/asc'/desc'/2'/0'` | `020bcde800f41ad1f924477a9502f111445224cc9ab70114ae4e5099ba02bdd034` |
| `m/9'/5'/5'/7'/0'/asc'/desc'/2'/1'` | `021b97869c21933673076a938337c28848c8bf8094bbe6883e3a4acbf33c639072` |

All rows are pinned in rust-dashcore `key-wallet` (`bip32.rs`). It also pins the earlier paths
without the rotation level, which wallets derive only to recognise registrations made before this
layout (for example `…/0x35…'/0x6b…'/1'` is
`03e989de1b62f137231cc06659c810c17100becd1f5e23d5710faa7602769fe434`); those keys are the parents
of the corresponding rows above.

# Reference Implementations

* App side: `platform-auth`, `src/app-connect/` (request codec, envelope, verifier, poller), vendored
  in Yappr.
* Wallets: dashwallet-ios
  [#1202](https://github.com/dashpay/dashwallet-ios/pull/1202),
  [#1204](https://github.com/dashpay/dashwallet-ios/pull/1204) and
  [#1210](https://github.com/dashpay/dashwallet-ios/pull/1210); dash-wallet
  [#1604](https://github.com/dashpay/dash-wallet/pull/1604). These implement the transitional
  carrier, encryption bindings for `appId` only, CRITICAL only on contractGroup bindings, and the
  encryption path without the rotation level.
* Response contract: `packages/app-connect-contract` in `dashpay/platform`.

# Copyright

Copyright (c) 2026 Dash Core Group, Inc. [Licensed under the MIT License](https://opensource.org/licenses/MIT)
