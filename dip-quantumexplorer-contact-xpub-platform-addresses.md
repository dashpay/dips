<pre>
  DIP: TBD
  Title: Transparent Platform Contact Payments via DashPay Relationship Xpubs
  Author(s): Quantum Explorer
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2026-04-27
  License: MIT License
  Requires: 0014, 0015, 0018
</pre>

# Table of Contents

* [Abstract](#abstract)
* [Motivation](#motivation)
* [Prior Work](#prior-work)
* [Specification](#specification)
  * [Overview](#overview)
  * [Relationship Xpub Reuse](#relationship-xpub-reuse)
  * [Terminal Child Index Partition](#terminal-child-index-partition)
  * [Transparent Platform Address Derivation](#transparent-platform-address-derivation)
  * [Sending and Receiving Behavior](#sending-and-receiving-behavior)
  * [Excluded Scope](#excluded-scope)
* [Rationale](#rationale)
* [Backwards Compatibility](#backwards-compatibility)
* [Reference Implementation](#reference-implementation)
* [Security Considerations](#security-considerations)
* [Privacy Considerations](#privacy-considerations)
* [Copyright](#copyright)

## Abstract

This DIP specifies how DashPay contacts can exchange transparent Platform payment addresses without
introducing a second extended public key into the DashPay contact request document. It reuses the
existing DashPay relationship xpub exchanged by [DIP-15](dip-0015.md) and reserves a distinct
terminal child-index subspace for transparent Platform payments.

DashPay Core contact payments continue to derive child keys as `contact_xpub / i`.

Transparent Platform contact payments derive child keys as `contact_xpub / (2^30 + i)`.

This preserves the existing contact request payload, avoids a DashPay contract change for the
transparent phase, and keeps contact payment derivation relationship-specific. Shielded Platform
payments are out of scope.

## Motivation

[DIP-15](dip-0015.md) already defines a contact-specific relationship xpub that is exchanged
between contacts and used for DashPay payment address derivation. A straightforward way to add
transparent Platform contact payments would be to extend the DashPay contract so that every new
contact request carries a second encrypted xpub dedicated to Platform addresses.

That approach introduces unnecessary complexity:

* it changes the DashPay system contract even though the existing relationship xpub already
  provides a deterministic per-contact public key stream;
* it requires SDK, wallet, FFI, and contract-version changes for a use case that can be expressed
  by derivation rules alone; and
* it encourages implementations to share wallet-global Platform payment xpubs, which weakens the
  relationship-specific privacy boundary that DashPay already creates.

Transparent Platform contact payments only require a per-contact public key stream that both sides
can derive. The DashPay relationship xpub already satisfies that requirement. The missing piece is
an unambiguous rule for separating Platform-derived child keys from existing DashPay Core payment
child keys.

## Prior Work

* [DIP-0009: Feature Derivation Paths](https://github.com/dashpay/dips/blob/master/dip-0009.md)
* [DIP-0013: Identities in Hierarchical Deterministic Wallets](https://github.com/dashpay/dips/blob/master/dip-0013.md)
* [DIP-0014: Extended Key Derivation using 256-Bit Unsigned Integers](https://github.com/dashpay/dips/blob/master/dip-0014.md)
* [DIP-0015: DashPay](https://github.com/dashpay/dips/blob/master/dip-0015.md)
* [DIP-0017: Dash Platform Payment Addresses and HD Derivation](https://github.com/dashpay/dips/blob/master/dip-0017.md)
* [DIP-0018: Dash Platform Payment Address Encodings](https://github.com/dashpay/dips/blob/master/dip-0018.md)
* [BIP-0032: Hierarchical Deterministic Wallets](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki)

## Specification

### Overview

This DIP extends the use of the [DIP-15](dip-0015.md) contact relationship xpub so that it can be
used for two transparent payment systems between the same contact pair:

* DashPay Core-chain payments
* transparent Platform payments

The contact request document format remains unchanged. Implementations derive different child keys
for the two systems by partitioning the unhardened terminal child-index space.

### Relationship Xpub Reuse

The relationship xpub exchanged in a DashPay contact request MUST remain the xpub derived at:

```text
m / 9' / coin_type' / 15' / account' / sender_id / recipient_id
```

Implementations MUST continue to exchange exactly one encrypted extended public key for the
transparent phase.

Implementations MUST interpret that xpub as the parent for both:

* DashPay Core contact payment address derivation
* transparent Platform contact payment address derivation

This DIP does not introduce a second encrypted extended public key into the `contactRequest`
document.

### Terminal Child Index Partition

The unhardened terminal child-index space of the contact relationship xpub MUST be partitioned as
follows:

* DashPay Core payment child indexes: `0 <= i < 2^30`
* transparent Platform payment child indexes: `2^30 <= i < 2^31`

Define:

```text
PLATFORM_CONTACT_INDEX_BASE = 2^30
```

For a logical transparent Platform payment index `p`, implementations MUST derive the actual child
index as:

```text
terminal_index = PLATFORM_CONTACT_INDEX_BASE + p
```

where `0 <= p < 2^30`.

After adopting this DIP, implementations MUST NOT derive new DashPay Core payment addresses at
terminal child indexes greater than or equal to `2^30`.

### Transparent Platform Address Derivation

Given:

* a contact relationship xpub `C`;
* a logical transparent Platform payment index `p`; and
* a terminal child index `n = 2^30 + p`;

the transparent Platform child public key is:

```text
K = CKDpub(C, n)
```

The corresponding transparent Platform payment address MUST be encoded from `K` using the
transparent Platform address rules defined by [DIP-0018](dip-0018.md).

For the first phase covered by this DIP:

* implementations SHOULD use transparent P2PKH Platform addresses; and
* implementations MUST NOT assume that shielded Platform recipient material can be derived from the
  same xpub.

This DIP does not modify the [DIP-0017](dip-0017.md) derivation used for wallet-owned Platform
payment accounts.

### Sending and Receiving Behavior

When sending transparent Platform funds to a contact, the sender:

1. obtains the contact relationship xpub from the accepted DashPay relationship;
2. selects the next logical transparent Platform payment index `p` for that contact;
3. derives `contact_xpub / (2^30 + p)`;
4. encodes that child key as a transparent Platform address; and
5. sends funds to that address.

The sender SHOULD persist the logical transparent Platform payment index used for each contact.

The recipient derives the corresponding private key from the same relationship path and the same
terminal child index.

Implementations MAY manage transparent Platform contact addresses with a contact-specific index and
watch strategy rather than by inserting them into the wallet-owned [DIP-0017](dip-0017.md)
Platform Payment account pool. For example, implementations MAY maintain:

* a sparse per-contact watched set;
* a per-contact next-expected transparent Platform payment index; or
* a bounded per-contact scan window in the reserved transparent Platform subspace.

The exact monitoring and recovery strategy is implementation-defined.

### Excluded Scope

This DIP does not require:

* a new DashPay contract version;
* a new required field in `contactRequest`;
* a second encrypted xpub in the SDK or FFI surface;
* a protocol-version bump solely for the transparent phase; or
* any shielded / Orchard contact payment derivation rule.

Shielded Platform payments MUST be specified by a separate DIP.

## Rationale

The existing [DIP-15](dip-0015.md) relationship xpub is already encrypted, shared per contact, and
capable of unhardened child public derivation. Adding a second xpub would duplicate information
that can already be represented through child-index allocation.

Reserving the upper half of the normal BIP-32 child-index space has several benefits:

* it creates a large disjoint subspace without changing the meaning of the already-shared contact
  xpub;
* it avoids collisions with existing low-index DashPay Core payment addresses;
* it preserves monotonic logical counters for both payment systems; and
* it does not require the wallet to treat contact-derived Platform payments as [DIP-0017](dip-0017.md)
  wallet-owned Platform Payment accounts.

An alternative would be to derive two explicit branches below the contact xpub, such as `/0/i` for
DashPay Core and `/1/i` for Platform. That approach is cleaner in a new derivation design, but it
changes the meaning of the terminal derivation structure that existing implementations already use.
The `2^30` split preserves current behavior while still creating a deterministic partition.

Sharing a wallet-global [DIP-0017](dip-0017.md) xpub with every contact was rejected because it
turns per-contact payments into one globally linkable address family. Reusing the relationship xpub
preserves the existing DashPay privacy boundary: each contact pair still has its own derivation
root.

## Backwards Compatibility

This DIP is backward compatible with existing DashPay contact requests because it does not alter the
contact request document format or encrypted payload layout.

Wallets that do not implement this DIP will continue to function for DashPay Core payments. They
simply will not derive or monitor the reserved transparent Platform subspace.

Because deployed DashPay contact payment implementations derive terminal child indexes starting at
`0` and increment upward, reserving `2^30` for transparent Platform use does not conflict with any
practical existing address allocation.

## Reference Implementation

The following pseudo-code is normative for transparent Platform contact payment address derivation:

```text
function platform_contact_payment_key(contact_xpub, logical_platform_index):
    PLATFORM_CONTACT_INDEX_BASE = 2^30

    if logical_platform_index < 0 or logical_platform_index >= 2^30:
        fail("logical_platform_index out of range")

    terminal_index = PLATFORM_CONTACT_INDEX_BASE + logical_platform_index
    child_pubkey = bip32_ckdpub(contact_xpub, terminal_index)

    return child_pubkey
```

Address encoding of `child_pubkey` into a transparent Platform address is defined by
[DIP-0018](dip-0018.md).

## Security Considerations

* Implementations MUST ensure that both parties apply the same child-index partition rule. If the
  sender and recipient disagree on the reserved Platform subspace, funds may be sent to addresses
  the recipient will never derive.
* Reusing the relationship xpub does not expose more public key material than the existing DashPay
  contact request already exposes, but it does extend the set of child public keys that may be
  derived from that xpub.
* Wallets MUST reject any attempt to interpret transparent Platform contact addresses as Core-chain
  receive addresses.
* Wallets MUST keep DashPay Core payment address allocation out of the reserved transparent Platform
  subspace after activating this DIP.

## Privacy Considerations

* This DIP is more private than sharing a wallet-global [DIP-0017](dip-0017.md) xpub with every
  contact because each relationship retains a distinct derivation root.
* DashPay Core and transparent Platform contact payments derived from the same relationship xpub are
  still linkable at the relationship level by the participants. This DIP preserves the per-contact
  boundary; it does not make the two payment systems unlinkable to each other.
* Wallets SHOULD avoid revealing logical transparent Platform payment indexes outside of the local
  wallet unless required for recovery or coordination.

## Copyright

Copyright (c) 2026 Dash Core Group, Inc. [Licensed under the MIT License](https://opensource.org/licenses/MIT)
