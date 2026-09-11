<pre>
  DIP: Unassigned (dip-dashvm-fees)
  Title: Admission bounds, fees, receipts and refunds
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

Extend the native Platform fee pipeline with deterministic contract costs, full affordability before guest execution, one final charge, default-enabled receipts and historical-owner refunds. Repair native fee-version lookup before dependent infrastructure lands.

## Motivation

Metered execution is safe only if admission covers its worst permitted cost and balances are conserved on every outcome. Storage deletion must use historical fee context and refund the real recorded owner. Node-local compilation, caches and speculative retries must not become consensus-dependent charges.

## Specification

### Fee version integrity

Registered fee-table identifiers must round-trip between persisted numbers, registry lookup and every PlatformVersion reference. Unknown identifiers are errors, not a fallback to the current table or array index. Preserve historical storage flags and refund rates on old records. Audit all deletion/refund callers, including scheduled/block lifecycle cleanup, for required historical context. A software correction that changes consensus behavior on historical blocks requires explicit versioned treatment, not retroactive reinterpretation.

### Cost model and sound bounds

Let F be the protocol fee profile and L the admitted resource limits. Before guest execution compute `U = validation_bound + computation_bound(F,L) + native_operation_bound(F,L) + storage_and_receipt_bound(F,L)`. Use checked arithmetic and bound derived index/reference/cascade work, memory growth/initialization, scanned keys, guest encoding expansion and repeated copies. An operation whose bound cannot be established is unavailable or constrained to a form with a sound bound. Output-size limits alone do not bound query work.

Check that the authorized live payer can cover U, including other obligations in accepted order. Establish invocation-local holds that cannot be spent twice. The direct signer pays the direct/nested invocation scope; scheduled work uses its declared authorized live source. Native transfer amounts and storage deposits must be reserved consistently with actual payer/owner policy. Nested code cannot change payer or exceed delegated spending limits. Recheck at execution after CheckTx; no guest execution occurs in CheckTx/RecheckTx.

One contract-only computation counter covers guards, all modules, nested calls and scheduled execution. Enforce both per-invocation and per-block contract limits on proposal creation and validation. Existing native event budgets remain; do not create the previously rejected combined native-event budget. Wall-clock time never decides a paid computation limit.

### Actual settlement

Charge deterministic accepted execution work plus existing native processing/storage charges exactly once. A host-entry overhead may be added where it represents separate work; do not charge a native query twice because it passes through a VM adapter. Native reference tests cannot provide consensus fuel prices; actual metered runtime vectors do. Local compilation time, artifact misses and internal retries have zero additional protocol execution charge.

| Outcome | Application effects | Settlement |
| --- | --- | --- |
| Successful accepted invocation | All validated outer/nested effects atomically | Actual charge; release unused hold; native nonce outcome; optional bounded receipt |
| Deterministic paid failure after admitted execution | None of the outer/nested application effects | Charge specified consumed work and failure bookkeeping; native paid-failure nonce rule; optional receipt |
| Structural/authentication/admission rejection | No guest execution or application effects | Existing native rejection-stage fee/nonce rules; never invent an execution receipt for unexecuted guest work |
| Speculative attempt discarded | No accepted effects | No separate charge/nonce/receipt; later canonical attempt settles once |
| Genuine infrastructure/storage fault | No fabricated guest success/failure | Abort/recover through existing node/protocol rules; never hide it with paid settlement |

The exact pre-execution error-to-fee/nonce mapping is bound to existing native validation stages in the allocation register. A numeric error ID alone does not define paidness. Refund unused invocation holds; storage fees remain subject to actual native allocation/deletion rules.

### Code and preparation economics

Charge accepted new canonical bytes permanently using native storage accounting. Deduplicate unchanged blobs within the same contract: new versions pay new manifest/binding storage and bounded validation, while already-stored bytes preserve their original owner/rate and do not earn another refund. No reference-count deletion of accepted code. Deployer charges cover protocol validation and accepted readiness verification; operators pay local native compilation. Refund unused preparation funding on authorized cancellation after applicable costs without deleting accepted bytes. Prototype one bounded upload before deciding any separate staging/chunking design.

### Receipts

Receipts default to enabled and the contract declares retention or disables them. Pre-reserve a bounded receipt/storage cost before execution so reporting failure cannot itself exceed the admitted bound. Store one outer receipt containing invocation/execution position, resolved version/method, success or deterministic paid failure, actual cost and bounded nested outcomes. Do not create one default receipt per function/module, or store speculative attempts. Deterministic truncation/omission of optional detail must be defined in its codec; required outcome/fee fields cannot be dropped.

