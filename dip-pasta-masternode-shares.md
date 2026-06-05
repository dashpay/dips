<pre>
  DIP: pasta-masternode-shares
  Title: Masternode Reward Shares
  Author(s): Pasta
  Special-Thanks:
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2026-06-05
  License: MIT License
</pre>

## Table of Contents

1.  [Abstract](#abstract)
2.  [Motivation](#motivation)
3.  [Prior Work](#prior-work)
4.  [Specification](#specification)
    1.  [Terminology](#terminology)
    2.  [Provider Transaction Version](#provider-transaction-version)
    3.  [Masternode Payout Share](#masternode-payout-share)
    4.  [Registering a Masternode](#registering-a-masternode)
    5.  [Updating Masternode Payout Shares](#updating-masternode-payout-shares)
    6.  [Masternode List State](#masternode-list-state)
    7.  [Masternode Reward Payments](#masternode-reward-payments)
    8.  [Validation Rules](#validation-rules)
    9.  [RPC and JSON Interfaces](#rpc-and-json-interfaces)
    10. [Special Transaction Filtering](#special-transaction-filtering)
5.  [Deployment and Compatibility](#deployment-and-compatibility)
6.  [Rationale](#rationale)
7.  [Test Cases](#test-cases)
8.  [Security Considerations](#security-considerations)
9.  [Copyright](#copyright)

## Abstract

This DIP extends [DIP-0003: Deterministic Masternode Lists](dip-0003.md) by
allowing the owner-controlled portion of a masternode reward to be split across
multiple payout scripts. A masternode may specify between 1 and 8 distinct owner
payout entries, each with a basis-point reward share. A masternode with one
owner uses the same structure as a masternode with multiple owners: one payout
entry with a reward value of 10000.

The existing operator reward mechanism is preserved. If a non-zero operator
reward was configured and an operator payout script is set, the operator reward
is subtracted from the masternode reward first. The remaining owner reward is
then split across the configured owner payout entries.

## Motivation

Dash masternodes currently support at most two automatic reward recipients: the
owner payout address and the operator payout address. This is useful when an
owner delegates operation to a hosting provider, but it does not support direct,
protocol-enforced reward distribution among multiple masternode share owners.

Without protocol support, shared masternode ownership requires an off-chain
agreement. One participant receives the masternode reward and then distributes
funds manually or through an external service. This introduces custodial risk,
operational delay, accounting complexity, and disputes when the receiving party
fails to distribute payments correctly.

This DIP allows the blockchain itself to enforce automatic reward distribution
for the owner-controlled portion of masternode rewards. The registrar owner key
continues to control masternode registration metadata, including the payout
split, so this proposal provides protocol-enforced automatic payouts while
preserving the existing owner-update model from DIP-0003.

## Prior Work

* [DIP-0002: Special Transactions](dip-0002.md)
* [DIP-0003: Deterministic Masternode Lists](dip-0003.md)
* [DIP-0004: Simplified Verification of Deterministic Masternode Lists](dip-0004.md)

## Specification

### Terminology

This DIP uses the following terms:

| Term | Definition |
| --- | --- |
| Owner reward | The masternode reward amount remaining after subtracting any operator reward. |
| Payout entry | One owner payout script and its reward share. |
| Payout list | The ordered list of owner payout entries for a masternode. |
| Reward share | A `uint16_t` basis-point value. A value of 10000 represents 100 percent. |

### Provider Transaction Version

This DIP defines a new provider transaction payload version:

| Name | Value | Description |
| --- | --- | --- |
| `MultiPayout` | 4 | Provider transaction payload version with a unified owner payout list. |

Version 4 provider registration and registrar update transactions replace the
single `scriptPayout` field with a unified `payouts` field. The unified field is
used for all owner payout configurations, including the single-owner case.

Version 4 applies to the following special transactions:

| Transaction | Special transaction type | Version 4 change |
| --- | --- | --- |
| ProRegTx | 1 | Replaces `scriptPayout` with `payouts`. |
| ProUpRegTx | 3 | Replaces `scriptPayout` with `payouts`. |

This DIP does not change the existing ProUpServTx operator payout field. The
operator payout remains a separate operator-controlled service update field.

### Masternode Payout Share

Each owner payout entry has the following structure:

| Field | Type | Size | Description |
| --- | --- | --- | --- |
| reward | uint16_t | 2 | Basis-point share of the owner reward. |
| scriptPayoutSize | compactSize uint | 1-9 | Size of the payout script. |
| scriptPayout | Script | Variable | Owner payout script. |

The `reward` field is expressed in basis points. Implementations must interpret
10000 as 100 percent, 5000 as 50 percent, and 100 as 1 percent.

The payout list has the following structure:

| Field | Type | Size | Description |
| --- | --- | --- | --- |
| payoutsCount | uint8_t | 1 | Number of payout entries. Must be from 1 to 8. |
| payouts | MasternodePayoutShare[] | Variable | Ordered owner payout entries. |

The ordering of payout entries is consensus-significant for reward rounding.
The last payout entry receives the rounding remainder as specified in
[Masternode Reward Payments](#masternode-reward-payments).

### Registering a Masternode

For version 4 ProRegTx payloads, the ProRegTx structure defined in DIP-0003 is
modified by replacing `scriptPayout` with `payouts`.

| Field | Type | Size | Description |
| --- | --- | --- | --- |
| version | uint16_t | 2 | Provider transaction version number. Set to 4 for this DIP. |
| type | uint16_t | 2 | Masternode type. |
| mode | uint16_t | 2 | Masternode mode. |
| collateralOutpoint | COutpoint | 36 | The collateral outpoint. |
| netInfo | NetInfo | Variable | Masternode service addressing information. |
| KeyIdOwner | CKeyID | 20 | The public key hash used for owner-related signing. |
| PubKeyOperator | BLSPubKey | 48 | The public key used for operator-related signing. |
| KeyIdVoting | CKeyID | 20 | The public key hash used for voting. |
| operatorReward | uint16_t | 2 | Operator reward in basis points, from 0 to 10000. |
| payoutsCount | uint8_t | 1 | Number of owner payout entries. |
| payouts | MasternodePayoutShare[] | Variable | Owner payout entries. |
| inputsHash | uint256 | 32 | The SHA256 hash of all transaction input outpoints. |
| platformNodeID | uint160 | 20 | Node ID derived from the Platform P2P public key. Present only for Evo masternodes. |
| payloadSigSize | compactSize uint | 1-9 | Size of the signature. |
| payloadSig | unsigned char[] | Variable | Signature required for external collateral ownership proof. |

For a masternode with one owner, the payout list contains exactly one entry with
`reward = 10000`.

For version 4 Evo masternode registrations, Platform P2P and HTTPS addressing
data is encoded in `netInfo` using the extended-address provider transaction
format. Separate `platformP2PPort` and `platformHTTPPort` fields are not
serialized in version 4 payloads.

For external collaterals, the collateral ownership sign string must include the
new payout list representation instead of the previous single payout string. The
payout list string is produced by concatenating each payout entry in serialized
order as:

```text
<reward>:<payoutStr>
```

Entries are joined with commas. `<payoutStr>` is the Dash address corresponding
to the entry's `scriptPayout` when the script is a standard address script, or
the hex representation of the script otherwise. The ProRegTx sign string
therefore becomes:

```text
<payoutListStr>|<operatorReward>|<ownerKeyAddress>|<votingKeyAddress>|<payloadHash>
```

### Updating Masternode Payout Shares

For version 4 ProUpRegTx payloads, the ProUpRegTx structure defined in DIP-0003
is modified by replacing `scriptPayout` with `payouts`.

| Field | Type | Size | Description |
| --- | --- | --- | --- |
| version | uint16_t | 2 | Provider update registrar transaction version number. Set to 4 for this DIP. |
| proTXHash | uint256 | 32 | The hash of the initial ProRegTx. |
| mode | uint16_t | 2 | Masternode mode. |
| PubKeyOperator | BLSPubKey | 48 | The public key used for operator-related signing. |
| KeyIdVoting | CKeyID | 20 | The public key hash used for voting. |
| payoutsCount | uint8_t | 1 | Number of owner payout entries. |
| payouts | MasternodePayoutShare[] | Variable | Owner payout entries. |
| inputsHash | uint256 | 32 | The SHA256 hash of all transaction input outpoints. |
| payloadSigSize | compactSize uint | 1-9 | Size of the signature. |
| payloadSig | unsigned char[] | Variable | Signature of the ProUpRegTx fields, signed by the owner. |

The masternode owner may update the payout list through ProUpRegTx. A payout
list update does not revive a PoSe-banned masternode, matching existing
ProUpRegTx behavior.

### Masternode List State

Deterministic masternode state must store the owner payout list for version 4
masternodes. The previous single `scriptPayout` state field is replaced by the
unified `payouts` field for version 4 state.

State diffs must report payout-list changes as a single logical field. A
version 4 state diff that changes any payout entry, payout order, payout script,
or reward share must include the full replacement payout list.

For compatibility with pre-version-4 masternodes, implementations may internally
represent legacy `scriptPayout` as a one-entry payout list with `reward = 10000`.
This compatibility representation must not change the serialization of legacy
provider transaction payloads or legacy deterministic masternode state.

### Masternode Reward Payments

Masternode reward payment construction proceeds in the following order:

1.  Calculate the block's masternode reward using the existing rules.
2.  Apply any Platform credit pool reallocation using the existing rules.
3.  If the selected masternode has a non-zero `operatorReward` and a non-empty
    operator payout script, calculate:

```text
operatorAmount = floor(masternodeReward * operatorReward / 10000)
```

4.  Subtract `operatorAmount` from `masternodeReward`. The result is the owner
    reward.
5.  For each owner payout entry except the last, calculate:

```text
entryAmount = floor(ownerReward * reward / 10000)
```

6.  The last owner payout entry receives:

```text
ownerReward - sum(previous owner payout entry amounts)
```

7.  Create one coinbase output for each owner payout entry with a non-zero
    calculated amount.
8.  If `operatorAmount` is non-zero, create the operator payout output using
    the existing operator payout script.

The final owner payout entry receives the remainder to guarantee that the total
owner reward is paid exactly even when integer division truncates earlier
entries.

Coinbase validation must require every expected masternode payout output by
amount and script. As with the current masternode payment implementation, the
relative order of outputs in the coinbase transaction is not consensus
significant.

### Validation Rules

A version 4 payout list is invalid if any of the following conditions are true:

1.  `payoutsCount` is less than 1.
2.  `payoutsCount` is greater than 8.
3.  Any payout entry has `reward` less than 100.
4.  Any payout entry has `reward` greater than 10000.
5.  The sum of all `reward` fields is not exactly 10000.
6.  Any `scriptPayout` is not a P2PKH or P2SH script.
7.  The same payout script appears more than once in the payout list.
8.  A P2PKH payout destination equals the owner key ID.
9.  A P2PKH payout destination equals the voting key ID.
10. A P2PKH payout destination equals the collateral key ID when the collateral
    output destination can be extracted as a P2PKH destination.

The 100-basis-point minimum is a consensus anti-dust bound. It prevents
intentionally tiny micro-owner entries from creating nuisance coinbase outputs.
It is not a guarantee that every possible future block reward will remain above
policy dust thresholds forever as the block reward declines.

All existing ProRegTx and ProUpRegTx validation rules from DIP-0003 continue to
apply unless explicitly replaced by this DIP.

### RPC and JSON Interfaces

RPCs that create ProRegTx or ProUpRegTx transactions must accept a unified
`payouts` array for version 4 transactions. Each entry contains an address and
a basis-point reward:

```json
[
  {
    "address": "X...",
    "reward": 10000
  }
]
```

```json
[
  {
    "address": "X...",
    "reward": 7000
  },
  {
    "address": "X...",
    "reward": 3000
  }
]
```

JSON output for version 4 masternodes and provider transaction payloads must
expose owner payouts through a `payouts` array. This applies to at least:

* Raw transaction JSON for ProRegTx and ProUpRegTx.
* `protx info`.
* `protx diff`.
* `protx listdiff`.
* Extended Simplified Masternode List JSON.

The `payoutAddress` field is not part of the normative JSON shape for version 4
masternodes. A single-owner version 4 masternode still reports a one-entry
`payouts` array with `reward = 10000`.

RPCs that report required or actual masternode payments must expose every
generated masternode payout output. This applies to at least:

* `masternode winners`.
* `masternode payments`.
* `getblocktemplate`.

The existing operator payout reporting remains separate when an operator payout
output is generated.

### Special Transaction Filtering

Special transaction filters and bloom filters must include every script in a
version 4 payout list. A filter that matches any owner payout script in the list
must match the containing ProRegTx or ProUpRegTx in the same manner that a match
on the current single `scriptPayout` field does.

## Deployment and Compatibility

This DIP is intended to deploy with Dash Core's v24 network upgrade
(`DEPLOYMENT_V24`). Version 4 ProRegTx and ProUpRegTx payloads are only valid
after v24 activates.

Before v24 activation:

* Provider transaction versions greater than the current maximum valid version
  remain invalid.
* Legacy ProRegTx and ProUpRegTx payload serialization is unchanged.
* Legacy masternode reward payment behavior is unchanged.

After v24 activation:

* New version 4 registrations may use 1 to 8 owner payout entries.
* Version 4 registrar updates may change the payout list.
* Existing legacy masternodes remain valid and continue to use their existing
  single owner payout script.
* Existing operator reward behavior remains unchanged.

Implementations should treat legacy single-payout masternodes and version 4
one-entry payout-list masternodes as equivalent for reward payment purposes, but
must preserve their distinct serialized provider transaction payloads.

## Rationale

### Unified payout list

Using a payout list for both single-owner and multi-owner masternodes avoids a
special case where one payout is represented differently from several payouts.
This makes the new version's semantics clear: every owner reward recipient is a
payout entry.

### Maximum of 8 owner payout entries

A maximum of 8 owner payout entries provides enough room for common shared
masternode arrangements while limiting the number of additional coinbase
outputs, deterministic masternode state size, and Simplified Masternode List
metadata. Larger limits would support finer ownership fragmentation, but would
increase worst-case coinbase and state growth for every paid block involving a
highly fragmented masternode.

### Basis-point reward shares

Basis points match the existing `operatorReward` precision and allow the payout
list to reuse a familiar representation. Requiring the shares to sum to exactly
10000 avoids ambiguous normalization rules.

### Minimum reward share

The minimum owner payout share of 100 basis points prevents registrations that
would intentionally create very small recurring coinbase outputs. This limit
also follows from the maximum payout count: if all 8 entries are used, each
entry must represent a meaningful owner share.

### Operator reward remains separate

The operator reward serves a different role from owner payout shares. It is
configured by the owner as a maximum operator percentage, while the operator
sets the actual operator payout script through ProUpServTx. Keeping this
mechanism separate preserves hosting-provider delegation without making the
operator payout script part of the owner payout list.

## Test Cases

Implementations should include tests for the following cases:

1.  A version 4 ProRegTx with one payout entry and `reward = 10000` is valid.
2.  A version 4 ProRegTx with 8 distinct payout entries whose rewards sum to
    10000 is valid.
3.  A version 4 ProRegTx with 0 payout entries is invalid.
4.  A version 4 ProRegTx with 9 payout entries is invalid.
5.  A payout entry with `reward = 99` is invalid.
6.  A payout list whose rewards sum to 9999 or 10001 is invalid.
7.  A payout list containing duplicate scripts is invalid.
8.  A payout list containing a non-P2PKH and non-P2SH script is invalid.
9.  A payout script that reuses the owner, voting, or collateral key is invalid
    where the corresponding key comparison is possible.
10. A ProUpRegTx can replace the payout list without reviving a PoSe-banned
    masternode.
11. A masternode with an operator payout first subtracts the operator reward and
    then splits the owner reward across the payout list.
12. Integer rounding pays the remainder to the last owner payout entry.
13. Coinbase validation rejects a block missing any expected owner payout output.
14. Coinbase validation rejects a block paying an expected payout script the
    wrong amount.
15. `protx info`, `protx diff`, `protx listdiff`, raw transaction JSON, and
    extended SML JSON expose the unified `payouts` array.
16. `masternode payments`, `masternode winners`, and `getblocktemplate` expose
    all generated masternode payout outputs.
17. Legacy single-payout masternodes continue to pay exactly as before.

## Security Considerations

This DIP removes the need for an off-chain distributor to manually forward the
owner portion of masternode rewards to multiple share owners. It does not remove
the registrar owner's authority to update masternode registration metadata. A
share arrangement that requires immutable payout rights must use additional
contractual, wallet, or protocol mechanisms outside the scope of this DIP.

Payout scripts must not reuse owner, voting, or collateral keys for the same
reason that DIP-0003 restricts current payout key reuse: payout keys may be used
in less secure wallet environments, while owner, voting, and collateral keys
control higher-value masternode functions.

The payout count and minimum share limits reduce the risk of using masternode
registrations to create large numbers of tiny recurring coinbase outputs.
However, the block reward declines over time, so no fixed basis-point minimum
can permanently guarantee that every future payout output will remain above all
policy dust thresholds.

## Copyright

Copyright (c) 2026 Dash Core Group, Inc. [Licensed under the MIT License](https://opensource.org/licenses/MIT)
