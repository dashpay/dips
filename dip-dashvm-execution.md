<pre>
  DIP: Unassigned (dip-dashvm-execution)
  Title: Atomic calls and ordered parallel execution
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

Define canonical sequential semantics for direct, internal-module and cross-contract calls, and permit parallel execution only when it produces exactly those semantics. Each transition sees current accepted predecessor state plus its own writes. One outer invocation has one atomic application-effect scope and one settlement.

## Motivation

Parallel workers can accelerate independent computation, but discovering only matching input/output keys is insufficient: absent keys, ranges, indexes, permissions and cost paths also affect results. The canonical writer must preserve native operations, Merk shape, fee accounting and the agreed transaction order.

## Specification

### Sequential reference semantics

Let B be the agreed block work sequence, including native lifecycle/scheduled phases. Execute each accepted work item against the state produced by its accepted predecessors. For a guest invocation, expose prior native effects from that invocation through a transaction-local view. Later work and abandoned speculative branches are invisible. Apply native validation and action conversion for every proposed effect; commit a successful outer application's effects atomically with its specified settlement. Drive ABCI commits the block transaction once.

Canonical order is the existing Platform ordering protocol plus explicit new phase conventions. This draft does not introduce a fairness/order auction or claim arbitrary transaction reorderings preserve outputs. Document ordering exposure for each value-moving capability.

### Caller and authority model

Context distinguishes the transaction signer, immediate caller contract, executing contract/version/module, resource owner and explicitly delegated rights. A direct call authenticates through native identity rules; the direct signer pays its invocation as specified by DVM-07. Nested calls do not inherit unrestricted signer authority. Delegation binds target, method/resource/action and bounded scope; receiving permission and native asset rules still apply. Same-contract module calls preserve the same contract authority and shared limits.

Cross-contract calls target the latest visible stable method route. Direct users may choose supported older code. Maintain an active contract-ID stack: entering a contract already active in that call stack is forbidden, including through predicates. This does not forbid ordinary Rust recursion or calls between modules of the same active contract; those consume the shared logical stack. A callee cannot increase remaining bounds, change payer or independently commit.

### Outcomes and atomicity

Success accepts validated application effects plus settlement. An actual nested failure, guest trap, guard rejection, native-action validation error or exhausted deterministic bound marks the outer invocation failed; returning `Ok` after catching the error cannot restore success. Roll back all outer and nested application effects. Retain only specified fee/nonce/receipt/job-attempt bookkeeping. Native missing read results and randomness `NotReady` are ordinary typed values, not hidden failure exceptions. Infrastructure faults follow existing node/protocol recovery and cannot be relabeled as paid guest failures.

The integration layer owns the failure latch; guest code cannot clear it. It also prevents writes, transfers or successful return from committing after poisoning. Native result classification must distinguish unsuccessful control/data queries from an attempted unauthorized/invalid state mutation. Tests cover those distinctions explicitly.

### Parallel execution — proposed implementation algorithm

The serial algorithm is authoritative. A correct serial implementation remains valid regardless of worker count. Parallel workers execute bounded speculative calls against an identified accepted prefix or a faithful isolated branch that exposes that prefix. The inspected GroveDB develop read-only snapshot is not a writable fork of the uncommitted transaction; building that capability is upstream work, not an existing guarantee.

Each attempt records the prefix/profile identity, typed native intent log, return/failure and fee/resource result, and every semantic observation used to produce them. Dependencies include point values and absence, ranges and their ordering/limits, index/schema definitions, permissions/ACL/group membership, code routing/lifecycle, nonces/balances/fee tables, derived writes and native operation-cost assumptions. A write-only key is not independent if its validation reads existing state. Query range tracking must detect phantom inserts/removals and changes outside returned rows that affect rank/count/cost.

At the canonical position of an attempt:

1. Compare all recorded dependencies and behavior/profile inputs with the current accepted prefix. Include cost-sensitive observations even when returned application values happen to be equal.
2. If any dependency is changed, unavailable or incompletely tracked, discard the attempt and reexecute against the current prefix. Revalidation alone cannot repair changed control flow or metering.
3. If valid, replay the typed native operations through the same native paths and ordering as serial execution, including derived indexes and two-stage namespace insertion. Do not merge physical Merk deltas or independently calculated root hashes.
4. Validate replay outcome, actual cost/refund dependencies and final result. If replay reveals a missing dependency or mismatched application behavior, abort the attempt and execute canonically; do not publish partial speculative fees/results.
5. Accept one result and its settlement, advance the prefix and continue.

