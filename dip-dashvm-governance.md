<pre>
  DIP: Unassigned (dip-dashvm-governance)
  Title: Freeze, wipe and deleted-contract custody
  Chain: Platform
  Layer: Consensus
  Author(s): To be confirmed
  Comments-Summary: Initial draft; discussion and implementation tracking linked below.
  Status: Draft
  Type: Standard
  Created: 2026-09-11
  License: MIT License
</pre>

These are draft proposals for review, not assigned/accepted DIPs or implemented features. Confirmed design decisions are preserved. Sections explicitly marked proposed and the [shared allocation register](dip-dashvm/allocations.md) contain engineering proposals requiring review and measurement. Exact wire identifiers, the production engine profile, limits and prices remain open. DVM aliases identify this proposal series and are not official DIP numbers. Final authorship and official numbering remain subject to editorial review.

[Parent plan](https://github.com/dashpay/platform/issues/4626) · [Implementation tracking](https://github.com/dashpay/platform/issues/4676) · [Shared allocation register](dip-dashvm/allocations.md)

## Abstract

Specify contract lifecycle governance requiring strictly more than two-thirds of all active eligible evonodes, one-week voting windows and early approval. A wipe immediately disables contract authority and accounts for its assets, while bounded cleanup removes physical state without deleting canonical code.

## Motivation

Network decisions must count the intended electorate, settle credits and issuer tokens exactly once, and preserve foreign assets under tightly scoped custody. An unbounded physical deletion or an unrestricted recovery key would violate those goals.

## Specification

### Proposal and vote records

A proposal binds network domain, unique proposal ID, action (`Freeze`, `Unfreeze`, `Wipe`, `RecoverVestige`), target contract, exact action payload, opening consensus time, one-week deadline, membership-check reference and outcome. Recovery binds exact token IDs, amounts and recipient. One evonode has one effective choice per proposal across all choice trees. Proposed vote-update convention permits replacing its choice while the proposal remains open, atomically moving the keyed record; repeated identical submissions are idempotent. This convention and ballot encoding require native vote-model review and replay vectors.

Use the same agreed current active-eligible Core membership boundary as DVM-03, not only current validators or those casting ballots. For N active eligible evonodes and Y eligible yes choices require `N > 0 && 3*Y > 2*N`, using checked wide integers. Exactly two-thirds fails; minimum is `floor(2*N/3)+1`. Governance thresholds are distinct from 80% compilation readiness and native contested-index voting parameters.

### Decision timing — proposed engineering convention

Use the beginning-of-block lifecycle phase after the agreed membership update and before affected scheduled work. Revalidate voters and denominator against one consistent current view. Reconsider on ballot arrival and membership change; raw choice counts do not establish eligibility. A bounded paged scan cannot approve using mixed or stale membership. Apply approved actions exactly once with their proposal outcome.

Proposed expiry boundary: decision times strictly before `opened_at + 604800 seconds` may approve early; at or after the deadline an unapproved proposal closes without approval. A vote accepted later in a block cannot retroactively change that block's prior lifecycle phase. Pending verification that has not established a valid crossing by expiry does not extend the window. This explicit ordering is an engineering proposal to be reconciled with native event phases, not a new threshold choice.

### Freeze and unfreeze

Native frozen state blocks affected guest calls, predicates and outbound guest-authorized effects; it cannot be implemented by skipping rules and accepting the write. Authorized code updates remain possible while frozen but do not clear a network freeze. Permitted native inbound credits/token transfers/refunds can continue under existing asset rules without executing frozen code. If authorization would require a guest callback that cannot run, the transfer is not silently authorized. Contract-defined freezes follow their declared native-compatible policy; a network freeze requires the same network vote to unfreeze.

### Wipe transition

At approved wipe, set permanent wiped/custody state, disable routing and pending activation, and prevent execution/spendability immediately. Retain accepted canonical blobs/manifests and required lifecycle facts forever. Introduce durable bounded cleanup work for deletable documents/indexes/collections/jobs/receipts and related locators. A cleanup step updates its native effects and cursor atomically and is safe to retry after a crash. A later update, query or cleanup resume cannot resurrect state.

**Credits:** remove the contract's live credit total from spendable accounting and add it to the current processing pool exactly once. Proposed storage technique marks the populated ordinary SumTree as `NotSummed` while retaining its inner data for cleanup; this is an engineering mechanism requiring populated-tree cost/root/proof tests, not an already implemented primitive guarantee. Every balance/aggregate/spend path must respect the wipe exclusion. Later refunds owned by that contract enter the current processing pool; refunds owned by others remain theirs. Physical deletion never adds that money a second time.

**Issuer tokens:** all tokens issued by the wiped contract cease to exist, including units held by native identities and other contracts. Implement a bounded logical issuer/token tombstone using the authoritative native token-to-issuer relation, and require all query, transfer, supply, mint/burn, freeze, distribution and proof paths to recognize it before any physical scan. Existing code paths lacking that check block completion of the wipe feature. Clear physical holdings/indexes incrementally without a second burn or resurrected supply. Populated pre-existing native issuances must be indexed or natively discoverable before smart activation.

**Foreign tokens:** tokens issued by other contracts retain their existing authoritative native holdings but custody becomes the deleted-contract identity vestige. The vestige is native authority state, not a fabricated ordinary identity with a private key and not a copied balance ledger. No former owner, retained guest code or generic admin key can spend those holdings.

### Specific vestige recovery

An approved recovery proposal authorizes only its exact token/amount/recipient transfer. At application, recheck remaining custody balance, token existence and native token transfer restrictions. Execute transfer and consumed-authorization marker atomically. Reject replay or a substituted recipient/amount. Proposed failure convention: if approved payload cannot pass current native validation, record a deterministic failed-application terminal outcome with no partial transfer; a changed request needs a new vote. This must be reviewed against the native governance error model. Approval is not permission to bypass issuer freezes or native asset rules.

## Engine recovery is separate

There is no new engine emergency pause authority. Engine behavior changes and emergency recovery use normal protocol upgrades. Removing a bad ordinary transition may help a proposer, but a reproducible scheduled host fault can halt processing and require coordinated recovery. Release tests must rehearse that selected policy rather than claim freeze/wipe voting always remains reachable during an engine halt.

## Backward compatibility and security

Keep contract governance separate from contested-index polls and protocol-upgrade voting. Version its namespace/codecs and native token lifecycle checks. Fail closed on missing wipe/custody state where required; prove current balances together with relevant live/wiped/issuer state. Bound every cleanup and tally phase; retain original refund flags and permanent code. Native inbound permission is not outbound recovery authority.

## Test vectors

N=3 requires 3 yes; N=300 requires 201; N=400 requires 267; N=1000 requires 667; empty set fails. Test one-week boundaries, early approval, changed electorate, duplicate/replaced ballots and once-only application. Wipe fixtures cover all holder types, contracts issuing and holding multiple tokens, pre-existing tokens, late refunds, third-party prefunds, cleanup interruption and sync. Recovery vectors include wrong amount/recipient, replay, frozen/destroyed issuer token and native validation failure. Match roots, supply and credit conservation on both proposal paths.

## Reference implementation, rationale and allocations

DPP defines proposal/payload; ABCI handles current membership and decisions; Drive handles native tombstones, conservation, vestige custody and cleanup; clients prove explicit lifecycle state. Exact tags, vote-update and application-failure encoding, phase wiring and logical exclusion mechanisms remain engineering review entries. Logical invalidation plus bounded physical cleanup achieves immediate policy effects without unbounded traversal.

## Related drafts and implementation tracking

[DVM-01](dip-dashvm-protocol.md) · [DVM-02](dip-dashvm-engine-abi.md) · [DVM-03](dip-dashvm-activation.md) · [DVM-04](dip-dashvm-storage.md) · [DVM-05](dip-dashvm-guards.md) · [DVM-06](dip-dashvm-execution.md) · [DVM-07](dip-dashvm-fees.md) · [DVM-08](dip-dashvm-scheduling.md) · [DVM-10](dip-dashvm-proofs-clients.md) · [DVM-11](dip-dashvm-rust-sdk.md) · [DVM-12](dip-dashvm-external-primitives.md)

* [50-NATIVE](https://github.com/dashpay/platform/issues/4690): Implement the full native capability and collection adapters (5.0-dev).
* [50-GOV](https://github.com/dashpay/platform/issues/4695): Implement governance, bounded wipes and vestige recovery (5.0-dev).
* [50-VERIFY](https://github.com/dashpay/platform/issues/4696): Complete upgrade, sync, recovery and release evidence (5.0-dev).

[Complete storage mapping](https://github.com/dashpay/platform/issues/4626#issuecomment-5634141255) · [Capability catalogue and current amendments](https://github.com/dashpay/platform/issues/4626#issuecomment-5636957194) · [Module architecture](https://github.com/dashpay/platform/issues/4626#issuecomment-5636536959) · [Owner decisions and provisional limits](https://github.com/dashpay/platform/issues/4626#issuecomment-5583771268). These linked appendices retain their stated confirmed/proposed status.

## Copyright

This working proposal is released under the MIT License, following the default license of the Dash DIPs repository.
