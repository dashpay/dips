<pre>
  DIP: TBD
  Title: Private Document Types and Anonymous DashPay Contact Requests
  Author(s): Samuel Westrich
  Special-Thanks: Dash Platform Team
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2026-11-10
  License: MIT License
  Requires: 0011, 0015
</pre>

## Table of Contents

1. [Abstract](#abstract)
1. [Motivation](#motivation)
1. [Prior Work](#prior-work)
1. [Terminology](#terminology)
1. [Specification](#specification)
   1. [Overview](#overview)
   1. [Private Document Types](#private-document-types)
   1. [Storage](#storage)
   1. [Appending Entries](#appending-entries)
   1. [Reading Entries](#reading-entries)
   1. [Standard Envelope](#standard-envelope)
   1. [DashPay Private Contact Requests](#dashpay-private-contact-requests)
1. [Rationale](#rationale)
1. [Backwards Compatibility](#backwards-compatibility)
1. [Security Considerations](#security-considerations)
1. [Privacy Considerations](#privacy-considerations)
1. [Test Vectors](#test-vectors)
1. [Future Extensions](#future-extensions)
1. [Copyright](#copyright)

## Abstract

This DIP specifies **private document types** on Dash Platform and their first use, **anonymous DashPay contact requests**.

A data contract can declare a document type private. A private type is an append-only store of fixed-size encrypted entries that Platform never reads. Anyone can append an entry by paying from the shielded pool, so no identity is attached to the write. There is no index: a recipient finds its entries by trying to decrypt each one, the same way a wallet finds its shielded notes.

The DIP defines the contract keyword, the storage, the state transition that appends entries, the query that reads them, and a standard envelope that clients use to encrypt an entry to one recipient, authenticate its sender, and let the sender recover it from seed. It then defines the DashPay `privateContactRequest` type on top: a contact request that reveals to observers neither who sent it nor who received it.

## Motivation

A [DIP-15](dip-0015.md) contact request is a public document. Its owner is the sender and its `toUserId` is the recipient, and an index lets anyone list every identity that contacted a given identity, with times. The contents are encrypted, but the relationship is not. For a payment application that is a serious leak: who a user's contacts are is often more sensitive than what they pay each other.

Hiding the relationship needs three things that an ordinary document cannot offer:

1. **No sender on the write.** An identity-signed document names its owner. The write has to be paid for without an identity.
2. **No recipient on the entry.** Any index or field naming the recipient reveals it. The recipient has to find its entries without the chain knowing whose they are.
3. **No readable content.** The chain must store the entry without being able to check or read it.

The same three needs arise for private payment notes, invitations, and messages in other contracts. This DIP therefore specifies one generic mechanism and applies it to DashPay, instead of a contact-request-specific transition.

## Prior Work

* [DIP-0011: Identities](dip-0011.md)
* [DIP-0015: DashPay](dip-0015.md)
* [DashPay Shielded Payment Addresses](dip-quantumexplorer-dashpay-shielded-addresses.md) (draft), which defines the per-contact shielded address a private contact request carries
* [ZIP-32](https://zips.z.cash/zip-0032) and the Zcash Orchard protocol, whose note encryption (trial decryption, outgoing viewing keys) the envelope follows in spirit
* [RFC 8439: ChaCha20 and Poly1305](https://www.rfc-editor.org/rfc/rfc8439)
* [RFC 2104: HMAC](https://www.rfc-editor.org/rfc/rfc2104)

## Terminology

* **Private document type**: a document type whose contract declares the `private` keyword. Its documents are **entries**.
* **Entry**: a fixed-size block of bytes appended to a private type. Platform treats it as opaque.
* **Store**: the append-only sequence of a private type's entries. An entry's **position** is its index in the store, from 0 in append order.
* **Shielded pool**: the Dash Platform credit shielded pool. A **bundle** is a set of pool actions with its proof, as carried by every shielded transition.
* **Envelope**: the standard layout of an entry defined in [Standard Envelope](#standard-envelope).
* **`H`**: SHA-256. **`ser(P)`**: the 33-byte compressed encoding of a secp256k1 point `P`. **`||`**: concatenation. **`u16le` / `u32le`**: little-endian encodings.

## Specification

### Overview

```text
 sender wallet                     Platform                                recipient wallet
 -------------                     --------                                ----------------
 shielded notes --bundle (fee)--> append transition --> nullifiers, change notes
 envelope(plaintext) -----------> entries -----------> the type's store
                                                            |
                                   getPrivateDocumentEntries (from a position, with proof)
                                                            |
                                                            +--> try to decrypt each entry
```

Three pieces are consensus or network protocol and apply to every private type:

1. a contract keyword that declares a private type ([Private Document Types](#private-document-types), [Storage](#storage));
2. one state transition that appends entries and pays from the shielded pool ([Appending Entries](#appending-entries));
3. one query that reads a store ([Reading Entries](#reading-entries)).

Two pieces are client conventions:

1. the envelope every client uses to fill an entry ([Standard Envelope](#standard-envelope));
2. the rules of each application; this DIP gives DashPay's ([DashPay Private Contact Requests](#dashpay-private-contact-requests)).

Everything in this DIP activates at Platform protocol version 15.

### Private Document Types

A document type is private when it declares:

```json
"private": { "entrySize": 589 }
```

Registration rules:

* `private` MUST be an object holding exactly `entrySize`, an integer from `1` to `4096`. Any other key is refused.
* A private type's `properties` describe the **plaintext** of an entry. They are checked at registration like any schema, so that clients can decode a decrypted entry with types. Platform never checks an entry against them.
* A private type MAY declare only these type-level keywords, each at most once: `type`, `properties`, `required`, `additionalProperties`, `minProperties`, `maxProperties`, `dependentRequired`, `description`, `$comment`, `requiresIdentityEncryptionBoundedKey`, `requiresIdentityDecryptionBoundedKey`, and `documentsMutable`, `canBeDeleted` and `documentsKeepHistory`, which MUST be `false`. Every other type-level keyword is refused, including indices, transfer and trade, creation restrictions, token costs, and moderation. Each of those is a promise Platform cannot keep without reading the document.
* Neither `properties`, `required` nor `dependentRequired` may name a system field (such as `$ownerId` or `$createdAt`): an entry has none.
* No property, at any depth, may declare a keyword Platform evaluates per document: `refersTo`, `distinctFrom`, `generatedFrom`, `encryptedFor`, `requiredSince`.
* No other document type may refer to a private type or count or sum over it.
* Platform does not compare `entrySize` with the properties. Clients MUST refuse to register a private type whose `entrySize` is smaller than its largest possible payload plus the envelope's 299 bytes, or whose properties are not all bounded in size.

Update rules:

* `private` is frozen. A type cannot change between public and private, and `entrySize` cannot change. A contract update MAY add new private types.
* An update MAY add properties to a private type only after the existing ones, at the end of the type and at the end of each nested object. Entries carry no version, so old entries must still decode under the updated type.

Writes and reads:

* Only the transition in [Appending Entries](#appending-entries) writes to a private type. A document batch transition MUST be refused for every document action (create, replace, delete, transfer, purchase, price update) that names a private type (consensus error `10425`).
* Document queries on a private type MUST be refused. Entries are read only with the query in [Reading Entries](#reading-entries).

### Storage

* A private type has one store and no index. The store takes the place where other types keep their documents by id.
* Each stored entry is a 16-byte **header** written by Platform, followed by the entry's `entrySize` bytes. The header is the height of the block that appended the entry (unsigned 64-bit, little-endian) and that block's time in milliseconds (unsigned 64-bit, little-endian). It gives a recipient a time it can trust, which nothing inside a ciphertext could be, and it reveals nothing new.
* The store is append-only. An entry is never changed or removed.
* The store is created wherever its contract comes to exist: at contract registration, when a contract update adds the type, and when a system contract is installed or upgraded.
* The store is divided into chunks of `2^chunkPower` entries. `chunkPower` is fixed when the store is created, by the rule below.

```text
chunkPower = clamp(floor(log2(1048576 / (16 + entrySize))), 4, 11)
```

A 589-byte entry gives `10` (1024 entries, about 605 KiB per chunk); a 4096-byte entry gives `7`.

### Appending Entries

Entries are appended by the state transition `PrivateDocumentCreateFromShieldedPool`, type `29`:

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `dataContractId` | 32 bytes | The contract that defines the private type |
| `documentTypeName` | string | The private type |
| `entries` | list of byte strings | The entries, appended in this order |
| `actions` | list of shielded actions | The credit pool bundle that pays the fee |
| `valueBalance` | unsigned 64-bit | Credits leaving the pool: exactly the fee |
| `anchor` | 32 bytes | Root of the note commitment tree the bundle was built against |
| `proof` | bytes | The bundle's proof |
| `bindingSignature` | 64 bytes | The bundle's binding signature |

The transition has no identity, no nonce, and no identity signature. The bundle's spend authorization authorizes the payment, and its nullifiers prevent replay, as for a shielded transfer.

**Binding.** The bundle's signature hash commits to the target and to every entry through this extra data (33 bytes):

```text
0x1d || SHA-256(dataContractId || u32le(len(documentTypeName)) || documentTypeName
                || u32le(count(entries)) || for each entry in order: u32le(len(entry)) || entry)
```

Changing any byte of the target or of an entry, or the number or order of entries, invalidates the bundle.

**Structure.** A transition MUST carry from `1` to `16` entries, all of the same length, at most `4096` bytes each, and no two identical (consensus errors `10426`, `10427`, `10428`).

**Fee.** `valueBalance` MUST equal the required fee exactly; a larger value is refused as well, because an unusual fee would distinguish its sender:

```text
fee = minimum_shielded_fee(count(actions))
    + count(entries) * ((entrySize + 32) * per_byte_rate + 10000000)
```

`minimum_shielded_fee` is the pool's fee for a bundle of that many actions, and `per_byte_rate` is Platform's storage rate per byte (disk usage plus processing). The 32 bytes cover the header and storage framing. The flat 10,000,000 credits per entry price the work each entry costs every wallet that scans the type. The fee depends only on the number of actions, the number of entries, and `entrySize`, so a wallet computes it before building the bundle. At the fee schedule of protocol version 15, a two-action bundle with one 589-byte entry costs 114,140,000 + 27,015,400 = 141,155,400 credits.

**State checks.** In this order, and each refusal is free (no fee is taken):

1. the pool holds at least its minimum number of notes, the anchor exists, the nullifiers are unspent, and the pool holds the fee;
2. the contract exists and has the type, and the type is private (`40151`);
3. each entry's length equals the type's `entrySize` (`40152`).

**Execution.** The nullifiers and the bundle's change notes are recorded, the pool's total is lowered by the fee, and each entry is appended to the store in order, behind its header. A transition's entries take consecutive positions.

The proof that a transition was executed proves its nullifiers. It does not give the positions of its entries; the sender finds those by scanning.

### Reading Entries

The query `getPrivateDocumentEntries`:

```text
request:  dataContractId, documentTypeName, startPosition (unsigned 64-bit), prove (boolean)
response: entries [ { position, blockHeight, blockTimeMs, data } ] and totalCount
          or a proof of the same
```

* A page starts at `startPosition` and runs to the end of the store chunk that holds it, or to the end of the store. `startPosition` need not be aligned to a chunk.
* `data` is the entry as appended (`entrySize` bytes). `blockHeight` and `blockTimeMs` are its header.
* `totalCount` is the number of entries the store holds.
* Clients SHOULD request proofs. A proof also yields the store's `chunkPower`, from which a client computes the next page's start. An unproved page can omit entries or misstate header times.

A wallet scans a store by reading pages from the position it last reached, and persists that position.

### Standard Envelope

The envelope is a client convention: Platform stores whatever bytes an entry holds. Every client of a private type MUST use it unless the type's own specification says otherwise.

#### Layout

An entry of `entrySize` bytes, with `B = entrySize - 162`:

| Field | Size | Contents |
| ----- | ---- | -------- |
| `cm` | 32 | Keyed commitment to the recipient key, the target, and the body |
| `epk` | 33 | The sender's ephemeral secp256k1 public key, compressed |
| `body_ct` | `B + 16` | ChaCha20-Poly1305 ciphertext of the body |
| `out_ct` | 81 | Sender-recovery ciphertext |

Derivation, for a recipient key `R`, a 32-byte `eskSeed`, and the sender's outgoing viewing key `ovk`:

```text
esk     = H("Dash/PrivDoc/v1/esk" || eskSeed), read as a big-endian scalar
epk     = esk * G
key     = H("Dash/PrivDoc/v1/key" || ser(esk * R) || ser(epk) || ser(R))
cm      = H("Dash/PrivDoc/v1/cm" || key || contractId || u32le(len(type)) || type || ser(R) || body)
body_ct = ChaCha20-Poly1305(key = key, nonce = 0, aad = cm, plaintext = body)
ock     = H("Dash/PrivDoc/v1/ock" || ovk || ser(epk))
out_ct  = ChaCha20-Poly1305(key = ock, nonce = 0, aad = cm, plaintext = ser(R) || eskSeed)
```

* `eskSeed` MUST be 32 fresh random bytes for every entry built, never reused, not even when retrying a failed send. The zero nonce is safe only because each key encrypts once.
* If `H("Dash/PrivDoc/v1/esk" || eskSeed)` is zero or not below the curve order, the seed is refused and another is drawn. It is not reduced.
* `esk * R` and every other shared point is serialized compressed (33 bytes). This is not DIP-15's hashed shared secret.
* `type` is the document type name in UTF-8, and `contractId` the 32-byte contract identifier.
* The domain strings are ASCII with no terminator.

#### Body

The body is `B` bytes:

| Field | Size | Contents |
| ----- | ---- | -------- |
| `version` | 1 | `1` |
| `authMode` | 1 | `0` anonymous, `1` deniable MAC, `2` signature |
| `senderIdentityId` | 32 | Zeros when anonymous |
| `senderKeyId` | 4 | `u32le`; zero when anonymous. What it names is the application's rule |
| `auth` | 65 | See [Authentication](#authentication) |
| `recipientIdentityId` | 32 | The identity the entry is for |
| `payloadLength` | 2 | `u16le` |
| `payload` | `payloadLength` | The type's properties ([Payload](#payload)) |
| padding | rest | Zeros |

The header before the payload is 137 bytes, so an entry holds a payload of at most `entrySize - 299` bytes.

#### Authentication

Authentication covers:

```text
m = H("Dash/PrivDoc/v1/auth" || version || authMode || contractId || u32le(len(type)) || type
      || senderIdentityId || senderKeyId || recipientIdentityId || ser(R)
      || payloadLength || payload)
```

`m` names the recipient key, so an entry re-encrypted to another key of the same identity carries no valid authentication.

* **Anonymous (`0`).** `senderIdentityId`, `senderKeyId`, and `auth` are all zeros.
* **Deniable MAC (`1`).** `auth` is `HMAC-SHA256(key = H("Dash/PrivDoc/v1/mac" || ser(s * R)), m)` followed by 33 zero bytes, where `s` is the secret key of the sender key named by `senderKeyId`. The recipient computes the same key from its own secret key and the sender's public key. Either side could have produced the MAC, so the recipient cannot prove to anyone who wrote the entry. Anyone holding the recipient's key can produce it too, so a stolen recipient key forges entries from any sender.
* **Signature (`2`).** `auth` is a recoverable ECDSA signature over `SHA-256(SHA-256(m))` in compact form: a header byte `31 + recoveryId`, then `r || s`. This is how a Dash identity signer signs the data `m`, so a wallet signs an entry with the signer it signs transitions with. The signing key is recovered from the signature. Which keys may sign is the application's rule.

All three sit inside the encrypted body. Only the recipient, and the sender with its outgoing viewing key, see who wrote an entry.

#### Opening an Entry

A recipient with a set of secret keys processes each entry of a store:

1. If `epk` is not a valid point, the entry is not for it.
2. For each of its keys `r` with public key `R`: compute `key` from `r * epk`, decrypt `body_ct`, and recompute `cm`. If decryption fails or `cm` does not match, it MUST try its next key instead of discarding the entry. If no key opens the entry, the entry is not for it.
3. The body MUST be refused unless `version` is `1`, `authMode` is `0`, `1` or `2`, the padding is all zeros, and the sender fields fit the mode: all zeros when anonymous, the last 33 bytes of `auth` zeros for a MAC, a header byte from 31 to 34 for a signature.
4. `recipientIdentityId` MUST be the recipient's own identity, or the entry is refused.
5. The sender is then checked by the application's rule, and the payload decoded and validated against the type's properties.
6. Two entries with the same `cm` are copies; the first by position is kept.

#### Sender Recovery

A sender recovers the entries it built, for example after restoring from seed, with `ovk` alone. For each entry it computes `ock` from `epk` and tries to decrypt `out_ct`. On success it obtains `ser(R)` and `eskSeed`, recomputes `esk`, checks that `esk * G` equals `epk`, derives `key`, and decrypts the body. An entry whose `out_ct` opens but whose body does not is malformed.

How `ovk` is derived is the application's rule. It MUST be derivable from the wallet seed.

#### Payload

The payload is the type's properties in Platform's document property encoding, as a document writes them after its system fields:

* properties are written in `position` order;
* a required property is written as its value;
* an optional property is written as one byte, `0x00` when absent or `0x01` when present, followed by its value when present;
* an integer is written big-endian at its stored width;
* a fixed-size byte array is written as its bytes;
* a variable-size byte array or a string is written as its length (an unsigned varint) followed by its bytes.

A sender MUST validate the properties against the type's schema before encoding. A reader MUST refuse a payload that is cut off or that has bytes left over, and MUST validate the decoded properties against the type's schema.

### DashPay Private Contact Requests

Version 3 of the DashPay contract declares:

```json
"privateContactRequest": {
  "type": "object",
  "private": { "entrySize": 589 },
  "documentsMutable": false,
  "canBeDeleted": false,
  "properties": {
    "accountReference": { "type": "integer", "minimum": 0, "maximum": 4294967295, "position": 0 },
    "extendedPublicKey": { "type": "array", "byteArray": true, "minItems": 69, "maxItems": 69, "position": 1 },
    "accountLabel": { "type": "string", "maxBytes": 63, "position": 2 },
    "autoAcceptProof": { "type": "array", "byteArray": true, "minItems": 38, "maxItems": 102, "position": 3 },
    "shieldedAddress": { "type": "array", "byteArray": true, "minItems": 43, "maxItems": 43, "position": 4 }
  },
  "required": ["accountReference", "extendedPublicKey"],
  "additionalProperties": false
}
```

#### Payload Fields

A private contact request carries what a [DIP-15](dip-0015.md) contact request carries, in the clear inside the entry. The entry is already encrypted to the recipient, so no field is encrypted a second time.

| Property | Encoded size | Meaning |
| -------- | ------------ | ------- |
| `accountReference` | 8 | The DIP-15 account reference, as a 64-bit big-endian integer |
| `extendedPublicKey` | 69 | The DIP-15 compact extended public key the recipient pays to: parent fingerprint (4), chain code (32), public key (33) |
| `accountLabel` | 1, or 2 + up to 63 | Optional label for the account, UTF-8 |
| `autoAcceptProof` | 1, or 2 + 38 to 102 | Optional DIP-15 auto-accept proof |
| `shieldedAddress` | 1, or 44 | Optional per-contact shielded payment address, 43 raw bytes |

The largest payload is 8 + 69 + 65 + 104 + 44 = 290 bytes, and 290 + 299 = 589, the type's `entrySize`. There is no spare byte: any further field needs a new type.

The fields a public contact request has and this one lacks come from the envelope and the header instead: `toUserId` is `recipientIdentityId`, the sender's key index is `senderKeyId`, the recipient's key index is whichever of its keys opened the entry, and the creation time is the header's block time.

#### Keys

* **Recipient key `R`.** An enabled `ECDSA_SECP256K1` key of the recipient identity with purpose `DECRYPTION`, the key DIP-15 encrypts contact requests to. A key with purpose `ENCRYPTION` is accepted as well, because some DIP-15 clients use one key for both. A key bound to a contract MUST be bound to DashPay or to its contact request types.
* **Sender key.** `senderKeyId` names the sender's enabled `ECDSA_SECP256K1` key with purpose `ENCRYPTION`, the key DIP-15 derives the pair's shared key from.
* **Signature.** Private contact requests use authentication mode `2`. The signer MUST be an enabled, unexpired `AUTHENTICATION` key of the sender identity, of type `ECDSA_SECP256K1` or `ECDSA_HASH160`, at security level `CRITICAL` or `HIGH`. If the key is bound to a contract, it MUST be bound to DashPay as a whole or to its `privateContactRequest` type. These are the key types and levels that may sign a public contact request's transition.
* **Outgoing viewing key.** `ovk = H("Dash/PrivDoc/v1/ovk" || s)`, where `s` is the 32-byte secret key of the sender's `ENCRYPTION` key named by `senderKeyId`. An identity that has changed its encryption key scans with the key of each.

The DIP-15 derivations from the extended public key, and the DIP-15 shared key of the pair, are unchanged; they use the two keys named above.

#### Sending

1. Build the payload. If the wallet supports shielded payment addresses, `shieldedAddress` MUST be the sender's per-contact address derived as [DashPay Shielded Payment Addresses](dip-quantumexplorer-dashpay-shielded-addresses.md#per-contact-diversifier-index) specifies, with `ownerId` the sender identity, `toUserId` the recipient identity, and `accountReference` the payload's value. A wallet MUST NOT place the same shielded address in requests to two different recipients.
2. Compute `m`, have the identity signer sign it with a permitted key, and seal the entry with a fresh `eskSeed`.
3. Append it with a `PrivateDocumentCreateFromShieldedPool` transition paid from the wallet's shielded balance.

The sender needs a shielded balance. Shielding funds immediately before sending links the two events in time, so wallets SHOULD keep a standing shielded balance.

#### Receiving

A wallet scans the `privateContactRequest` store with the secret keys of every key of its identities that a request may be encrypted to ([Keys](#keys)). For an entry that opens, it MUST refuse the request unless all of the following hold, with every key evaluated as it was at the entry's block time (keys are disabled, never removed):

* the authentication mode is `2`. An anonymous entry, or one carrying a deniable MAC, is refused: anyone holding the recipient's key could have written the latter;
* the sender identity exists;
* the key named by `senderKeyId` is an `ECDSA_SECP256K1` `ENCRYPTION` key of the sender that was not disabled;
* the key recovered from the signature is a key of the sender that was permitted to sign ([Keys](#keys)) and was neither disabled nor expired;
* the recipient key the entry opened under was not disabled;
* the payload is a valid `privateContactRequest`.

The sender's identity MUST be read from a state proved at or after the block that appended the entry, so that a key disabled in that block shows as disabled.

**Shielded address.** A `shieldedAddress` in a request the wallet keeps is a per-contact address, and the wallet uses it under the same checks as one received in a public contact request ([DashPay Shielded Payment Addresses](dip-quantumexplorer-dashpay-shielded-addresses.md#per-contact-shielded-addresses)): it decodes as a valid shielded payment address, it is not an address of any account of the wallet's own, and it differs from the sender's current profile `shieldedAddress`. An address that fails a check is ignored; the request stands.

**Duplicates.** Of several valid requests from the same sender to the same recipient with the same `accountReference`, the first by position is kept and the rest are ignored.

**Rotation.** A request from a known sender with a different `accountReference` is a rotation, as in DIP-15: the newest takes effect.

#### Accepting

A user accepts a private contact request by sending a private contact request back. A wallet MUST NOT answer a privately received request with a public [DIP-15](dip-0015.md) contact request, and MUST NOT send a public contact request to a contact established privately: either would publish the relationship the private request hid.

`autoAcceptProof` has its DIP-15 meaning. Because the reply spends the recipient's shielded funds, wallets SHOULD NOT send it without the user's confirmation.

#### Restore

A wallet restored from seed recovers received requests by scanning the store from position 0 with those keys, and sent requests by scanning with the outgoing viewing key of each of its encryption keys. A sent entry is accepted only if it names the identity and encryption key its outgoing viewing key belongs to, and is signed by a key of that identity. Disabled keys need scanning once, at restore; ordinary sync uses the keys in use.

## Rationale

* **One generic mechanism.** Contact requests, payment notes, invitations, and messages all need a write with no sender, no visible recipient, and no readable content. One keyword, one transition, and one query serve them all, and a new private application needs no consensus change.
* **One store per type, not a shared mailbox.** A shared store would make every client try to decrypt every application's traffic.
* **Paid from the shielded pool.** Any identity-paid write names its payer. The pool is the only payer on Platform that does not.
* **One type per transition.** Mixing types would let one transition link its payer across applications.
* **An exact fee.** The fee is a function of public sizes only, so a wallet can compute it ahead of time, and no transition stands out by overpaying.
* **A flat fee per entry.** Every wallet of a type downloads and tries every entry. The flat part prices that shared cost, on top of storage.
* **A header written by Platform.** A recipient must know when an entry was written to judge whether the sender's key was valid then. Nothing inside a ciphertext can be trusted for that.
* **A keyed commitment.** An unkeyed hash of the recipient key and the plaintext would let anyone confirm a guess about an entry. Keying it with the entry key prevents that, and committing to the recipient key rejects a ciphertext crafted to open under several keys.
* **No uniqueness enforced by the chain.** A sender-chosen uniqueness tag can be copied by anyone who sees the transition before it executes, permanently blocking the honest sender. Recipients deduplicate after decrypting instead.
* **Signatures for DashPay, not deniable MACs.** A deniable MAC can be forged by whoever holds the recipient's key, which would let a thief of that key forge a rotation and redirect payments. A signature cannot. The cost is that the recipient holds proof of who contacted it; the proof is inside the encrypted entry and visible to nobody else.
* **The outgoing viewing key from the encryption key.** It needs no new derivation path and is recoverable from seed with the key it belongs to.
* **Plaintext fields inside the entry.** The envelope already encrypts and authenticates the whole payload to the same key pair, so DIP-15's inner AES layer would only cost bytes.

## Backwards Compatibility

* Private document types, the append transition, and the query activate at Platform protocol version 15. Before it, the keyword cannot be registered and the transition is refused.
* The DashPay `privateContactRequest` type is added in version 3 of the DashPay contract at the same protocol version.
* The public DIP-15 `contactRequest` is unchanged and remains valid. Wallets that do not implement this DIP are unaffected, and cannot see private contact requests.
* A wallet that supports both handles a contact as public or private according to how the relationship was established ([Accepting](#accepting)).

## Security Considerations

* **Platform checks nothing inside an entry.** Recipients check everything: the decryption, the commitment, the recipient identity, the sender's authentication, and the payload's schema. A client that skips a check accepts forgeries.
* **Key state at the entry's time.** A sender key or recipient key is judged as of the entry's block time, from a state proved at or after that block. Judging by current state alone would accept an entry written with a key that had already been disabled.
* **Copied entries.** Anyone can append a copy of an existing entry at their own cost. It has the same `cm` and is dropped.
* **Stolen recipient key.** With signatures, a stolen recipient key reads that identity's incoming requests but forges none.
* **Fresh seeds.** Reusing an `eskSeed` reuses a key with a zero nonce, which breaks the confidentiality of both entries.
* **Flooding.** Entries cost their sender a fee each, but a determined sender can still append many. Wallets SHOULD bound the work they spend on one sender (for example, one pending request per sender) and let users block senders.
* **Stale contracts.** A payload written after a type gained a property reads as invalid to a client holding the older contract. Clients SHOULD refetch the contract and read the entry again before discarding it.
* **Halting.** A private type's store is created on every path that creates the type, and the append transition checks that the store exists before execution, so an append cannot fail during block execution.

## Privacy Considerations

* **What observers see**: which contract and type each entry belongs to, how many entries a type receives and when, and that the entries of one transition share a payer.
* **What observers do not see**: the sender (the pool pays), the recipient (no index; every wallet scans the whole store), and the content.
* **What the recipient learns**: the sender's identity, and a signature it could show to others.
* **Timing.** Shielding funds and then immediately sending a request links the two. So does establishing a contact and immediately making a visible payment.
* **Network-level correlation.** A node serving a wallet sees its queries. Fetching a sender's identity right after reading a page tells the node which identity the wallet is interested in; fetching a recipient's keys right before sending does the same. Wallets SHOULD cache identities and avoid lookups adjacent to the events they relate to.
* **Unproved pages.** A node can hide entries from a wallet that does not ask for proofs.
* **Quantum adversaries.** Entries are encrypted with secp256k1 ECDH to keys that are public on chain, and entries are never deleted. An adversary able to compute discrete logarithms can decrypt recorded entries later. Post-quantum protection is out of scope.

## Test Vectors

A full entry, with every intermediate value and the program that generates it against Dash Platform's implementation, is in [test-vectors.md](dip-quantumexplorer-anonymous-contact-requests/test-vectors.md). It is a DashPay `privateContactRequest` in signature mode, opened by its recipient and recovered by its sender. Summary:

| Value | Hex |
| ----- | --- |
| `eskSeed` | 32 bytes of `0x55` |
| Recipient secret key | 32 bytes of `0x22` |
| `epk` | `031ab0e922099ceeeafcf1d408f5ed8f626b130cd8c1f8f73a21618180ee5c07ac` |
| `m` | `4ae9182d57eb14a5dfdbfb21bb2100a0cb6b2597fa3dc5b5312fe4b6fad08650` |
| `cm` | `44e17df1a8f4244d0f6e34061cf3df8637c8a036adfaa455204b834640f91de7` |

## Future Extensions

* **Proven constraints.** A later version can let a private type declare constraints (for example, that the sender's key is registered, or a uniqueness tag) proven in zero knowledge with each entry. Unknown keys inside `private` are refused today so that such keys can be added safely, and `cm` keeps a fixed position so that its formula can change with the envelope version.
* **Identity-funded private documents.** For applications whose sender is public anyway, a sibling transition could let an identity pay for an entry whose recipient and content stay hidden.
* **Retiring the public contact request.** Once wallets have adopted private contact requests, DashPay could stop accepting new public ones.

## Copyright

Copyright (c) 2026 Dash Core Group, Inc. [Licensed under the MIT License](https://opensource.org/licenses/MIT)
