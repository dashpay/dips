<pre>
  DIP: pasta-shared-masternode-collateral
  Title: Decentralized Masternode Shares
  Author(s): Pasta
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2026-07-04
  Requires: 2, 3, 26
  License: MIT License
</pre>

## Table of Contents

1. [Abstract](#abstract)
2. [Motivation](#motivation)
3. [Prior Work](#prior-work)
4. [Specification](#specification)
    1. [Terminology](#terminology)
    2. [Provider Transaction Version](#provider-transaction-version)
    3. [Shared Collateral Script](#shared-collateral-script)
    4. [Collateral Share](#collateral-share)
    5. [Registering a Shared Masternode](#registering-a-shared-masternode)
    6. [Dissolving a Shared Masternode (ProDisTx)](#dissolving-a-shared-masternode-prodistx)
    7. [Updating a Share (ProUpShareTx)](#updating-a-share-proupsharetx)
    8. [Updating the Shared Registrar (ProUpSharedRegTx)](#updating-the-shared-registrar-proupsharedregtx)
    9. [Masternode List State](#masternode-list-state)
    10. [Masternode Reward Payments](#masternode-reward-payments)
    11. [Collateral Spend Enforcement](#collateral-spend-enforcement)
    12. [Forbidden Template Destinations](#forbidden-template-destinations)
    13. [Special Transaction Filtering](#special-transaction-filtering)
5. [Deployment and Compatibility](#deployment-and-compatibility)
6. [Rationale](#rationale)
7. [Test Cases](#test-cases)
8. [Security Considerations](#security-considerations)
9. [Privacy Considerations](#privacy-considerations)
10. [Copyright](#copyright)

## Abstract

This DIP extends [DIP-0003: Deterministic Masternode Lists](dip-0003.md) and
[DIP-0026: Masternode Multi-Party Payouts](dip-0026.md) to allow 2 to 8
participants to trustlessly co-own a single masternode. The participants fund
the collateral atomically in one registration transaction, consensus splits the
owner reward across the participants in proportion to their recorded
contributions, and the collateral can leave the masternode only through a
consensus-enforced dissolution that pays each participant's principal to a
refund script recorded at registration. No participant, operator, miner, or
compromised update path can redirect another participant's principal, and no
participant can be prevented from exiting.

## Motivation

DIP-0026 provides protocol-enforced recurring reward splitting, but it
explicitly leaves the registrar owner in control of the payout list and does
not protect the collateral UTXO from unilateral spending. Its Security
Considerations section notes that "a share arrangement that requires immutable
payout rights must use additional contractual, wallet, or protocol mechanisms
outside the scope of this DIP." This DIP is that protocol mechanism.

Without it, a single collateral holder can spend the collateral, destroy the
masternode, and take the other participants' principal. A P2SH multi-signature
collateral can prevent unilateral theft, but it cannot guarantee unilateral
exit. A dissolution signed before the funding transaction confirms is exposed
to co-signer transaction-identifier malleability on Dash, while signing it
after confirmation still depends on enough participants remaining available
and cooperative. It also does not protect recurring payout rights. This DIP
instead records each participant's contribution, refund script, reward script,
and owner key in consensus and directly enforces refunds, rewards, and update
consent.

This DIP is therefore a strict superset of DIP-0026:

* DIP-0026: Protocol-enforced recurring reward split;
* This DIP: Protocol-enforced funding, reward split, update consent, and
  trustless exit.

## Prior Work

* [DIP-0002: Special Transactions](dip-0002.md)
* [DIP-0003: Deterministic Masternode Lists](dip-0003.md)
* [DIP-0026: Masternode Multi-Party Payouts](dip-0026.md)

## Specification

### Terminology

| Term | Definition |
| --- | --- |
| Participant | One of the 2 to 8 co-owners of a shared masternode. |
| Share | One participant's recorded collateral contribution and associated scripts and key. |
| Share table | The ordered list of shares recorded at registration. Order is consensus-significant. |
| Refund script | The immutable script a participant's principal is paid to at dissolution. |
| Reward script | The script a participant's portion of owner rewards is paid to. Participant-updatable. |
| Share owner key | The ECDSA key (as a key ID) that authorizes a participant's consensus actions. Immutable. |
| Early period | The first `earlyPeriodBlocks` blocks after registration, during which unilateral exit is penalized. |
| Dissolution | The consensus-enforced spend of shared collateral that refunds all participants and removes the masternode. |
| ProDisTx | The special transaction defined by this DIP that performs a dissolution. |
| Actor | The participant designated by `actorIndex` in a dissolution; pays the penalty (if any) and the transaction fee. |
| Unilateral dissolution | A dissolution authorized by exactly one participant. |
| Unanimous dissolution | A dissolution authorized by every participant. |

### Provider Transaction Version

This DIP extends the version 3 (extended addresses) ProRegTx payload, which
carries the DIP-0026 `payouts` field. A version 3 ProRegTx with a non-zero
`sharesCount` is a shared registration. A version 3 ProRegTx with
`sharesCount = 0` behaves exactly as specified in DIP-0026; it must serialize
no shares, no `joinSigs`, `earlyPeriodBlocks = 0`, and `earlyPenalty = 0`, and
a non-zero value in any of these fields is invalid. The fields below are part
of the serialization of every version 3 ProRegTx payload, so this DIP and
DIP-0026 deploy together in the same release (see
[Deployment and Compatibility](#deployment-and-compatibility)).

### Shared Collateral Script

The collateral output of a shared registration must use exactly the following
7-byte script (the template):

```text
0x04 "DSHC" OP_DROP OP_TRUE
hex: 04445348437551
```

Template matching is always exact-script comparison against these 7 bytes,
never prefix matching.

The template contains no keys and is spendable with an empty `scriptSig` at the
script layer. All protection comes from the following consensus rules, active
from deployment activation:

* Creation: An output whose `scriptPubKey` equals the template is valid
  only as the collateral output of a valid shared registration. Any other
  creation — in a normal transaction, a coinbase, another special transaction,
  or a non-collateral output of the registration itself — is invalid.
* Spending: A transaction spending an output whose `scriptPubKey` equals
  the template is valid only if it is a valid ProDisTx whose referenced
  masternode owns that outpoint.

A template output mined before activation (necessarily created deliberately,
against a pattern reserved by this published DIP, and nonstandard to relay)
becomes permanently unspendable at activation. This follows the established
reserved-pattern upgrade path and affects only coins whose owner explicitly
opted in.

### Collateral Share

Each share has the following structure:

| Field | Type | Size | Description |
| --- | --- | --- | --- |
| amount | int64_t | 8 | Collateral contribution in duffs. |
| refundScriptSize | compactSize uint | 1-9 | Size of the refund script. |
| refundScript | Script | Variable | Immutable principal refund script (P2PKH/P2SH). |
| rewardScriptSize | compactSize uint | 1-9 | Size of the reward script. |
| rewardScript | Script | Variable | Reward payout script (P2PKH/P2SH). Zero length means "use refundScript". |
| ownerKeyID | CKeyID | 20 | Immutable share owner key ID. |

For shared registrations, the following fields are appended to the version 3
ProRegTx payload immediately after the `payouts` field defined in DIP-0026:

| Field | Type | Size | Description |
| --- | --- | --- | --- |
| sharesCount | uint8_t | 1 | Number of shares. 0 = not shared; otherwise 2 to 8. |
| shares | CollateralShare[] | Variable | The share table, in consensus-significant order. |
| joinSigs | signature[sharesCount] | 65 * sharesCount | One registration consent signature per share, in share order. |
| earlyPeriodBlocks | uint32_t | 4 | Length of the early period in blocks. |
| earlyPenalty | int64_t | 8 | Penalty in duffs for unilateral dissolution during the early period. |

These fields are serialized in the table order shown above.

All signatures introduced by this DIP, including `joinSigs`, ProDisTx,
ProUpShareTx, and ProUpSharedRegTx signatures, use the owner-key signature
scheme from DIP-0003 and must be canonical. Compact signatures are 65-byte
recoverable ECDSA signatures, and all signatures must use low-S form. High-S
signatures are invalid. This, combined with the digest rules below, prevents
third-party malleation of the affected transaction identifiers.

### Registering a Shared Masternode

A shared registration (version 3 ProRegTx, `sharesCount > 0`) is valid only if
all of the following hold, in addition to DIP-0003 rules not explicitly
replaced here:

1. The deployment (see [Deployment and Compatibility](#deployment-and-compatibility))
   is active.
2. `type` is 0 (Regular masternode). Shared Evo masternodes are out of scope
   (see [Rationale](#rationale)).
3. The collateral is internal: `collateralOutpoint.hash` is null and
   `collateralOutpoint.n` points at an output of this transaction whose value
   equals the required collateral and whose `scriptPubKey` is exactly the
   template.
4. The DIP-0026 `payouts` list is empty (owner rewards derive from the share
   table) and the legacy `scriptPayout` is absent per version 3.
5. `keyIdOwner` is all zeros. The share owner keys replace it.
6. `sharesCount` is between 2 and 8 inclusive.
7. Every share `amount` is at least 100 DASH, and the amounts sum exactly to
   the required collateral.
8. `0 <= earlyPenalty < min(share amounts)`, and `earlyPeriodBlocks` does not
   exceed 420480 blocks (approximately two years at 2.5-minute blocks). If
   `earlyPeriodBlocks` is zero, `earlyPenalty` must be zero: with no early
   period the penalty is never required, but it would still act as the
   unilateral bonus ceiling (output rule 6), leaving that much of the actor's
   share extractable by a stolen owner key for the life of the masternode.
9. No two shares have the same `ownerKeyID`; no share `ownerKeyID` equals any
   owner key registered by any other masternode (see
   [Masternode List State](#masternode-list-state)); duplicate `refundScript`s
   within the share table are invalid; duplicate `rewardScript`s are allowed.
10. Every `refundScript` and non-empty `rewardScript` is P2PKH or P2SH. A P2PKH
    destination must not equal any share `ownerKeyID` in the table or
    `keyIdVoting` (extending the DIP-0026 payee-reuse rules), and no script may
    equal the template
    (see [Forbidden Template Destinations](#forbidden-template-destinations)).
11. The external-collateral `payloadSig` is empty, and each entry of `joinSigs`
    is a valid canonical signature by the corresponding share's `ownerKeyID`
    over `SharedRegConsentHash`.

`SharedRegConsentHash` is the double-SHA256 of the serialization of:

```text
"DashSharedMNReg" || payload version ||
tx version || tx type || tx nLockTime ||
inputsHash || all input sequences || outputsHash ||
type || mode || netInfo ||
keyIdVoting || pubKeyOperator || operatorReward ||
shares || earlyPeriodBlocks || earlyPenalty
```

where `inputsHash` is as defined in DIP-0003, `outputsHash` is the
double-SHA256 of the concatenated serialized transaction outputs in order with
no count prefix (the same construction as `inputsHash`, over outputs instead of
input prevouts), and `shares` is the share table exactly as serialized in the
payload, including the leading `sharesCount` byte. Every field uses its
payload or transaction serialization, and the leading tag is serialized as a
compactSize-length-prefixed string, not as bare bytes. Shared registrations are type 0, so no Platform payload fields
exist to hash. `collateralOutpoint` is deliberately absent: only one output of
the transaction may carry the template (see
[Collateral Spend Enforcement](#collateral-spend-enforcement)), so
`outputsHash` already fixes the collateral slot. Consent binds every
participant to the
exact funding inputs (prevouts and sequences), all outputs (including the
collateral output and every change output), the full share table, the penalty
terms, and the registrar configuration. Consent never relies on the sighash
modes of funding-input signatures, because Dash transaction signatures permit
`SIGHASH_NONE`, `SIGHASH_SINGLE`, and `SIGHASH_ANYONECANPAY`. Covering the
input sequences matters: BIP68 gives them consensus meaning on version 2 and
later transactions, so an uncovered sequence rewrite between consent signing
and funding-input signing could lock a fully consented registration for several
months.

Registration is atomic: if any funding input is double-spent or any participant
withholds a `joinSig`, no shared masternode is created and no participant's
funds move. Co-signer transaction-identifier malleability is harmless: nothing
is pre-signed against the registration txid, and the consent digest binds to
prevouts, sequences, and outputs, which malleation cannot change.

### Dissolving a Shared Masternode (ProDisTx)

This DIP introduces a new special transaction type:

| Name | Special transaction type |
| --- | --- |
| ProDisTx | 10 |

Payload:

| Field | Type | Size | Description |
| --- | --- | --- | --- |
| version | uint16_t | 2 | Payload version. Currently 1. |
| proTxHash | uint256 | 32 | The ProRegTx hash of the shared masternode. |
| actorIndex | uint16_t | 2 | Index into the share table of the actor. |
| sigCount | uint8_t | 1 | Number of signatures: exactly 1 (unilateral) or exactly `sharesCount` (unanimous). |
| sigs | signature[sigCount] | 65 * sigCount | Canonical signatures over `SharedDisHash`. |

There is no mode field: the signature count defines the mode. Exactly one
signature — which must be by `shares[actorIndex].ownerKeyID` — is a unilateral
dissolution. Exactly `sharesCount` signatures — one per share, in share order —
is a unanimous dissolution. Any other count, order, or signer set is invalid.
The signature count is committed into `SharedDisHash` (below), so the mode is
bound into every signature: a third party cannot reinterpret a penalty-free
unanimous dissolution as a unilateral one (or vice versa) by dropping or adding
signatures, which would otherwise leave the inputs and outputs unchanged but
alter the transaction identifier.

A ProDisTx must have exactly one input: the masternode's collateral outpoint,
with an empty `scriptSig`. It must have no outputs other than those required
below.

`SharedDisHash` is the double-SHA256 of the serialization of:

```text
"DashSharedMNDissolve" || payload version ||
tx version || tx type || tx nLockTime ||
all input prevouts || all input sequences || all outputs ||
proTxHash || actorIndex || sigCount
```

The digest commits to the transaction's actual input and outputs directly; the
payload deliberately carries no `inputsHash`/`outputsHash` copies. It also
commits to `sigCount`, which selects the mode, so the unilateral/unanimous
distinction cannot be malleated after signing. The tag is serialized as a
compactSize-length-prefixed string, like `SharedRegConsentHash`'s.

The digest commits `nLockTime` and the input sequence, but consensus does not
otherwise restrict them, and special transactions use transaction version 3,
so BIP68 relative lock-time semantics apply to the collateral input's
sequence. Participants who want a time-locked dissolution may use one; the
monotone validity described below then holds from the first height at which
the transaction is also final. Wallets must verify `nLockTime` and the input
sequence before signing — in particular when co-signing a unanimous
dissolution built by another participant, and when signing a standby
dissolution intended to be broadcastable immediately.

#### Required penalty

```text
early = (spendHeight - registeredHeight) < earlyPeriodBlocks
requiredPenalty = (unanimous or not early) ? 0 : earlyPenalty
```

`spendHeight` is the height of the block containing the ProDisTx and
`registeredHeight` is the masternode's registration height. `requiredPenalty`
can only step from `earlyPenalty` to zero as the chain advances, so it is
non-increasing in `spendHeight`.

#### Output rules

All output rules are minimum-based, with two fixed ceilings: paying more
penalty than required is valid up to the configured `earlyPenalty`, and the
transaction fee is capped. Because `requiredPenalty` is non-increasing and
both ceilings are height-independent, a ProDisTx that is valid at height `h`
is valid at every height `h' >= h`: no dissolution is silently invalidated by
chain progress. A unilateral ProDisTx is invalid
whenever it pays less than `requiredPenalty`. A zero-penalty standby becomes
valid when the required penalty reaches zero, or immediately when
`earlyPenalty` is zero.

Let `a = actorIndex`, `W` = the sum of non-actor share amounts, and
`P = requiredPenalty`. A ProDisTx is valid only if:

1. `actorIndex < sharesCount`.
2. There is exactly one output per non-actor share `i`, paying
   `shares[i].refundScript`, in share order, plus optionally one final output
   paying `shares[a].refundScript` (the actor output). A zero-value actor
   output must be omitted. No other outputs are permitted.
3. For each non-actor output, with `bonus[i] = value[i] - shares[i].amount`:
   `bonus[i] >= floor(P * shares[i].amount / W)`.
4. The sum of all `bonus[i]` is at least `P`.
5. The transaction fee — the collateral value minus the sum of all outputs —
   is at most `MAX_DIS_FEE` = 1000000 duffs (0.01 DASH).
6. In a unilateral dissolution, the sum of all `bonus[i]` is at most
   `earlyPenalty`.

The multiplication in rule 3 must use an intermediate at least 128 bits wide;
a signed 64-bit intermediate can overflow for valid amounts.

Everything not paid to these outputs is the transaction fee, which by value
conservation can only come from the actor's share. Rules 5 and 6 cap the two
paths by which value can leave the actor's share beyond the required penalty —
fees and voluntary penalty overpayment — so a unilateral dissolution pays the
actor output at least `shares[a].amount - earlyPenalty - MAX_DIS_FEE`. Rule 6
does not constrain unanimous dissolutions: every share owner has signed the
exact outputs, so the participants may jointly distribute any bonuses that
respect the per-share minimums, subject only to the fee cap.

The per-recipient minimum in rule 3 uses a plain floor with no remainder
assignment: floors are element-wise monotone in `P`, whereas any remainder
assignment rule is not, and would break monotone validity. Rule 4 forces the
sub-duff remainder onto some non-actor output. The pro-rata floors also prevent
the actor from concentrating the penalty into a colluding share beyond rounding
dust. Constructors should build outputs with the same sequential-floor,
remainder-to-last convention that DIP-0026 uses for rewards; that construction
always satisfies the minimums.

When a valid ProDisTx is confirmed, the masternode is removed from the
deterministic masternode list. Confirmed reward-script or registrar updates
never invalidate a pending ProDisTx (its digest references none of those
fields); the only transaction that can displace a pending ProDisTx is a
competing ProDisTx, which conflicts on the collateral input.

#### Fees and standby dissolutions (non-normative)

Dash relay supports neither BIP125 replacement nor package relay, so a ProDisTx
must embed a sufficient fee at signing time; child-pays-for-parent on the actor
output can only raise the mining priority of a ProDisTx that already meets the
minimum relay fee. A flat fee of roughly 100000 duffs — about one millionth of
the minimum share, and a tenth of the consensus fee ceiling `MAX_DIS_FEE` —
provides large fee-market headroom. Because Dash relay has
no replacement mechanism, the first ProDisTx to reach the mempool for a given
collateral wins; a competing ProDisTx conflicts on the collateral input and is
rejected until the first is mined or dropped.

Because validity is monotone and share owner keys are immutable, a signed
ProDisTx never goes stale. Wallets should have each participant sign a
standby dissolution immediately after registration confirms — unilateral,
paying `earlyPenalty` (valid immediately and forever) or no penalty (valid from
the end of the early period, forever) — and store it with the participant's
refund-key backup, separately from the owner key. If the owner key is later
lost, broadcasting the standby recovers the participant's principal without any
other party's cooperation. A leaked standby can force an early exit, but every
output is fixed by the covenant, so its holder cannot redirect any value.

### Updating a Share (ProUpShareTx)

| Name | Special transaction type |
| --- | --- |
| ProUpShareTx | 11 |

Payload:

| Field | Type | Size | Description |
| --- | --- | --- | --- |
| version | uint16_t | 2 | Payload version. Currently 1. |
| proTxHash | uint256 | 32 | The ProRegTx hash of the shared masternode. |
| shareIndex | uint16_t | 2 | Index into the share table of the share being updated. |
| rewardScriptSize | compactSize uint | 1-9 | Size of the new reward script. |
| rewardScript | Script | Variable | New reward script (P2PKH/P2SH). The script must be non-empty. |
| inputsHash | uint256 | 32 | Hash of all transaction inputs, as in DIP-0003 update payloads. |
| payloadSigSize | compactSize uint | 1-9 | Size of the signature. Must encode 65. |
| payloadSig | unsigned char[] | Variable | Canonical signature by `shares[shareIndex].ownerKeyID` over the payload hash (`payloadSigSize` and `payloadSig` omitted entirely, not serialized as empty). |

A ProUpShareTx updates exactly one share's `rewardScript` and nothing else. An
update must include an explicit, non-empty reward script; the zero-length
`rewardScript` form is not valid for ProUpShareTx because reward scripts must
remain directly filterable by bloom filters.
Share `amount`, `refundScript`, `ownerKeyID`, the participant count, the
penalty, and the early period are immutable for the life of the masternode. The
new reward script is subject to the same script-type, payee-reuse, and template
restrictions as at registration. A ProUpShareTx referencing a non-shared
masternode is invalid. The payload hash is the double-SHA256 of the payload
serialized with the signature fields (`payloadSigSize` and `payloadSig`)
omitted entirely, following the DIP-0003 convention for update payloads.

### Updating the Shared Registrar (ProUpSharedRegTx)

| Name | Special transaction type |
| --- | --- |
| ProUpSharedRegTx | 12 |

Payload:

| Field | Type | Size | Description |
| --- | --- | --- | --- |
| version | uint16_t | 2 | Payload version. Currently 1. |
| proTxHash | uint256 | 32 | The ProRegTx hash of the shared masternode. |
| pubKeyOperator | BLSPubKey | 48 | New operator public key, in the basic (non-legacy) BLS encoding. |
| keyIdVoting | CKeyID | 20 | New voting key ID. |
| inputsHash | uint256 | 32 | Hash of all transaction inputs, as in DIP-0003 update payloads. |
| sigCount | uint8_t | 1 | Must equal `sharesCount`. |
| sigs | signature[sigCount] | 65 * sigCount | Canonical signatures over the payload hash (`sigCount` and `sigs` omitted entirely, not serialized as empty), one per share, in share order. |

A ProUpSharedRegTx updates the whole-masternode registrar fields and requires
one valid signature from every current share owner key, in share order.
`pubKeyOperator` is always serialized and validated in the basic BLS encoding:
shared masternodes only exist after the v24 activation that also retires the
legacy scheme, so a legacy-encoded key is invalid here.
Operator-key change semantics (service reset) match ProUpRegTx in DIP-0003. A
ProUpSharedRegTx referencing a non-shared masternode is invalid, and a plain
ProUpRegTx referencing a shared masternode is invalid. The payload hash each
owner signs is the double-SHA256 of the payload serialized with `sigCount` and
`sigs` omitted entirely, following the same DIP-0003 convention. Unlike
ProDisTx, `sigCount` is not committed into the digest; it needs no commitment
because it must equal the immutable `sharesCount`.

The new `keyIdVoting` is subject to the registration payee-reuse rule in
reverse: its P2PKH form must not equal any share's `refundScript` or effective
reward script (the reward script in use, falling back to the refund script
when empty). Without this check, a registrar update could silently re-create
the payee collision that registration rule 10 forbids.

The operator reward is fixed at registration and is not updatable, matching the
DIP-0003 ProUpRegTx model (where `operatorReward` is likewise immutable after
registration); it is therefore not carried in this payload.

Operator-authorized updates are unchanged: the operator continues to manage
service fields via ProUpServTx (including the operator payout script) and may
revoke via ProUpRevTx. The operator can stop service but cannot spend
collateral, redirect owner rewards, or rewrite ownership.

### Masternode List State

Deterministic masternode state for a shared masternode must store the share
table (without `joinSigs`, which are needed only at registration validation),
`earlyPeriodBlocks`, and `earlyPenalty`. State diffs must report the share
table as a single logical field: any change to a mutable share field includes
the full replacement share table.

Owner-key uniqueness is enforced across the whole masternode list in both
directions: a share `ownerKeyID` must not equal any other masternode's
registered owner key (shared or `keyIdOwner`), and a normal registration must
not reuse any active share owner key.

Proof-of-Service rules are unchanged for shared masternodes. In particular, a
valid ProUpServTx revives a banned shared masternode once its operator and
voting keys are set; the intentionally null legacy `keyIdOwner` does not prevent
revival.

Share data is excluded from the simplified masternode list entry hash
(`CSimplifiedMNListEntry`), matching DIP-0026's treatment of payout data.
RPCs that expose full deterministic state, including `protx info`, should return
the share table, `earlyPeriodBlocks`, and `earlyPenalty`. Extended simplified
masternode list JSON should expose the share table so clients can observe share
updates. None of these JSON fields is a light-client commitment. Full nodes
validate shared rewards and dissolutions from deterministic masternode state
reconstructed from blocks.

### Masternode Reward Payments

Reward payment construction for a shared masternode follows the DIP-0026
procedure exactly, with the owner payout entries derived from the share table:

* The entry ordering is the share-table order;
* The entry weight is the share `amount` (instead of basis points), so entry
  `i` (except the last) receives `floor(ownerReward * amount[i] / collateral)`
  and the last entry receives the remainder;
* The entry destination is the share's `rewardScript` if non-empty, otherwise
  its `refundScript`;
* Zero-amount outputs are omitted, and operator reward handling is unchanged.

This reuses DIP-0026's single rounding convention (sequential floor, remainder
to the last entry) rather than introducing a second one. Implementations must
use an intermediate at least 128 bits wide for the amount multiplication.

### Collateral Spend Enforcement

Template rules cannot live only inside provider-transaction checks. Consensus
implementations must enforce, at both mempool acceptance and block connection:

1. For every transaction, if any input's previous output script equals the
   template, the transaction must be a valid ProDisTx spending that outpoint.
   This is a constant exact-script comparison per input; the masternode list is
   consulted only inside ProDisTx validation.
2. Any transaction output whose script equals the template, outside the
   collateral slot of a valid shared registration, is invalid.
3. ProDisTx, ProUpShareTx, and ProUpSharedRegTx are validated against the
   deterministic masternode list as of the previous block (the current chain
   tip for mempool acceptance). The referenced shared masternode must exist
   in that list. Registering and then updating or dissolving the same
   masternode within one block is invalid. A registration confirmed in block
   H first becomes eligible for these transactions in block H+1, subject to
   all other validity requirements.
4. Masternode removal for a shared masternode occurs only through a validated
   ProDisTx. Collateral-spend removal semantics for normal masternodes are
   unchanged (normal collateral never carries the template).
5. A validated ProDisTx removes its masternode in the same collateral-spend
   phase of deterministic-list construction as an ordinary collateral spend —
   that is, after all of the block's provider transactions have been applied.
   A shared masternode update (ProUpShareTx or ProUpSharedRegTx) and a
   dissolution of the same masternode may therefore appear together in one
   block in either order, provided the masternode exists in the previous
   block's list: the update always applies before the removal takes effect.

Within a block, provider transactions are applied sequentially to the evolving
list, with additional checks to preserve operator-key uniqueness and
voting-key/payee separation after earlier updates. This does not replace the
prior-block validation requirement. Because removal takes effect only in the
collateral-spend phase, share owner keys freed by a ProDisTx become reusable
by a new registration only from the following block.

Mempool implementations should additionally evict pending ProUpShareTx and
ProUpSharedRegTx transactions for a masternode when its ProDisTx confirms, and
should evict a pending ProUpShareTx or ProUpSharedRegTx whose counterpart
confirms in a way that makes it violate the voting-key/payee separation rule
(a confirmed registrar update setting a voting key that a pending share update
pays, or a confirmed share update paying a key that a pending registrar update
sets as the voting key): such a transaction can never be mined against the new
tip and would otherwise linger until expiry.

### Forbidden Template Destinations

Because template outputs may only be created inside shared registrations, a
consensus-mandated output paying the template would be impossible to construct
and could deadlock consensus. Validation must therefore reject the template
script wherever a user-supplied script later becomes a consensus-mandated
output:

* Share `refundScript` and `rewardScript` values (registration and
  ProUpShareTx) — a template refund script would make every dissolution
  invalid, freezing the collateral forever;
* Every provider-transaction payout script for every masternode type and
  payload version, including DIP-0026 payout entries and the operator payout
  script — a template payout would make the coinbase impossible to construct
  when that masternode is paid;
* Governance proposal and trigger payment scripts (validated after
  activation) — a template payee would invalidate the superblock carrying it;
* Asset-unlock (credit withdrawal) destinations — a template destination would
  make the withdrawal transaction invalid.

### Special Transaction Filtering

A shared registration carries the full share table, so special transaction
filters and bloom filters must match it on every share `refundScript`,
`rewardScript`, and `ownerKeyID`, in the same manner that DIP-0026 requires for
payout scripts.

The lifecycle transactions do not carry the share table — only the `proTxHash`
identifying the masternode — so, consistent with the DIP-0003 treatment of
ProUpRegTx and ProUpRevTx, they are matched by `proTxHash`. ProUpShareTx is also
matched by its new `rewardScript`, and ProUpSharedRegTx by its new
`keyIdVoting`. A light client learns a masternode's share
scripts and owner keys from the registration it matched, then follows that
masternode's lifecycle by its `proTxHash`. Two properties make this sufficient
in practice: the refund and reward payments produced by a ProDisTx are ordinary
transaction outputs, matched by script in the base filter, so a client watching
its refund or reward script sees its funds without any special-transaction
logic; and a BIP37 bloom filter with `BLOOM_UPDATE_ALL` inserts the `proTxHash`
automatically when it matches the registration, so an owner-key watcher receives
subsequent lifecycle transactions without further configuration.

Requiring stateless filters to match the lifecycle transactions on the share
`ownerKeyID`s is not possible, because those transactions do not contain the
keys and filter construction performs no masternode-list lookup.

## Deployment and Compatibility

This DIP deploys with Dash Core's v24 network upgrade (`DEPLOYMENT_V24`,
an Enhanced Hard Fork per [DIP-0023](dip-0023.md)), together with DIP-0026.
Contextual validation must recognize special transaction types 10 through 12
so they reach their type-specific checks; those checks enforce the v24 gate.

Before activation:

* Shared registrations, ProDisTx, ProUpShareTx, and ProUpSharedRegTx are
  invalid.
* Creating template-scripted outputs is nonstandard but not consensus-invalid.

After activation:

* All rules in this DIP apply.
* Template outputs created before activation are permanently unspendable.
* Existing masternodes (legacy and version 3 non-shared) are unaffected.
  Normal masternode collateral-spend semantics are unchanged.

Shared registration is restricted to Regular masternodes in this version.
Extending shared ownership to Evo masternodes requires a Platform-side
specification for distributing Platform credits according to the share table;
without it, Platform-side rewards would not follow the consensus split and
would reintroduce the trust this DIP removes.

## Rationale

### Why a consensus covenant instead of multi-signature scripts

P2SH multi-signature collateral can prevent unilateral theft, but its threshold
also makes exit depend on continued signer cooperation. A pre-signed
dissolution can encode the refund amounts, but signing it before funding
confirmation is unsafe on Dash because a co-signer can change the funding
transaction identifier; signing after confirmation preserves the cooperation
requirement. Recording ownership and refund amounts in the provider payload and
enforcing spends in consensus — the same trust model as DIP-0003's deterministic
masternode lists — provides each participant an independent exit. The price is
that the collateral output is anyone-can-spend at the script layer on any chain
that does not enforce these rules; see
[Security Considerations](#security-considerations).

### Why the template is pattern-restricted on both creation and spend

Restricting creation makes the template a trustworthy marker: after activation,
every template output is live shared collateral. Restricting spending by
pattern (rather than by masternode-list lookup) makes the per-input hook a
constant script comparison and closes every path to such an output. Freezing
the (deliberately created, nonstandard) pre-activation outputs follows the
SegWit reserved-pattern precedent and affects only opt-in coins. Exact-script
matching keeps the reserved set to a single 7-byte script.

### Why share owner keys cannot be rotated

Rotation authorization would rest on the very key being replaced, so under key
compromise rotation is first-mover-wins: a thief who rotates first locks the
honest participant out of their own share permanently. With immutable keys,
compromise is a standoff in which the honest holder always retains the right to
dissolve, and principal is protected by the immutable refund script in every
scenario. Share owner keys sign only rare deliberate events and should be held
in cold storage; custody migration uses a penalty-free unanimous dissolution
followed by re-registration. Immutability also makes dissolution validity
unconditional: no confirmed transaction can stale a pending ProDisTx's
signatures.

### Why updates and dissolution require prior-block registration

Requiring prior-block registration keeps block and mempool validation on the
same confirmed-state path. Allowing a dissolution to follow registration in
the same block would require a separate validation path against the evolving
list, including dissolution signature checks during list construction. The
prior-block rule avoids that extra path and duplicate signature checks.

All registered state needed to validate a dissolution — share owner keys,
refund scripts, amounts, penalty terms, and registration height — is immutable.
Updates therefore cannot invalidate a dissolution's authorization or refund
obligations, and no second validation against the evolving list is needed for
ProDisTx. Shared updates follow the same prior-block registration requirement
as other provider updates, while retaining the evolving-list checks needed
for mutable fields.

### Why dissolution outputs are minimum-based

Exact-amount output rules would make a unilateral ProDisTx signed near the
early-period boundary silently consensus-invalid one block later (the required
penalty changes with height, so the exact amounts change). Minimum-based rules
with a non-increasing required penalty make validity monotone: once valid,
always valid. This property is also what makes standby dissolutions safe to
sign years in advance.

### Why unilateral fees and penalty overpayment are capped

The output minimums alone leave two unbounded paths by which value could leave
the actor's share: the transaction fee and voluntary penalty overpayment.
Without ceilings, one stolen share owner key could sign a unilateral
dissolution that pays the victim's entire share to miners as fee, or as
"bonus" concentrated on a colluding participant — principal theft through the
very transaction meant to make it impossible. The fee ceiling is a fixed
constant, and the bonus ceiling is the configured `earlyPenalty` rather than
the height-dependent `requiredPenalty`: both ceilings are stable while the
required minimum only loosens with height, preserving monotone validity, so an
early-period standby paying the full `earlyPenalty` remains valid forever.
With the ceilings, key compromise costs the actor at most
`earlyPenalty + MAX_DIS_FEE` — the forced exit the penalty terms already
price, plus a small constant.

### Why the penalty is redistributed rather than burned or waived

Redistribution compensates remaining participants for losing their node and
payment-queue position. Burning would punish the innocent majority to deny a
malicious participant a small bonus. A penalty waiver triggered by sustained
PoSe ban was considered and rejected: the operator controls PoSe status, and in
practice a participant is often the operator, so a waiver lets a participant
deliberately get the node banned and exit penalty-free during the early period,
converting "the leaver compensates the others" into "everyone loses". There is
exactly one penalty and it applies only to unilateral exits during the early
period; free exit afterwards is structural.

### Why the mode is derived from the signature count

A ProDisTx with one signature is unilateral; with all `sharesCount` signatures
it is unanimous. An explicit mode byte would be redundant with the signature
count and require a consistency cross-check. Both modes share one output-rule
regime because the minimum-based rules degenerate cleanly to
"each participant receives at least their share" when the required penalty is
zero.

### Why this extends provider transaction version 3

Folding shared collateral into version 3 (extended addresses, which carries
DIP-0026's payouts) avoids an additional payload version solely for field
layering. The two DIPs deploy together in v24, so every version 3 payload
carries both field sets.

### Bounds

Two to eight participants matches the DIP-0026 payout-entry cap and bounds
coinbase fan-out and masternode state size. The 100 DASH minimum share keeps
shares meaningful and bounds fragmentation. The two-year cap on the early
period prevents unbounded penalty windows. `earlyPenalty < min(share amounts)`
guarantees the actor a positive remainder, so a dissolution can always pay its
own fee. A nonzero `earlyPenalty` with a zero `earlyPeriodBlocks` is rejected
because it is never required yet still bounds unilateral bonuses, so it would
only serve as a drain ceiling for a stolen share owner key.

## Test Cases

Implementations should include tests for at least the following:

1. A valid shared registration with 2 and with 8 participants; exact
   serialization round-trips for shared payloads and for a non-shared version 3
   payload with an empty share table and zeroed penalty fields.
2. Invalid: shared Evo registration; external shared collateral; share sum not
   equal to the collateral; share below 100 DASH; `earlyPenalty >= min(share)`;
   nonzero `earlyPenalty` with `earlyPeriodBlocks == 0`; early period above
   the cap; non-empty DIP-0026 `payouts` with shares;
   non-zero `keyIdOwner`; a non-shared version 3 payload with non-zero
   `joinSigs`, `earlyPeriodBlocks`, or `earlyPenalty`.
3. Invalid: duplicate share owner key within the table or across masternodes
   (both directions with normal masternodes); duplicate refund scripts;
   refund or reward script paying P2PKH to any share owner key or the voting
   key; refund or reward script equal to the template.
4. Invalid: missing or non-canonical (high-S) signature in each signature-bearing
   payload introduced by this DIP; consent digest mismatch after changing any
   covered field.
5. Invalid: any normal transaction spending a template output; post-activation
   template-output creation in a normal transaction, a coinbase, or a
   non-collateral output of a shared registration. A near-miss script (template
   plus or minus a byte) is unrestricted. A pre-activation template output is
   permanently unspendable.
6. Valid: unilateral dissolution during the early period paying `earlyPenalty`;
   unilateral dissolution after the early period paying no penalty; a
   dissolution signed during the early period confirming after the boundary
   (monotonicity); overpaying the penalty up to `earlyPenalty`; unanimous
   dissolution paying no penalty at any height; unanimous dissolution paying
   bonuses above `earlyPenalty`.
7. Invalid: unilateral dissolution paying no penalty inside the early period;
   any per-recipient floor violation; bonus sum below the required penalty;
   a unilateral bonus sum above `earlyPenalty`; a fee above `MAX_DIS_FEE`;
   redirected or reordered refund outputs; extra outputs; extra inputs;
   non-empty `scriptSig` on the collateral input; wrong actor signature;
   signature count other than 1 or `sharesCount`; unanimous signatures out of
   share order.
8. Invalid: registration followed by ProDisTx, ProUpShareTx, or
   ProUpSharedRegTx for the same masternode within one block; a registration
   reusing a share owner key freed by a ProDisTx in the same block. Valid:
   each of those three transaction types in the block after registration,
   subject to all other validity requirements; an update and dissolution of
   an already registered masternode in one block, in either order; reuse of
   a freed share owner key in the block after dissolution.
9. A pending dissolution remains valid across confirming ProUpShareTx and
   ProUpSharedRegTx transactions; a standby dissolution signed at registration
   broadcasts successfully after the early-period boundary.
10. ProUpShareTx updates exactly one reward script with the correct single
    signature; invalid for wrong signer, non-shared masternode, or any attempt
    to alter immutable fields. ProUpSharedRegTx requires all signatures in
    share order; plain ProUpRegTx is invalid for a shared masternode; a
    ProUpSharedRegTx whose new voting key is paid by any share's refund or
    effective reward script is invalid.
11. Reward split across mined blocks: conservation, remainder to the last
    entry, zero-output omission, operator reward interaction, reward script
    fallback to refund script, and amounts large enough to overflow a 64-bit
    multiplication.
12. Reorg across registration, across the early-period boundary, and across
    update-then-dissolution ordering; restart from a deterministic masternode
    list snapshot before and after shared state changes.
13. Filter matching for every share refund script, reward script, and owner key;
    the new reward script in ProUpShareTx; and the new voting key in
    ProUpSharedRegTx.
14. Proof-of-Service ban and revival of a shared masternode, including revival
    with a null legacy `keyIdOwner`.

## Security Considerations

Non-enforcing chains. The template is anyone-can-spend at the script layer.
On any chain that does not enforce this DIP — non-upgraded software, a chain
split, a hypothetical future consensus regression — shared collateral outputs
are freely spendable. The protection is the hard fork itself: theft can only
"succeed" on chains that are economically meaningless to the participants. This
trade-off is inherent to consensus covenants on a chain without script-level
covenant support and must be accepted with eyes open.

Key separation. The share owner key is control plane, never a fund
destination. The central guarantee — owner-key compromise cannot steal
principal — holds only because the refund destination is independent of the
owner key: a thief who dissolves as the victim still pays the principal to a
script they cannot spend. This is why refund and reward scripts must not pay to
share owner keys. Consensus can enforce this separation for direct P2PKH
destinations, but cannot inspect the spending conditions behind P2SH. Wallets
must keep the owner key independent from the keys controlling either kind of
destination.

Key compromise. A stolen share owner key allows redirecting that share's
future rewards and triggering a penalized unilateral dissolution — never
uncapped principal theft. The dissolution fee and bonus ceilings bound the
loss at `earlyPenalty + MAX_DIS_FEE`; every other duff must reach the actor's
immutable refund script. Because keys cannot be rotated, victim and thief hold
identical capabilities; the honest holder always retains the exit right.

Key loss. Principal is never endangered: any other participant's unilateral
dissolution refunds the key-less participant in full, and outside the early
period this costs the rescuer only the transaction fee. A key-less participant
cannot force exit, one lost key permanently disables the unanimous and
whole-masternode update paths, and losing all owner keys freezes the collateral
forever. Standby dissolutions (see above) reduce all of these to "keep your
standby with your refund-key backup".

Obstruction and forced exits. A participant who refuses to sign whole-masternode
updates can degrade the node (for example, by blocking operator-key
replacement), and an honest leaver both pays the early penalty and distributes
a pro-rata portion of it to the obstructive participant. This is bounded: the
initially configured operator key keeps working indefinitely, exit after the
early period is penalty-free, and the early penalty is a term every participant
consented to at formation. Wallets must present penalty terms prominently and
warn that a zero `earlyPenalty` makes it inexpensive to force an early exit.

Transaction-identifier malleability. The covenant input's empty-`scriptSig`
rule and the low-S requirement on all payload signatures pin every free byte of
a ProDisTx; inputs, sequences, outputs, and lock time are covered by the signed
digest. Without these rules, third parties could mutate a pending dissolution's
txid, breaking child-pays-for-parent fee bumps.

Forbidden destinations. The list in
[Forbidden Template Destinations](#forbidden-template-destinations) is
consensus-critical: missing any entry creates either permanently frozen
collateral or a coinbase that is impossible to construct (a consensus deadlock)
via a crafted script.

## Privacy Considerations

Shared ownership is consensus-visible by construction:

* The share table — amounts, owner key IDs, refund scripts, reward scripts, and
  penalty terms — is public on-chain forever;
* Every payout block creates up to 8 owner outputs that persistently cluster
  the co-owners' scripts with each other and with the masternode;
* The immutable refund script is an address pre-commitment made years before
  the exit that eventually pays it.

Wallets should use fresh keys and destinations for every formation, never reuse
a refund destination across formations or with other on-chain activity, and may
rotate reward scripts freely. Participants who do not want their share linked to
other funds must break the link before funding (for example, by mixing the
funding inputs); note that refunds return as large, non-denominated outputs.

## Copyright

Copyright (c) 2026 Dash Core Group, Inc. [Licensed under the MIT License](https://opensource.org/licenses/MIT)