The writer remains single and ordered. Parallelism applies to computation/read/validation work where safe; all accepted effects become externally committed together at block commit. Native work that cannot yet declare sound dependencies uses the serial path. A coarse contract/subtree dependency is safe but reduces concurrency. It is not acceptable to assume a disjoint declared input list is complete without host enforcement.

### Bounds and fallback

Bound workers, speculative memory, observation-log size and attempts. Overflow/coarsening selects serial execution; it cannot become a new paid error. Proposed initial fallback is at most one speculative attempt followed by a canonical serial retry for a conflicting item; more retries are a local optimization only if consensus charges/outcomes remain identical and resource exhaustion cannot invalidate a block. Internal retries consume node resources but add no user charge, nonce, receipt or scheduled attempt. Charge only the accepted canonical execution and its native work.

## Compatibility and deployment

Existing native state transitions must participate in conflict/observation handling or execute as serial barriers; they cannot bypass dependencies by being classified non-contract. Protocol upgrades and lifecycle events establish barriers before affected work. The implementation may ship a serial engine while parallel support is developed, but the tracked 5.0 acceptance for ordered parallel execution stays open until the required feature and equivalence tests pass.

## Security and performance considerations

An attacker can create shared balances, hot indexes, giant ranges or conflicts that erase parallel speedups. Bound speculation and retain deterministic serial fallback. Single-writer native storage is an explicit throughput limit. Hidden storage-cache costs cannot leak into consensus charging. No reentry reduces attack surface but limits composability; it is an approved rule rather than a claim of universal superiority.

## Test vectors

Include two increments to one key, disjoint writes sharing one payer, range phantoms, absent-key insertion, index/schema/ACL changes, latest-version activation, same-invocation writes, caught nested failure, logical stack across modules and native operation failure during replay. Compare serial and parallel roots, outputs, fees, nonces, refunds, receipt bytes and job outcomes at worker counts 1 and many. Inject a deliberately omitted dependency and show acceptance rejects or detects the mismatch. Host-fault scheduled recovery is a separate required rehearsal.

## Reference implementation and open allocations

rs-drive-contracts owns scope/context/dependency tracking, call routing and native-effect mediation; Drive owns isolated native views/replay and shared validation; GroveDB needs the proposed branch facility; ABCI owns order and commit. Exact observation representation, native cost/cache dependency coverage and upstream branch API require implementation evidence. The serial specification provides an executable oracle without dictating unsafe physical tree merging.

## Related drafts and implementation tracking

[DVM-01](dip-dashvm-protocol.md) · [DVM-02](dip-dashvm-engine-abi.md) · [DVM-03](dip-dashvm-activation.md) · [DVM-04](dip-dashvm-storage.md) · [DVM-05](dip-dashvm-guards.md) · [DVM-07](dip-dashvm-fees.md) · [DVM-08](dip-dashvm-scheduling.md) · [DVM-09](dip-dashvm-governance.md) · [DVM-10](dip-dashvm-proofs-clients.md) · [DVM-11](dip-dashvm-rust-sdk.md) · [DVM-12](dip-dashvm-external-primitives.md)

* [44-ENGINE](https://github.com/dashpay/platform/issues/4681): Build a small isolated VM experiment and test foundation (4.4-dev).
* [50-GUARDS](https://github.com/dashpay/platform/issues/4685): Implement native guards and preserve contested-index awards (5.0-dev).
* [50-READS](https://github.com/dashpay/platform/issues/4686): Implement bounded current-state guest reads (5.0-dev).
* [50-CALLS](https://github.com/dashpay/platform/issues/4687): Implement atomic calls, delegation and ordered parallel execution (5.0-dev).
* [50-SCHEDULE](https://github.com/dashpay/platform/issues/4688): Implement time-only live-paid schedules and removal settlement (5.0-dev).
* [50-FEES](https://github.com/dashpay/platform/issues/4689): Implement contract bounds, actual charging, receipts and historical refunds (5.0-dev).
* [50-NATIVE](https://github.com/dashpay/platform/issues/4690): Implement the full native capability and collection adapters (5.0-dev).
* [50-VERIFY](https://github.com/dashpay/platform/issues/4696): Complete upgrade, sync, recovery and release evidence (5.0-dev).

[Complete storage mapping](https://github.com/dashpay/platform/issues/4626#issuecomment-5634141255) · [Capability catalogue and current amendments](https://github.com/dashpay/platform/issues/4626#issuecomment-5636957194) · [Module architecture](https://github.com/dashpay/platform/issues/4626#issuecomment-5636536959) · [Owner decisions and provisional limits](https://github.com/dashpay/platform/issues/4626#issuecomment-5583771268). These linked appendices retain their stated confirmed/proposed status.

## Copyright

This working proposal is released under the MIT License, following the default license of the Dash DIPs repository.
