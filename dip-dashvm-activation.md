<pre>
  DIP: Unassigned (dip-dashvm-activation)
  Title: Compilation readiness and executable lifecycle
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

Activate one immutable contract version only after at least 80% of the full active eligible evonode set reports compilation readiness, followed by an additional consensus-time delay. Specify pending replacement, permanent code, supported/deprecated/retired versions and latest-method routing.

## Motivation

Compilation should occur before execution becomes possible. Readiness must count the whole eligible network, survive report retransmission and membership changes, and never depend on a validator's local wall clock or artifact cache. Deprecated versions remain callable during a warning period without forcing contracts to link to stale versions.

## Specification

### State

For each contract retain immutable manifests/blobs, one optional pending round, current latest active version, and per-version lifecycle metadata. A pending round contains contract/version/manifest/profile identifiers, acceptance time, round ID, keyed ready reports, membership-check cursor/reference if needed, first validated crossing and optional activation deadline. Supported/deprecated/unsupported status is distinct from pending/active selection and contract-wide freeze/wipe state.

Only authorized update actions change a pending candidate. Replacing it atomically cancels the old round and its timer; old reports cannot count for the replacement. Cancelling it stops activation and refunds unused preparation funding after specified costs; all accepted canonical bytes remain. Collection has no automatic expiry. The previous latest version continues until the replacement activates, subject to its own freeze/retirement rules.

### Membership and reports

Use the agreed Core masternode list referenced by the Platform block at its specified membership-update phase. Never count the current validator quorum alone or query a newer node-local Core height. One authenticated eligible evonode identity has one yes report per round. A report binds network, contract/version, round, manifest and engine/preparation profile and can be sent only after full bundle compilation and binding checks. Duplicate reports are idempotent; failed delivery permits retransmission. Stale keys/profiles/rounds cannot be replayed.

Let `N` be all active eligible evonodes in that same membership view and `Y` the eligible distinct yes reports. Threshold is `N > 0 && 5*Y >= 4*N`, evaluated with checked wide integers. A count tree accelerates tallying but does not establish current voter eligibility. Prune ineligible votes and revalidate against the agreed view when a raw count could cross, and reconsider on membership changes, including a decrease in N without a new report. Bounded paged validation uses one immutable membership reference and cannot establish a crossing from a partial/stale scan. If membership changes before the result is committed, revalidate or invalidate that scan's certificate.

The exact active-eligibility predicate must be bound to the current native evonode eligibility implementation and versioned in the allocation register. It cannot be inferred from report participation. This is an implementation binding still requiring source-level vectors, not an unanswered threshold policy.

### Timing and block phases — proposed engineering convention

Use monotonic committed Platform consensus time, checked for overflow. At a beginning-of-block lifecycle phase, first apply the block's agreed membership update, then finish/revalidate pending threshold checks, apply due prior activation decisions, and apply approved governance outcomes before affected scheduled work. Reports/cancellations/replacements accepted from this block's ordered transition sequence become eligible for lifecycle decisions at the next block boundary. This prevents scheduled execution from depending on a report appearing later in the same block. The exact mapping onto existing ABCI event order is a reviewable proposal and must pass upgrade/order vectors before adoption.

At the first boundary that validates a threshold crossing, let `T = crossing_time - accepted_deployment_time`. Set `wait = min(max(T, 120 seconds), 3600 seconds)` and `deadline = crossing_time + wait`. Activate at the first eligible block boundary whose consensus time is at least that deadline. There is no second quorum gate at the deadline and later membership changes do not restart an established timer. New nodes prepare to follow the active state. A replacement or authorized cancellation processed before activation removes the old pending deadline; a transaction processed after a boundary cannot retroactively cancel activation at that boundary.

This is an additional wait equal to the time taken to reach 80%, bounded between two minutes and one hour. It is not an extra wait of 2T. Empty membership never approves; withholding readiness can leave a candidate pending indefinitely. No below-threshold fallback is allowed.

### Version selection

