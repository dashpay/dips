<pre>
  DIP: TBD
  Title: EvoNode Platform Reward Withdrawals
  Chain: Platform
  Author(s): Ivan Shumkov
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2026-10-06
  License: MIT License
</pre>

## Table of Contents

* [Abstract](#abstract)
* [Motivation](#motivation)
* [Prior Work](#prior-work)
* [Specification](#specification)
* [Rationale](#rationale)
* [Deployment and Compatibility](#deployment-and-compatibility)
* [Test Cases](#test-cases)
* [Security Considerations](#security-considerations)
* [Open Items](#open-items)
* [Copyright](#copyright)

## Abstract

This DIP defines withdrawals from EvoNode owner identities to the owner payout scripts registered on Dash Core. It supports one or multiple P2PKH or P2SH destinations without granting individual participants in a multi-recipient policy unrestricted access to the EvoNode's Platform balance. Existing sole-P2PKH recipient authority is preserved.

An owner authorizes a withdrawal against a particular payout policy. Platform deducts the withdrawal amount once and creates one Asset Unlock transaction paying all entries in that policy. Recipient scripts, amounts, and the Core transaction fee are fixed when Platform accepts the request.

This proposal retains the existing model in which rewards accumulate on an EvoNode identity. It does not establish individual recipient balances or entitlement at the time each reward is earned. The payout policy effective when the withdrawal is accepted applies to the entire requested amount, including credits earned before that policy became effective. All credits held by that identity are fungible: this also covers top-ups, incoming transfers, refunds, and other credited funds, without a reward-only balance. The owner controls when a withdrawal is requested.

## Motivation

Core v24 introduces an ordered owner payout list for deterministic masternodes, including EvoNodes. Supporting the new registration representation alone is insufficient for Platform: an EvoNode with multiple recipients has no single recipient that may safely receive an unrestricted identity transfer key. A P2SH destination likewise cannot be treated as a public key hash.

Platform can continue accruing rewards to these identities while being unable to construct their default withdrawal. This DIP closes that withdrawal gap by preserving the registered Core scripts and applying their shares when an owner requests payment.

Only EvoNodes participate in Platform consensus and earn its validator rewards. Core's shared-collateral masternodes are a separate feature; Core v24 restricts them to regular masternodes. This DIP does not assign Platform rewards or Platform payout identities to shared-collateral participants.

## Prior Work

* [DIP-0003: Deterministic Masternode Lists](https://github.com/dashpay/dips/blob/master/dip-0003.md)
* [DIP-0011: Identities](https://github.com/dashpay/dips/blob/master/dip-0011.md)
* [DIP-0026: Masternode Multi-Party Payouts](https://github.com/dashpay/dips/blob/master/dip-0026.md), including the [Core v24 revision under review](https://github.com/dashpay/dips/pull/184)
* [DIP-0027: Dash Core Credit Pool](https://github.com/dashpay/dips/blob/master/dip-0027.md)
* [DIP-0028: Evolution Masternodes](https://github.com/dashpay/dips/blob/master/dip-0028.md)

DIP-0026 describes Core reward outputs. It does not specify how previously accumulated Platform credits are allocated or who can initiate their withdrawal. DIP-0027 describes the credit pool and Asset Unlock transactions, leaving masternode identity and Platform payout details to subsequent specifications. The rules below are proposed additional Platform consensus rules.

## Specification

The terms MUST, MUST NOT, SHOULD, and MAY express requirements of this proposed protocol. They do not indicate that the proposal has been accepted or activated.

### Terminology

| Term | Definition |
| --- | --- |
| Managed identity | An EvoNode owner identity enrolled in the payout rules defined here. |
| Payout policy | An ordered list of Core output scripts and basis-point shares associated with a managed identity. |
| Current policy | The policy in the Platform state visible at the relevant execution point, updated from the Core chain state accepted by Platform. Queries prove a committed snapshot; block validation may see subsequent updates in the candidate block's transaction. |
| Registered-payout withdrawal | An owner-authorized request that pays only the scripts in a specified current policy. |
| Gross amount | Credits removed for the Core withdrawal, including the Core transaction fee but excluding Platform processing fees. |

### Reward Accrual

Existing Platform reward computation, epoch settlement, reward-share documents, and identity debt repayment MUST retain their behavior. The remainder due to an EvoNode continues to be credited to its owner identity after the applicable Platform reward shares.

This DIP does not apply Core's operator reward percentage a second time to Platform rewards. It does not change Core coinbase payments or the Platform reward-share contract. The payout policy controls withdrawals from the owner identity; it does not override credits already assigned to other identities by reward-share documents.

### Payout Policy

A managed identity MUST have a persistent enrollment marker and an authoritative payout policy in authenticated Platform state. Enrollment MUST remain detectable independently of the presence or validity of the policy. An enrolled identity with missing or invalid policy data MUST NOT fall back to historical transfer-key lookup.

For the Core v24 representation, a policy MUST contain between one and eight entries. Each entry consists of an exact P2PKH or P2SH output script and an integer share between 100 and 10000 basis points. Scripts MUST be distinct and shares MUST sum to 10000. The order MUST match the Core payout list; implementations MUST NOT sort entries by address or script.

A legacy single Core payout script is represented as one entry with share 10000. Its script type MUST be recovered from a type-preserving Core representation. A stored 20-byte hash alone is insufficient to distinguish P2PKH from P2SH and MUST NOT be used to guess the type.

Only processing of the accepted Core deterministic masternode state, or the activation initialization described below, may create or replace a policy. Ordinary Platform identity updates MUST NOT edit it. Policy changes and any corresponding identity-key changes MUST be atomic.

The policy used for a request is the policy visible to state-transition validation in that Platform block, following the protocol's ordered Core update processing. An RPC response obtained from a moving Core tip during request execution MUST NOT determine the destination.

The enrollment marker and last policy MUST survive EvoNode removal. Removal does not itself forfeit accumulated credits. Requests for a removed, enrolled identity use its last committed policy and the retained owner authority.

### Policy Commitment

The policy commitment is `SHA256d(domain || identityId || entries)`, where:

* `domain` is the ASCII byte string `DashPlatform/EvoNodePayoutPolicy/v1` followed by one zero byte;
* `identityId` is the 32-byte Platform identity identifier in its canonical binary representation;
* `entries` is a one-byte count followed by each entry in Core order;
* each entry is a one-byte script length, the exact script bytes, and a two-byte little-endian basis-point share.

Only the standard 25-byte P2PKH and 23-byte P2SH output templates are valid for this encoding. P2SH redeem scripts are not included. The commitment changes if the script type, script bytes, entry order, or a share changes. Reinstating a byte-identical policy produces the same commitment; ordinary identity nonces continue to prevent replay of previously accepted requests.

### Authorization and Request

A registered-payout withdrawal MUST be signed by an enabled OWNER key of the managed identity under the normal identity signature and security-level rules. Possession of an operator key, voting key, one recipient key, or a P2SH script hash alone does not authorize this request.

The request MUST sign and bind the following logical fields using Platform's versioned state-transition encoding:

| Field | Meaning |
| --- | --- |
| Identity identifier | Managed identity to debit. |
| Identity nonce | Existing replay-protection nonce. |
| Gross amount | Credits reserved for the Core withdrawal. |
| Policy commitment | Exact policy the owner authorizes. |
| Core fee rate | Requested duffs per byte, subject to the active protocol cap. |
| User fee increase | Existing Platform processing-fee preference. |
| Registered-payout mode | Explicitly selects these rules rather than an arbitrary destination. |

There is no caller-selected output script or recipient subset in this mode. Pooling is disabled. The state-transition wire generation and numeric identifiers are deployment items; implementations MUST NOT change an existing wire generation's meaning to add these fields.

At acceptance, the signed policy commitment MUST equal the current policy commitment. A request whose policy has changed MUST be rejected. A wallet MUST obtain a fresh preview and signature; it MUST NOT silently substitute a new policy into a previously signed request.

For a policy consisting of one P2PKH entry, the existing enabled TRANSFER authority and its explicit-destination withdrawal remain available. This preserves the existing sole-recipient behavior. That authority MUST be reconciled against the current typed policy. A multi-recipient policy or a sole P2SH policy MUST NOT leave any payout-derived unrestricted TRANSFER key enabled, including obsolete historical keys. Other spending paths MUST NOT provide an equivalent bypass of these restrictions.

An old owner request lacking a policy commitment MUST NOT acquire the new multi-recipient or P2SH behavior implicitly. Existing sole-P2PKH requests may retain their previous generation's supported behavior. Clients SHOULD use the policy-bound mode for all registered-payout withdrawals.

### Amounts and Fees

Let `G` be the gross withdrawal amount in credits. `G` MUST be positive and exactly divisible by the protocol's credits-per-duff ratio. Credits below one duff remain on the identity. Let `D` be the corresponding integer number of duffs.

Let `S` be the exact serialized byte size of the qualified Asset Unlock transaction, including its complete special payload, quorum fields, fixed-size signature, vector counts, and all payout outputs. The Core fee is `F = S * r`, where `r` is the accepted fee rate. The requested rate MUST satisfy the active protocol's minimum and maximum rules; it MUST NOT be silently changed after the request is accepted. Checked arithmetic MUST be used, and `F` MUST fit the Asset Unlock payload's fee field.

The amount to split is `N = D - F`. For ordered shares `b[0]` through `b[n-1]`, output values in duffs are:

```text
value[i] = floor(N * b[i] / 10000), for i < n - 1
value[n - 1] = N - sum(value[0..n - 2])
```

For one entry, its value is `N`. The final Core-list entry receives the rounding remainder, matching Core's owner payout ordering. Intermediate multiplication MUST use sufficient width to avoid overflow.

Every output MUST meet the active Platform/Core withdrawal output floor applicable to its script. Platform MUST reject an amount that leaves any output zero or below that floor. It MUST NOT drop a small recipient, redistribute its amount, or create a partial payout. These floor parameters MUST be deterministic protocol values, not the local Core node's configurable relay policy.

The identity MUST cover both `G` and its normal Platform processing fees. The invariant for the accepted withdrawal is:

```text
sum(output values) + Core fee = G / credits_per_duff
```

All existing withdrawal-capacity limits and credit-pool checks continue to apply to the full gross debit, including its Core fee. Recipient count MUST NOT multiply the debit or divide a single request into independently admitted withdrawals.

### Acceptance and Queue Processing

Acceptance MUST atomically debit the identity by the gross amount, account for normal Platform processing fees, update the appropriate credit and withdrawal-limit accounting, consume the nonce under normal transition rules, and enqueue one withdrawal. The existing queue ordering assigns exactly one transaction index when that withdrawal is built into an Asset Unlock transaction; this DIP does not move index allocation into request acceptance. Once assigned, the index MUST remain fixed for that payment.

The queued record MUST have an explicit format discriminator separate from historical single-output records. It MUST preserve the identity, policy commitment, ordered exact scripts and output values, gross amount, and Core fee. Changing an optional contract-version field from absent to present is not a sufficient discriminator: preexisting formats already use it.

Initial signing, re-signing, and rebroadcast MUST preserve the accepted scripts, amounts, fee, and transaction index. Normal quorum/signing-height updates remain governed by the existing withdrawal protocol. A later policy change, EvoNode removal, or fee-schedule change MUST NOT recompute these monetary fields.

A failed request MUST NOT leave a withdrawal debit, reserved capacity, or partial queue record. Existing rules for charging failed-transition processing fees and consuming nonces remain applicable; this DIP does not introduce a free failure path. A rolled-back block MUST restore all related state. Retrying the same accepted request MUST NOT produce a second payment.

### P2SH Destinations

Platform constructs the exact registered P2SH output without requesting or executing its redeem script. The owner authorizes release to the registered script; Core validates the redeem conditions when the resulting output is later spent. Platform MUST NOT reinterpret the script hash as a public key hash or require one signature to stand for an arbitrary script.

This supports Core-valid P2SH destinations even when their redeem scripts cannot be used as Platform address witnesses. It does not make an unknown, unsatisfiable, or lost redeem script spendable.

### Queries and Client Behavior

Clients MUST be able to obtain a proof of enrollment and the current policy against an authenticated Platform state root. A preview SHOULD show every destination with its script type, basis-point share, output amount, total Core fee, and separate Platform fee estimate.

The wallet MUST distinguish an owner-controlled trigger from recipient spending authority. It MUST NOT advertise independent beneficiary withdrawal or automatic epoch payments for this protocol. Wallets MUST treat an uncertain broadcast as uncertain until they reconcile the nonce and withdrawal status; they MUST NOT automatically create a replacement payment with a new nonce.

## Rationale

### Withdrawal-Time Allocation

The existing EvoNode balance is held by one identity and is not partitioned by payout history. Applying the current policy at withdrawal extends the existing single-payout rotation model without reconstructing an entitlement ledger.

This choice is material: after a policy change, the new recipients receive subsequent withdrawals even if the credits were earned under an older list. No part of an unwithdrawn balance is reserved for a former recipient. A policy accepted into a queued withdrawal, however, cannot redirect that already committed payment. This is a proposed compatibility policy, not a right implied by DIP-0026.

### Owner-Authorized Trigger

The existing owner key can authorize a fixed-destination payout without proving control over all recipient scripts. Unlike Core's automatic coinbase reward distribution, this proposal requires the owner to initiate each Platform withdrawal. Both systems retain the owner's authority to update the payout list, but this proposal additionally depends on owner availability to trigger payment. Requiring every beneficiary to co-sign introduces coordination requirements and cannot generally validate arbitrary Core P2SH scripts on Platform. Giving each beneficiary an unrestricted TRANSFER key would allow that beneficiary to spend the entire shared identity balance.

Permissionless triggers would require additional rules for processing-fee sponsorship, forced small withdrawals, fee griefing, and rate limits. Independent per-recipient claims would require separate entitlement accounting. Neither is introduced here. An uncooperative or unavailable owner can delay payouts; participants retain this trust dependency.

### Existing Platform Address Balances

Distributing newly earned credits directly into typed Platform addresses is an alternative with independent beneficiary control. It is not a complete substitute for this proposal: current Platform P2SH witnesses support only a restricted multisig form, while a Core payout script does not reveal or restrict its redeem script to that form. Such a design also changes reward/debt accounting and requires a decision about policy snapshots during delayed epoch settlement and the allocation of existing balances.

A future accrual-based proposal could address these requirements. This DIP does not relocate existing identity balances or claim that all Core P2SH scripts can sign Platform address transitions.

## Deployment and Compatibility

Activation requires an explicitly selected, unreleased Platform protocol version and support for the policy-bound request, authenticated queries, new queued-record format, and complete signing/rebroadcast path. The selected version MUST preserve replay of all previously activated generations. This DIP does not require Asset Unlock v2 or a Core transaction output-limit increase: at most eight outputs fit the existing Asset Unlock limit.

Let `H0` and its block hash be the Core anchor recorded in the last committed Platform block before activation. Platform MUST first initialize enrollment and policies for all existing EvoNode owner identities whose EvoNodes are present in the full registered Core masternode list at `H0`. This includes registered PoSe-banned EvoNodes. Initialization MUST use that exact chain-anchored list, not a moving tip or a difference from an unproven empty baseline. The type-preserving full-list RPC `protx list registered true HEIGHT`, tied to the accepted Core block hash, is one suitable source. Legacy single-payout data MUST also work before the Core v24 deployment activates.

After initialization, the activation block processes its normal Core updates from `H0` to its proposed accepted Core anchor, atomically updating policies and keys before validating withdrawals. Consequently an EvoNode removed by those updates retains the policy initialized at `H0`; an updated EvoNode uses its new policy; and a newly observed EvoNode is enrolled through registration. With no Core-height advance, full initialization still occurs. A network starting with this protocol MUST initialize its genesis EvoNode list under the same enrollment and typed-policy rules.

Initialization MUST retain identity identifiers, balances, debt, nonces, and previously queued withdrawal records. It may reconcile payout-derived keys and create the new authenticated policy state. It MUST NOT recreate existing identities through the ordinary registration path. Initialization and activation MUST roll back and retry atomically.

An EvoNode first observed after activation is enrolled with its identity and policy. Enrolled identities retain their policy after later removal. Identities whose EvoNodes were already removed before activation are not recoverable from the current full list alone; this draft does not silently assign them a policy. Their previous behavior remains. A separate historical-source recovery rule is required before claiming coverage of those identities.

Historical single-output queued withdrawals MUST continue through their existing format and accounting rules. They MUST NOT be reinterpreted as registered-payout withdrawals. Ordinary identities and regular masternode compatibility paths remain outside enrollment.

Before activation on a network, migration verification MUST record the source Core block hash and height, source Platform state root and protocol version, covered and excluded identity counts, and the exact permitted key/policy changes. Balances, debt, nonces, and old queue records MUST be invariant across initialization itself; subsequent ordinary block processing retains its normal effects. Clean activation and rollback/retry MUST produce the same resulting state root. A missing or inconsistent policy source for an EvoNode registered at `H0` MUST fail initialization. Exclusions are limited to the specified already-removed class and MUST NOT depend on a node's locally available RPC data. No destination may be guessed.

## Test Cases

The following are requirements for a reference implementation. They are not a report of executed tests.

| Case | Required result |
| --- | --- |
| One P2PKH recipient | Owner can request a policy-bound payout; enabled sole-recipient TRANSFER behavior remains available. |
| One P2SH recipient | Owner can pay the exact P2SH script without a Platform redeem-script witness. |
| Two to eight mixed recipients | One debit and transaction; every exact script receives its computed value. |
| Net 10001 duffs, shares 3333/3333/3334 | Ordered output values 3333, 3333, 3335. |
| Net 10001 duffs, shares 3334/3333/3333 | Ordered output values 3334, 3333, 3334. |
| Shares 100/9900, amount too small for first output | Reject the withdrawal without dropping the first recipient. |
| Same 20-byte hash in P2PKH and P2SH entries | Distinct scripts, distinct authority; no type coercion. |
| Payout rotation between preview and execution | Reject stale commitment; do not substitute the new recipients. |
| Policy changed after enqueue | Preserve accepted output amounts, scripts, fee, and transaction index. |
| Accepted request awaiting index allocation, then restart and policy change | Allocate one index through normal queue processing; retain the originally accepted outputs and fee. |
| Single P2PKH changes to multi-recipient policy | Revoke payout-derived TRANSFER authority even if that recipient remains in the list. |
| More than six prior payout rotations | Current committed policy determines default routing without a bounded historical-key guess. |
| Recipient or operator attempts owner mode | Reject authorization; no shared-balance spending authority is inferred. |
| Fee/product overflow, non-duff amount, insufficient funds/capacity | Deterministic rejection with no partial withdrawal state. |
| Core fee schedule changes while queued | Preserve accepted monetary fields during signing and rebroadcast. |
| Removed enrolled EvoNode with remaining rewards | Retained owner may withdraw to the last policy. |
| Activation before Core v24 with legacy P2SH payout | Preserve type; never synthesize P2PKH from the hash. |
| Activation without a Core-height advance | Initialize all covered identities, not only changed entries. |
| Activation with a simultaneous removal/update | Resolve enrollment and policy against the specified accepted Core state deterministically. |
| Failed activation, block rollback, restart, replay | Identical committed result; unchanged historical queue and balances. |
| Owner changes list with an old unwithdrawn balance | New list applies to the next accepted payout; no implicit historical entitlement. |
| Existing Platform reward shares and debt | Unchanged allocation and debt repayment before withdrawal. |

Tests MUST demonstrate actual signed transition acceptance, queued transaction construction, proof verification, and Core acceptance, including a spend of a paid P2SH output under its redeem conditions. Existing broken multi-payout and sole-P2SH withdrawal scenarios MUST fail before the implementation and pass afterward. Migration tests require authentic network-state evidence in addition to synthetic unit fixtures.

## Security Considerations

This protocol enforces destinations for each accepted request, but does not remove the registrar owner's control over future payout configuration or the withdrawal trigger. It is not a trustless fractional ownership or accrued-entitlement protocol. Users MUST be informed of that distinction.

Policy commitments prevent destination substitution between a signed preview and acceptance. They do not prevent a Core-authorized owner from changing the policy and signing a new request. Existing identity nonce and key-revocation rules remain necessary.

Exact script typing prevents a script hash from becoming public-key spending authority. Persistent enrollment prevents missing-policy data from re-enabling obsolete destination inference. Authorization must be checked across all identity spending paths, not only withdrawal construction.

For `n >= 2`, the final recipient receives less than `n - 1` additional duffs beyond its exact proportional entitlement due to rounding. For `n = 1`, no rounding allocation occurs. Repeated small withdrawals can amplify this bounded per-request bias. Protocol output floors and processing fees constrain small requests, but do not eliminate the bias or the owner's ability to choose withdrawal timing.

An excessively small share can make a withdrawal impractical until the balance grows. The protocol preserves the balance and reports the minimum viable gross amount rather than sacrificing a recipient. A lost owner key, lost recipient key, or unsatisfiable P2SH script is not recoverable by changing signature semantics.

## Open Items

This is a design-review draft, not an activation-ready standard. The proposal makes the following explicit policy choices for review:

* Owner-controlled triggering, without independent beneficiary claims.
* Applying the current payout policy to all fungible credits in the requested amount, including previous rewards, top-ups, incoming transfers, and refunds.
* The stated recovery boundary for EvoNodes removed before activation.

Before activation, the specification and reference implementation must additionally fix the Platform protocol version, assigned state-transition wire generation and binary test vectors, authenticated storage/query encoding, new withdrawal-record discriminator, fee/output-floor parameters, and per-network migration inventory. These items must not be selected independently by different implementations.

## Copyright

Copyright (c) 2026 Dash Core Group, Inc. [Licensed under the MIT License](https://opensource.org/licenses/MIT).