Proposed retention rule snapshots effective terms at creation; later policy changes apply to new receipts. Any retrospective change is an explicit bounded metered native operation. Infinite retention has no expiry index entry. Receipt deletion and expiry-index removal are atomic. The receipt stores native ownership/fee context; deletion refunds that owner, not the caller performing cleanup. A receipt's inclusion proof proves a stored current-state record, not arbitrary historical execution correctness.

### Typed refund ownership and conservation

Use a typed owner such as native identity, contract bucket or existing native destination where supported. Never reinterpret all ownership flags as identity IDs. Wiped contract credits and later refunds go to the current processing pool; another payer's refund remains theirs. Refunds to frozen contracts follow permitted native inbound rules without executing guest code.

Reuse the existing prefunded ledger for job removal. Count its money once and keep purpose metadata nonmonetary. Registration debits the actual funder; settlement consumes removal cost and returns unused value once. Fee upgrades must preserve removal affordability or settle affected old jobs before raising an unpayable obligation. Incremental wipe/cleanup cannot credit a balance again after logical settlement. Test conservation across contract buckets, native identities, prefunds, processing/storage pools and per-token ledgers separately.

## Backward compatibility and deployment

The small 4.3-dev native fee-registry/refund prerequisite is separable from 5.0 contract pricing. Proposed early slices do not complete the full DashVM fee tasks. Preserve historical replay and old fee formats on both replay-from-genesis and saved-state upgrade paths. Exact new rates and limits require measurements and versioned allocation before activation.

## Security considerations

Affordability must include failure and receipt costs; no underfunded path can execute expensive guest work first. Repeated failed reads, deep nested structures, cache-dependent native costs, integer overflow and ownership misrouting are attack surfaces. A sound upper bound is a protocol obligation, not a UI estimate. Block boundaries and epochs may change fee destinations; settlement uses the specified current processing pool and historical storage context correctly.

## Test vectors and reference implementation

Require exact U/actual/refund vectors for success, guard rejection, nested failure, exhaustion, receipt on/off/expiry, same-payer calls, scheduled-only blocks, cancellation, wipe and late refunds across fee upgrades. Replay stored fee IDs through every registry entry and reject unknown IDs. DPP/native fee modules and rs-platform-version own tables; Drive owns storage flags/refunds/operations; rs-drive-contracts meters and holds; ABCI settles. The provisional appendix is a measurement starting point, not production price evidence.

## Rationale

Upfront full bounds prevent unpaid execution; actual final charging avoids billing discarded speculation. Existing storage accounting preserves compatibility. Default receipts improve usability while contract-controlled retention recognizes their real storage cost.

## Related drafts and implementation tracking

[DVM-01](dip-dashvm-protocol.md) · [DVM-02](dip-dashvm-engine-abi.md) · [DVM-03](dip-dashvm-activation.md) · [DVM-04](dip-dashvm-storage.md) · [DVM-05](dip-dashvm-guards.md) · [DVM-06](dip-dashvm-execution.md) · [DVM-08](dip-dashvm-scheduling.md) · [DVM-09](dip-dashvm-governance.md) · [DVM-10](dip-dashvm-proofs-clients.md) · [DVM-11](dip-dashvm-rust-sdk.md) · [DVM-12](dip-dashvm-external-primitives.md)

* [43-FEES](https://github.com/dashpay/platform/issues/4675): Repair existing fee history (4.3-dev).
* [50-ENGINE](https://github.com/dashpay/platform/issues/4683): Implement the deterministic runtime, validator and compatibility corpus (5.0-dev).
* [50-GUARDS](https://github.com/dashpay/platform/issues/4685): Implement native guards and preserve contested-index awards (5.0-dev).
* [50-CALLS](https://github.com/dashpay/platform/issues/4687): Implement atomic calls, delegation and ordered parallel execution (5.0-dev).
* [50-SCHEDULE](https://github.com/dashpay/platform/issues/4688): Implement time-only live-paid schedules and removal settlement (5.0-dev).
* [50-FEES](https://github.com/dashpay/platform/issues/4689): Implement contract bounds, actual charging, receipts and historical refunds (5.0-dev).
* [50-CAP-COST](https://github.com/dashpay/platform/issues/4691): Validate cost and refund bounds for every native capability (5.0-dev).
* [50-GOV](https://github.com/dashpay/platform/issues/4695): Implement governance, bounded wipes and vestige recovery (5.0-dev).

[Complete storage mapping](https://github.com/dashpay/platform/issues/4626#issuecomment-5634141255) · [Capability catalogue and current amendments](https://github.com/dashpay/platform/issues/4626#issuecomment-5636957194) · [Module architecture](https://github.com/dashpay/platform/issues/4626#issuecomment-5636536959) · [Owner decisions and provisional limits](https://github.com/dashpay/platform/issues/4626#issuecomment-5583771268). These linked appendices retain their stated confirmed/proposed status.

## Copyright

This working proposal is released under the MIT License, following the default license of the Dash DIPs repository.