Activation atomically installs the complete bundle and latest public routing. Cross-contract calls and scheduled calls resolve stable method IDs on the latest version visible at their ordered execution point; no older-version fallback. A direct user may explicitly request a still-supported older version. With no direct selection, use latest. Missing methods return a structured failure under DVM-06/08.

An authorized update can declare deprecation, warning/notice commitments and later unsupported status. Deprecation is a warning state, not rejection. A promised notice interval cannot be shortened by a later update. A newer active version does not itself make older versions unsupported. Once unsupported, new direct calls cannot select that version, but its canonical code remains. Supported older code never restores older schema/index permissions or obsolete authorization. Freeze is contract-wide; updates while network-frozen do not unfreeze execution. Wipe cannot be undone by activating a retained blob.

## Backward compatibility and node operation

Preparation on restart, cache loss and upgrades uses permanent canonical state and historical profiles. A node without a compatible compiled artifact is locally unready; it must not reject a consensus-valid call, charge a cold-cache surcharge or use another backend's behavior. Readiness is an availability mechanism, not a proof that compiled output is correct. Report transport, catch-up and membership-key upgrades are implementation work.

## Security considerations

Bind report signatures to exact rounds and profiles; count identities rather than messages. Bound repeated validation and membership work without allowing an unverified tally. Deployment fees cover specified validation/report verification, while operators pay local compilation. Timer overflow, membership churn, abandoned candidates and compilation storms require adversarial tests. The protocol deliberately trades pending-deployment liveness for the selected 80% condition.

## Test vectors

For N=5, Y=3 fails and Y=4 passes; N=400 requires 320; N=0 always fails. Duplicate, removed and wrong-round voters never inflate Y. If T is 30 seconds, wait is 120; T=600 gives wait=600; T=7200 gives wait=3600. Test exact deadline, no block exactly at deadline, membership-only crossing, churn during paged checking, cancellation/replacement on each phase boundary, old/latest routing, frozen update, code retention and all cache states. The phase table must have golden beginning/end-of-block cases.

## Reference implementation, rationale and open allocations

ABCI owns membership/report scheduling and activation phases; DPP owns messages; Drive owns version/round/vote records; DashVM owns compilation. DVM-04 specifies paths. Exact codecs, report signature/key reuse, active predicate binding and event-phase wiring remain registry entries. The proposed phase convention and support metadata are fleshed-out engineering drafts, not claims of additional owner approval.

## Related drafts and implementation tracking

[DVM-01](dip-dashvm-protocol.md) · [DVM-02](dip-dashvm-engine-abi.md) · [DVM-04](dip-dashvm-storage.md) · [DVM-05](dip-dashvm-guards.md) · [DVM-06](dip-dashvm-execution.md) · [DVM-07](dip-dashvm-fees.md) · [DVM-08](dip-dashvm-scheduling.md) · [DVM-09](dip-dashvm-governance.md) · [DVM-10](dip-dashvm-proofs-clients.md) · [DVM-11](dip-dashvm-rust-sdk.md) · [DVM-12](dip-dashvm-external-primitives.md)

* [50-DEPLOY](https://github.com/dashpay/platform/issues/4684): Implement permanent bundles, registration, readiness and version routing (5.0-dev).
* [50-CLIENTS](https://github.com/dashpay/platform/issues/4693): Deliver DAPI, Rust, Wasm/JS and mobile parity (5.0-dev).
* [50-GOV](https://github.com/dashpay/platform/issues/4695): Implement governance, bounded wipes and vestige recovery (5.0-dev).

[Complete storage mapping](https://github.com/dashpay/platform/issues/4626#issuecomment-5634141255) · [Capability catalogue and current amendments](https://github.com/dashpay/platform/issues/4626#issuecomment-5636957194) · [Module architecture](https://github.com/dashpay/platform/issues/4626#issuecomment-5636536959) · [Owner decisions and provisional limits](https://github.com/dashpay/platform/issues/4626#issuecomment-5583771268). These linked appendices retain their stated confirmed/proposed status.

## Copyright

This working proposal is released under the MIT License, following the default license of the Dash DIPs repository.
