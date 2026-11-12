<pre>
  DIP: TBD
  Title: DashPay Shielded Payment Addresses
  Author(s): Samuel Westrich
  Special-Thanks: Dash Platform Team
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2026-11-10
  License: MIT License
  Requires: 0013, 0015
</pre>

## Table of Contents

1. [Abstract](#abstract)
1. [Motivation](#motivation)
1. [Prior Work](#prior-work)
1. [Terminology](#terminology)
1. [Specification](#specification)
   1. [Overview](#overview)
   1. [Identity Shielded Accounts](#identity-shielded-accounts)
   1. [Profile Shielded Address](#profile-shielded-address)
   1. [Per-Contact Shielded Addresses](#per-contact-shielded-addresses)
   1. [Per-Contact Diversifier Index](#per-contact-diversifier-index)
   1. [Rotation and Existing Contacts](#rotation-and-existing-contacts)
   1. [Shielded Memo Kinds](#shielded-memo-kinds)
   1. [Client Behavior](#client-behavior)
1. [Rationale](#rationale)
1. [Backwards Compatibility](#backwards-compatibility)
1. [Security Considerations](#security-considerations)
1. [Privacy Considerations](#privacy-considerations)
1. [Test Vectors](#test-vectors)
1. [Future Extensions](#future-extensions)
1. [Copyright](#copyright)

## Abstract

This DIP specifies how DashPay identities receive payments through the Dash Platform shielded pool. It defines:

* a shielded account for each identity, derived from the wallet seed;
* a shielded payment address published on the DashPay profile, for private payments from anyone;
* a per-contact shielded payment address carried, encrypted, in each [DIP-15](dip-0015.md) contact request, for private payments between contacts with built-in attribution;
* the rule that derives each per-contact address from the contact request that carries it, so a wallet never hands the same address to two contacts, on any device and after any restore, without keeping allocation state;
* a shielded memo kind that names what a payment is for.

Shielded payments hide the payer, the recipient, and the amount. This DIP covers contact requests as DIP-15 defines them, which are public documents; contact requests that hide the relationship itself are specified separately.

## Motivation

[DIP-15](dip-0015.md) lets two contacts pay each other on the Core chain through per-contact address chains derived from extended public keys exchanged in contact requests. Those payments are ordinary transparent transactions: their amounts are public, and anyone who learns a contact's address chain can follow it.

The Dash Platform shielded pool hides the payer, the recipient, and the amount of every payment, and a recipient detects payments by trial decryption with no discovery channel. What the pool does not define is how a DashPay user learns which shielded address to pay. Three things are missing:

1. **A published address.** There is no standard way to pay a profile privately without first becoming its contact.
2. **A per-contact address.** Paying a contact's published address tells the recipient nothing about who paid. A separate address per contact attributes each payment for free, but only if no address is ever given to two contacts.
3. **A derivation rule.** If wallets choose per-contact addresses from local state, such as a counter, two devices on the same seed can give the same address to two different contacts. Contact requests are immutable, so that mistake can never be corrected. Wallets from different vendors restoring the same seed must also agree on which accounts to scan, or funds go unseen.

This DIP fills these three gaps.

## Prior Work

* [DIP-0011: Identities](dip-0011.md)
* [DIP-0013: Identities in Hierarchical Deterministic Wallets](dip-0013.md)
* [DIP-0015: DashPay](dip-0015.md)
* [ZIP-32: Shielded Hierarchical Deterministic Wallets](https://zips.z.cash/zip-0032) (Orchard key derivation and diversifier indices)
* [Zcash Protocol Specification](https://zips.z.cash/protocol/protocol.pdf), section 5.6.4 (Orchard raw payment address and raw full viewing key encodings)
* [RFC 2104: HMAC](https://www.rfc-editor.org/rfc/rfc2104) and [RFC 5869: HKDF](https://www.rfc-editor.org/rfc/rfc5869)
* Zcash Orchard diversified payment addresses (the unlinkability mechanism this DIP builds on)

## Terminology

* **Shielded pool**: the Dash Platform shielded pool, an Orchard-based pool in which payments hide the payer, the recipient, and the amount.
* **Diversified address**: one of many unlinkable shielded payment addresses derivable from a single full viewing key; addresses at different diversifier indices cannot be linked to each other without the viewing key.
* **Diversifier index**: the 88-bit index `j` from which a full viewing key derives the diversified address at index `j` (ZIP-32). Distinct indices always give distinct addresses.
* **IVK / FVK / OVK**: the pool's incoming viewing key (detects and decrypts incoming notes), full viewing key, and outgoing viewing key (lets a sender recover what they paid).
* **Identity shielded account**: the shielded account a wallet derives for one of its identities ([Identity Shielded Accounts](#identity-shielded-accounts)). All shielded addresses this DIP publishes or exchanges come from it.
* **DIP-15 shared key**: the 32-byte AES key that [DIP-15](dip-0015.md) derives by ECDH between the sender key and recipient key of a contact request, used for its `encryptedPublicKey` field.

## Specification

### Overview

An identity can receive shielded payments at two kinds of address:

1. A **profile shielded address**, published in its DashPay profile document. Anyone can pay it without any prior interaction.
2. **Per-contact shielded addresses**, one for each contact request the identity sends, delivered encrypted inside that contact request. Only that contact can read the address.

A wallet takes both kinds from the same identity shielded account, so it detects payments to all of them with one viewing key and the pool's native trial decryption. The one exception is a profile address the wallet does not own ([Profile Shielded Address](#profile-shielded-address)). No additional discovery mechanism, publication, or ordering rule is required: the encrypted note carried by a payment is its own notification.

### Identity Shielded Accounts

Every shielded address of its own that a wallet publishes or exchanges under this DIP belongs to the **identity shielded account** of the identity that publishes it. For an identity with [DIP-13](dip-0013.md) identity index `identity_index`, the account is derived with ZIP-32 Orchard key derivation:

```text
m_Orchard / 32' / coin_type' / (0x40000000 + identity_index)'
```

* `coin_type'` MUST be `5'` on mainnet and `1'` on testnet, devnets, and regtest.
* `identity_index` MUST be less than `0x40000000`. Account indices from `0x40000000` to `0x7FFFFFFF` are reserved for identity shielded accounts; wallets MUST NOT use them for other purposes.
* Addresses are taken from the account's external scope. The diversifier index space of the account is partitioned as follows:

| Diversifier index `j` | Use |
| --------------------- | --- |
| `0` | The first profile `shieldedAddress` an identity publishes |
| `1` to `2^87 - 1` | Later profile addresses (rotations) and every other address the wallet uses for itself; never given to a contact |
| `2^87` to `2^88 - 1` | Per-contact addresses, derived only as specified in [Per-Contact Diversifier Index](#per-contact-diversifier-index) |

* A wallet that picks an index for its own use, whether in sequence or at random, MUST pick one from `1` to `2^87 - 1`. A wallet that draws an index at random MUST discard a draw of `0` and a draw of `2^87` or above, and draw again.
* Wallets MUST NOT publish or hand out, for any purpose defined in this DIP, a shielded address of any other account they hold. Index `0` of a wallet's ordinary accounts receives change, and any address of an ordinary account is one the user may give out elsewhere, so publishing it would tie those uses to the identity. The only address from outside the identity shielded account that a wallet may publish is a profile address it does not own ([Profile Shielded Address](#profile-shielded-address)).
* Wallets MUST scan the identity shielded account of every identity they manage, and on restore from seed MUST derive and scan the identity shielded account of every identity they discover. Funds received there belong to that identity. Wallets SHOULD show them under that identity and count them in the wallet's total. Wallets SHOULD spend them for the payments the user makes as that identity, and MUST NOT combine them with the funds of another account, or move them to one, unless the user chooses to.
* An identity without a DIP-13 identity index (for example, one whose keys were imported rather than derived) has no identity shielded account. Wallets MUST NOT include `encryptedShieldedAddress` in its contact requests, and the only profile address they may publish for it is one the wallet does not own.

### Profile Shielded Address

The DashPay data contract's `profile` document type has an OPTIONAL field:

```json
"shieldedAddress": {
  "type": "array",
  "byteArray": true,
  "minItems": 43,
  "maxItems": 43,
  "position": 7,
  "description": "Raw Orchard receiving address: 11-byte diversifier followed by 32-byte diversified transmission key. Clients validate before payment; wallets should use a dedicated tip account."
}
```

The "dedicated tip account" the contract's description refers to is the identity shielded account.

Normative requirements:

* The value is the raw 43-byte shielded payment address (11-byte diversifier `d` followed by the 32-byte diversified transmission key `pk_d`), exactly as used by shielded pool outputs. Clients MUST validate that the bytes decode to a valid shielded payment address before paying and MUST treat an undecodable value as no address rather than as an error in the profile.
* A wallet publishes one of two kinds of address:
  * **An address of the identity shielded account.** The first one an identity publishes MUST be the address at diversifier index `0`. An address that replaces it (a rotation) MUST be the address at an index from `1` to `2^87 - 1` of the same account that the identity has not published before. Such an address therefore always has an index below `2^87`.
  * **An address the wallet does not own**, supplied by the user: one from another wallet or a hardware wallet, for example. Before publishing it, the wallet MUST check that it is not an address of any account the wallet holds, and SHOULD tell the user that this wallet neither detects nor can spend or recover payments to it. Those belong to whoever holds its keys.
* A profile address MUST NOT be handed out as a per-contact address, so that attribution by diversifier ([Client Behavior](#client-behavior)) stays meaningful.
* Owners MAY rotate the published address at any time by updating the profile document; because shielded addresses never appear on chain, rotation is hygiene rather than necessity, and old addresses remain spendable-to and detected by the same viewing key.
* Publishing is OPTIONAL. An identity that does not publish a profile shielded address still receives private payments from its contacts through per-contact addresses.

### Per-Contact Shielded Addresses

The `contactRequest` document type gains one OPTIONAL field. Contact requests are immutable; the field is set at creation:

```json
"encryptedShieldedAddress": {
  "type": "array",
  "byteArray": true,
  "minItems": 64,
  "maxItems": 80,
  "encryptedFor": {
    "recipient": "toUserId",
    "recipientKey": "recipientKeyIndex",
    "senderKey": "senderKeyIndex",
    "scheme": "ecdh-secp256k1-aes256-cbc"
  },
  "position": 7,
  "description": "Sender's per-contact shielded payment address (43 bytes), encrypted to the contact with the DIP-15 shared key"
}
```

The `encryptedFor` declaration is the one `encryptedPublicKey` carries. It makes consensus accept only ciphertext lengths that are a multiple of 16 bytes, so with the size bounds above only 64-byte and 80-byte values are valid.

Normative requirements:

* **Plaintext.** The plaintext is the sender's 43-byte raw shielded payment address at the per-contact diversifier index defined in [Per-Contact Diversifier Index](#per-contact-diversifier-index), taken from the sender identity's identity shielded account.
* **Encoding.** The value is a random 16-byte IV followed by the AES-256-CBC encryption, with PKCS#7 padding, of the 43-byte plaintext under the DIP-15 shared key of this contact request (the same key that encrypts its `encryptedPublicKey`), for 16 + 48 = 64 bytes. Each field of a contact request MUST use its own random IV. Writers MUST write 64-byte values. 80-byte values are reserved for a future encoding; readers MUST ignore a value whose length or content they cannot decode.
* **Activation.** Writers MUST include the field only when the DashPay contract on the connected chain defines it. On a chain whose contract predates the field, a contact request carrying it is invalid as a whole.
* **Consistency.** A wallet that supports this DIP SHOULD include the field on every contact request it creates. If it cannot derive the address at that moment, it SHOULD retry or defer the request rather than send it without the field, because the field's presence on some requests and absence on others is observable per contact.
* **Acceptance.** A reader MUST use a decrypted value only if all of the following hold: the same DIP-15 shared key decrypts the request's `encryptedPublicKey` to a well-formed extended public key; the decrypted plaintext is exactly 43 bytes (so the padding is exactly five `0x05` bytes); it decodes as a valid shielded payment address; it is not an address of any account of the reader's own wallet; and it differs from the sender's current profile `shieldedAddress`. CBC provides no authentication, so these checks are what reject a value decrypted under the wrong key.
* **Account reference.** Writers MUST use an `accountReference` from `0` to `4294967295`, as constructed by DIP-15. Readers MUST ignore `encryptedShieldedAddress` on a request whose `accountReference` is outside that range.
* **Selection.** A reader groups a sender's contact requests by the extended public key each decrypts to; DIP-15 uses one extended public key for each account of the sender. Within a group, requests are ordered by their DIP-15 version (bits 28–31 of `accountReference`), then by `$createdAt`, then by document id compared as a 32-byte big-endian number; the greatest is the newest. Creation times, which the sender supplies, therefore decide only between requests of equal version. The reader uses the accepted address of the newest request in the group that carries one: a request without the field (for example, one sent by an older client) is passed over and does not remove an address accepted from an older request. When a sender has several groups, the reader uses the group of the account it pays to under DIP-15.
* **Change warning.** Readers SHOULD remember the first address accepted for each contact and SHOULD warn the user before the first payment after it changes, with the same weight as a change of the contact's DIP-15 extended public key.
* The recipient of the contact request uses this address for shielded payments to the sender, in preference to the sender's public profile `shieldedAddress`.

Per-contact diversified addresses provide attribution for free: an incoming note to one of them is attributed, without any memo, to the contact that address was given to, while remaining unlinkable, on chain and to third parties, to the profile address and to every other contact's address. This attribution is not proof of the payer: anyone who learns the address can pay it ([Security Considerations](#security-considerations)).

### Per-Contact Diversifier Index

The per-contact diversifier index is a pseudorandom function of the contact request's unique key, keyed by the sender's full viewing key:

```text
K = HMAC-SHA256(key = "DashPay/shielded/contact-index-key/v1",
                msg = FVK)
t = HMAC-SHA256(key = K,
                msg = "DashPay/shielded/contact-index/v1" || ownerId || toUserId || accountReference)
j = t[0..11], with t[10] |= 0x80
```

where:

* `FVK` is the 96-byte raw encoding of the full viewing key of the sender identity's identity shielded account (`ak || nk || rivk`, Zcash Protocol Specification section 5.6.4.4). `K` is HKDF-Extract with the label as salt and the FVK as input keying material.
* The labels are ASCII strings with no terminator.
* `ownerId` is the 32-byte identifier of the sending identity, `toUserId` the 32-byte identifier of the recipient identity, and `accountReference` the contact request's `accountReference` exactly as published in the document, encoded as an unsigned 64-bit little-endian integer (the 32-bit value followed by four zero bytes).
* `j` is the first 11 bytes of `t`, read as a little-endian 88-bit diversifier index, with bit 87 set. It therefore always lies in the per-contact range `2^87` to `2^88 - 1`.

The address is the external-scope address at diversifier index `j` of the identity shielded account.

Normative requirements:

* Wallets MUST derive per-contact indices only with this function. They MUST NOT allocate per-contact indices from a counter or from any other per-device or per-installation state.
* Wallets MUST compute `j` from the `accountReference` value published in the contact request, never from a locally recomputed value.
* Before sending a contact request, a wallet MUST check the derived index against the indices it has already issued to other recipients. If it matches one issued to a different `toUserId`, the wallet MUST NOT send the request; it SHOULD increment the DIP-15 version and derive again. (With 87 free bits of HMAC output, the probability of any collision among `n` requests from one identity is about `n^2 / 2^88`, roughly `3 * 10^-19` for `n = 10^4`.)

Consequences, all of which follow from the function and need no further rule:

* **Never the same address for two contacts.** `toUserId` is an input, and distinct indices give distinct addresses.
* **One address per contact request.** The inputs are the document's unique index `($ownerId, toUserId, accountReference)`.
* **Multi-device safety.** Every device holding the same seed derives the same address for the same contact request. Two devices creating the same request with the same `accountReference` derive the same address, and the platform accepts only one of the two requests.
* **Stateless restore.** Given the seed, a wallet recomputes every index it has issued from its own sent contact requests, all of whose inputs are public fields, with no signer and no decryption.
* **Delegation boundary.** A holder of only the IVK of the account can recover `j` from an address but cannot compute `K`, so it cannot tell which contact an index belongs to. A holder of the FVK can.

The function depends only on the three inputs, not on the document that carries the address. Another carrier that fixes the same three values for a request can use it unchanged.

### Rotation and Existing Contacts

**Rotation.** A wallet gives a contact a new per-contact address by sending a new contact request with the [DIP-15](dip-0015.md) version incremented and the same extended public key. The new `accountReference` yields a new index and a new address. DIP-15's four version bits allow 15 rotations per DashPay account.

* A reader receiving a contact request from a known sender whose decrypted extended public key is unchanged SHOULD treat it as an update of the shielded address only: no new acceptance prompt and no rebuild of the transparent payment account for that contact.
* Previous per-contact addresses cannot be revoked and keep receiving. Wallets SHOULD continue to attribute receipts on them to the contact, marked as an earlier address.

**Contacts established before a wallet supported this DIP.** Their contact requests are immutable and lack the field.

* Wallets MUST NOT send a new contact request automatically in response to receiving a payment. Doing so would publicly timestamp the payment, and would let whoever sends a payment make the wallet spend fees.
* Wallets MAY offer the user a way to give such a contact a per-contact address by rotation. They SHOULD show the fee, SHOULD do so only when the contact shows support for this DIP (a contact request from them carries the field, or their profile carries `shieldedAddress`), and SHOULD send after a random delay.
* Until then, such a contact can pay only the profile shielded address, and the payment arrives without attribution.

### Shielded Memo Kinds

Shielded pool note memos are 36 bytes: a little-endian `u32` kind tag followed by a 32-byte payload. Kinds `0` (empty) and `1` (UTF-8 text) are already established; unknown kinds round-trip untouched. This DIP registers one kind:

| Kind | Name | Payload | Semantics |
| ---- | ---- | ------- | --------- |
| `2` | `PaymentRef` | Reference (32 bytes) | "This payment is for X." A reference that the payee chose and gave to the payer, such as an invoice or order number. It names what is being paid, never who is paying. |

`PaymentRef` carries a reference that the payee issued for a payment it expects, so that the payee can match the note to its own records. Normative requirements:

* **Issued by the payee.** A payer MUST send a `PaymentRef` only when the payee supplied the reference for this payment, and MUST copy it unchanged. How the payee gives the reference to the payer (for example, in a payment request) is outside the scope of this DIP.
* **Encoding.** The payload is the reference, padded on the right with `0x00` bytes to 32 bytes. A payee whose own identifier is longer than 32 bytes issues a 32-byte hash of it instead. The payee compares all 32 bytes of the payload, so two references are distinct only if their padded payloads differ: references that differ only in trailing `0x00` bytes are one reference, and a payee MUST NOT issue more than one of them for payments it needs to tell apart. A payload of 32 zero bytes is not a reference, and clients MUST ignore it. Clients MAY show a payload as text when it is valid UTF-8 once its trailing `0x00` bytes are removed, and SHOULD show it in hexadecimal otherwise.
* **Not the payer.** A reference does not identify or authenticate the payer: everyone who has seen it can attach it to a payment. Clients MUST NOT show or treat a `PaymentRef` as evidence of who paid. The only indication of who paid is the address the note arrived on. It shows which contact that address was given to, and is not proof of the payer.
* **Amount.** A reference says nothing about the amount. A payee MUST compare the amount it received under a reference with the amount it requested, and decides for itself how to treat a short, excess, or repeated payment.
* **One per request.** A payee SHOULD issue a different reference for each payment it needs to tell apart. Because a memo is readable by whoever holds the viewing keys of either party, a payee SHOULD choose references that mean nothing without its own records: a random value or a sequence number rather than a name.
* **One memo per note.** A note carries one memo, so a note with a `PaymentRef` carries no text memo. A contact that holds a per-contact address pays that address, which attributes the payment to that contact, and adds the `PaymentRef`.

No memo kind in this DIP names the payer. A payment to a profile address is anonymous to the payee, whoever sends it; a payer who wants a payment attributed to it needs a per-contact address from the payee.

### Client Behavior

* **Detection** is the pool's native mechanism: clients trial-decrypt note ciphertexts with the IVK of each identity shielded account they manage. One IVK covers *all* diversified addresses of its account (the profile address and every per-contact address), so publishing or minting more addresses adds no scanning cost. The cost grows with the number of accounts scanned, not with the number of addresses.
* **Attribution** is by the diversifier index of the address a note arrived on, recovered from the note's recipient address with the account's IVK:

| Index `j` | Attribution |
| --------- | ----------- |
| `0` | The first profile address (or change; the OVK tells the wallet's own change apart). Anonymous. |
| `1` to `2^87 - 1` | A later profile address, attributed like index `0`, or another address the wallet uses for itself |
| `2^87` and above, matching a sent contact request | That contact; shown as received via the address given to that contact, and marked as an earlier address if the request has been superseded |
| `2^87` and above, matching none | Unattributed until the wallet's contact data is synchronized |

* **Paying a contact.** Clients SHOULD use, in order: the contact's per-contact address; the contact's profile shielded address, after telling the user that the contact will not see who paid; and only on the user's explicit choice, the transparent DIP-15 payment chain. Clients MUST NOT silently fall back from a shielded payment to one that reveals the payer or the amount; paying from transparent funds directly into the shielded pool to the contact reveals both the payer and the amount, and requires explicit confirmation. Shielding funds to oneself and paying later is preferable to both.
* **Paying a profile.** Given a profile that carries `shieldedAddress`, clients SHOULD offer it as the private way to pay that identity.
* **Paying against a reference.** When the payee supplied a reference with its payment details, clients SHOULD carry it in a `PaymentRef` memo, on whichever address the payment uses. On receipt, clients SHOULD show the reference with the payment, so that the user or the application that issued it can match the two. A `PaymentRef` never changes the attribution given by the table above.
* **Exiting to transparent funds**: a recipient who wants Core-chain or Platform-address funds unshields to themselves at a time and amount of their own choosing. Non-normative hygiene: unshield to fresh addresses, avoid amount-identical shield-then-unshield sequences close in time, and prefer round or denomination-friendly amounts.
* **Watch-only delegation**: the pool's viewing keys provide detection-without-spend delegation; nothing in this DIP adds a delegation mechanism or requires one. An IVK-only delegate sees amounts and memos of incoming notes but cannot map per-contact indices to contacts; an FVK delegate can, and also sees every outgoing payment.
* **Restore from seed**: the wallet derives the identity shielded account of every identity it discovers and rescans the pool. It rebuilds its map from per-contact indices to contacts by recomputing `j` for each contact request it has sent, including superseded ones. An index in the per-contact range that matches none of them was issued by an implementation that does not follow this DIP; the wallet MAY recover it by decrypting its own sent requests' `encryptedShieldedAddress` with the DIP-15 shared keys. Sender-side history comes from the OVK, which recovers each paid address; the wallet matches those against the addresses in every contact request it has received from each contact, including superseded ones.
* **Key disablement.** If an identity key referenced by a contact request's `senderKeyIndex` or `recipientKeyIndex` is disabled, its holder may have leaked it, and anyone holding it can learn the per-contact address and compute that request's shared key. Wallets SHOULD treat attribution through that address as unverified from then on, and SHOULD offer to rotate the address using different keys.

## Rationale

* **The shielded pool for private payments.** Shielded payments hide the amount as well as the parties, need no discovery artifact (the payment carries its own encrypted notification, so there is nothing to correlate by timing), and recover from seed plus chain alone.
* **Per-contact diversified addresses rather than memos for attribution.** Diversifier attribution costs nothing at scan time, works with empty memos (leaving the memo free for text), and cannot be spoofed by a third party who has not learned the address.
* **Carried in the contact request itself.** Orchard key derivation is hardened only, so there is no public key from which a contact could derive fresh addresses, as DIP-15 contacts do on the Core chain; the recipient must mint the address and send it. The contact request is created atomically with the relationship and is immutable, so updating the profile cannot change the address it carries. A compromised key that can create new contact requests can still issue a replacement ([Security Considerations](#security-considerations)).
* **Deterministic indices, not a counter.** A per-device counter lets two devices on one seed give the same index to two different contacts, and because contact requests are immutable the collision is permanent. Deriving the index from the contact request's own unique key gives the same answer on every device and after every restore, needs no stored state, and makes a version-bumped request a rotation automatically.
* **Keyed by the full viewing key.** The FVK is available wherever the wallet scans, including seedless background sync, so attribution never needs the seed or a signer; an IVK-only delegate still cannot attribute.
* **A partitioned index space.** Per-contact indices have bit 87 set, and every index a wallet picks for itself has it clear. One bit keeps the two apart, whether the wallet allocates its own indices from `1` upward or draws them at random, and a random index below `2^87` still has 87 bits of entropy, so two draws do not meet in practice.
* **One account per identity.** Separate hardened accounts keep a wallet's identities unlinkable even to someone holding one identity's viewing key, and one IVK per identity covers its profile address and all its contacts. Keeping these addresses out of a wallet's ordinary accounts also keeps the account that receives change from ever being published. Combining an identity's funds with another account's is left to the user for the same reason: it is the one thing a wallet could do that joins what the separate accounts keep apart.
* **A profile address the wallet does not own.** A user may want payments to a profile to reach another wallet, a hardware wallet for example, and nothing on chain could forbid it: a profile holds any 43 bytes. What a wallet must not publish is narrower: an address of its own ordinary accounts, which the user also gives out elsewhere.
* **64 to 80 bytes, not exactly 64.** A fixed-size byte array is stored without a length prefix and a ranged one with one, so the choice can never be changed for stored documents. The range allows a future 80-byte encoding (for example an authentication tag, or up to 20 more bytes of plaintext) without any contract change; older readers ignore values they cannot decode.
* **No memo that names the payer.** An identity id written into a memo is unauthenticated, since anyone can write any id. A tag that authenticates the payer to a contact can be built from the DIP-15 shared key, but it has to cover a value unique to its note, which a wallet can compute only after its bundle builder has paired the note's output with a spend, and it needs rules for shared keys whose identity keys have been disabled. Its main use would be payments between contacts whose requests predate this DIP, and a new contact request that carries the field already serves them.
* **`PaymentRef` names the payment, not the payer.** Who paid is indicated by the address a note arrives on, as an attribution and not a proof. What a payment is for is a separate question. An address answers it only when the payee issues a separate address for each request, which it cannot do for its published profile address or for an address it has already given to a contact. A reference chosen by the payee lets it reconcile payments on any address, and needs no authentication: a payment that carries the reference and the requested amount settles the request, whoever sent it.
* **Version before creation time.** A contact request's creation time is supplied by its sender, so two requests can carry equal times or times that disagree with their versions. Ordering by the DIP-15 version first makes every reader pick the same request after a rotation.

## Backwards Compatibility

* Both fields are optional additions; existing profiles and contact requests remain valid.
  * `profile.shieldedAddress` is part of version 2 of the DashPay contract (Platform protocol version 14). This DIP specifies which address wallets put there.
  * `contactRequest.encryptedShieldedAddress` is added in version 3 of the DashPay contract (Platform protocol version 15). The `encryptedFor` declaration relies on the `maximum` of `4294967295` on `senderKeyIndex` and `recipientKeyIndex` that version 3 already carries.
* Documents written under a newer contract version cannot be decoded by clients holding an earlier copy of the DashPay contract: the document format records every optional property, even an absent one, so an older reader finds bytes it does not expect and fails rather than ignoring them. Each document records the contract version it was written under, so such a reader can tell that it must fetch the newer contract. Clients MUST update their copy of the contract when each upgrade activates.
* Until a chain has activated the contract version that defines `encryptedShieldedAddress`, wallets MUST NOT include it ([Per-Contact Shielded Addresses](#per-contact-shielded-addresses)); identities on such a chain still receive shielded payments from contacts through the profile shielded address, without attribution.
* Memo kinds are a client-side registry over the pool's existing extensible memo format; unknown kinds already round-trip, so no protocol change is involved.
* DIP-15 contact-request flows are unchanged, except that a version-bumped request with an unchanged extended public key updates only the shielded address ([Rotation and Existing Contacts](#rotation-and-existing-contacts)). Older DIP-15 clients may ignore such a request or treat it as a new account for the same extended public key; either is harmless. Established contacts can continue using per-contact derived chains for transparent payments.
* Core chain consensus is unchanged.

## Security Considerations

* **Profile address hijacking.** A compromised identity key authorized to update the profile can replace the published shielded address. Profiles and contact requests both default to the HIGH signing requirement; a wallet may use separate keys bound to each document type, but this separation is not guaranteed. Clients SHOULD alert users when a contact's profile shielded address changes and pin previously seen values. Existing contact requests are immutable, so their addresses survive a compromise limited to profile updates.
* **Forged contact requests.** If the compromised key can also create contact requests, an attacker can issue a replacement using an existing identity key whose private key they control as `senderKeyIndex`, potentially the signing key itself. The contract does not require that key to have the encryption purpose. The attacker can encrypt a well-formed extended public key and address; if they know the original extended public key, they can copy it. A different extended public key is subject to DIP-15 account acceptance. Requiring an encryption-purpose key alone would not establish that a replacement address is legitimate; the change warning still applies.
* **Weak authentication of per-contact addresses.** Anyone who *learns* a per-contact address can pay it: the contact, anyone holding either identity key of the contact request's DIP-15 key pair, and anyone holding the sender's viewing keys once a note has arrived on it. Diversifier attribution therefore means "received on the address given to this contact", not proof of the payer. This DIP defines no authenticated alternative.
* **Address changes.** A new per-contact address from a contact looks the same whether the contact rotated it or someone controlling the contact's identity keys replaced it. The change warning in [Per-Contact Shielded Addresses](#per-contact-shielded-addresses) is the defense; clients SHOULD encourage out-of-band confirmation for large payments after a change.
* **`PaymentRef` is not authentication.** A reference is known to the payee, to everyone the payee gave it to, and, once a note carries it, to whoever holds the viewing keys of either party. Any of them can attach it to a payment. Clients MUST NOT treat it as identifying the payer. A payee that acts on a reference MUST check the amount received against its own record of the request; otherwise a small payment under someone else's reference passes for the payment of that request.
* **No consensus enforcement of uniqueness.** Consensus sees only ciphertext and cannot check that an address is unique per contact; the guarantee comes entirely from the index derivation in wallets.
* **Payer-provable payments.** A payer to any shielded address can later prove they made the payment (they know the note plaintext). This is inherent to any receiving address and usually desirable (receipts).

## Privacy Considerations

* **The contact graph stays public.** DIP-15 contact requests are public documents that name both identities. This DIP hides payments between contacts, not the fact that two identities are contacts.
* **What publishing a shielded address leaks**: only that the profile accepts shielded payments. Payments to it produce note ciphertexts that reveal nothing, and the address itself never appears on chain. Diversified-address unlinkability means the published address cannot be linked to any per-contact address derived from the same viewing key.
* **Public signals in contact requests.** The presence of `encryptedShieldedAddress` on a contact request is public, and so are the DIP-15 version bits of `accountReference` and the request's creation time. A rotation or a later backfill therefore reveals which pair of identities it concerns, when it happened, and how many rotations have occurred. The [Consistency](#per-contact-shielded-addresses) rule and the prohibition on automatic re-sends keep these signals from revealing more.
* **Viewing-key holders.** Whoever holds an account's viewing keys sees the amounts and memos of its incoming notes and, with the FVK, every outgoing payment and the per-contact attribution. Treat an FVK as a full view of the identity's shielded activity.
* **Network-level correlation.** A node serving a wallet sees its queries. Querying a payee's profile or contact requests immediately before broadcasting a shielded payment lets that node link payer and payee. Non-normative: pay from already-synchronized state, and broadcast after a short random delay.
* **Payer-side linkage on entry.** Shielding transparent funds is a visible event. Payers who shield and immediately pay amount-identical values create a correlation between their shielding and the recipient's later unshielding; the hygiene guidance in [Client Behavior](#client-behavior) applies to both sides.
* **The anonymity set is pool activity.** The privacy of shielded payments is proportional to overall pool usage. Platform's minimum pool note count for transfers out of the pool is a bootstrap safeguard, not a measure of anonymity.
* **Quantum adversaries.** The privacy properties in this DIP hold against classical adversaries only. A published shielded address yields its account's IVK to an adversary able to compute discrete logarithms, and per-contact addresses are protected by secp256k1 ECDH in documents that can never be deleted; both can be recorded today and broken later. Owners who do not want a permanent published receiver can omit the profile shielded address. Post-quantum protection is out of scope.

## Test Vectors

Full vectors, and the program that generates them against the Orchard implementation Dash Platform uses, are in [test-vectors.md](dip-quantumexplorer-dashpay-shielded-addresses/test-vectors.md). A summary, for the mnemonic `abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about` with an empty passphrase, mainnet (`coin_type` `5'`), `identity_index` `0` (account `0x40000000`), `ownerId` = 32 bytes of `0x11`:

| Contact request | `toUserId` | `accountReference` | `j` (11 bytes, little-endian) |
| --------------- | ---------- | ------------------ | ----------------------------- |
| Bob, version 0 | 32 bytes of `0x22` | `0x01234567` | `f90d5349d8530cf76835d0` |
| Carol, version 0 | 32 bytes of `0x33` | `0x01234567` | `a5ca8646a33e3db572ca94` |
| Bob, version 1 | 32 bytes of `0x22` | `0x11234567` | `4d2ff123168ee0a07ff5b2` |

## Future Extensions

* **Anonymous contact requests.** Contact requests that hide the relationship itself are specified in a separate DIP. They carry the sender's per-contact shielded address inside the encrypted request, and derive it with the function in [Per-Contact Diversifier Index](#per-contact-diversifier-index).
* **Authenticated payer memo.** A memo kind that proves to a contact which contact paid, keyed by the DIP-15 shared key and bound to the note that carries it. It would turn attribution into proof, and would cover payments to a profile address.
* **A second encoding of `encryptedShieldedAddress`.** The 80-byte length is reserved for a future encoding within the same field, requiring no contract change.
* **Post-quantum address exchange.** Protecting per-contact addresses against quantum adversaries would need a post-quantum key encapsulation, whose ciphertexts (over a kilobyte) do not fit this field; it would be a new field or document type.

## Copyright

Copyright (c) 2026 Dash Core Group, Inc. [Licensed under the MIT License](https://opensource.org/licenses/MIT)
