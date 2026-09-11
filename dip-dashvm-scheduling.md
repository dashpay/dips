<pre>
  DIP: Unassigned (dip-dashvm-scheduling)
  Title: Time-based scheduled calls
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

Schedule bounded contract calls using agreed consensus time, latest method routing, live execution payment and prepaid removal in the existing prefunded balance ledger. Separate actual scheduled failure policy from free internal speculative retries.

## Motivation

Contracts need recurring and delayed work without prepaying every future execution. A job must remain removable when operating funds run out, and deterministic ordering and bounded backlog handling must prevent timer storms from consuming a block.

## Specification

### Job record and registration

Store `Job{id, owner_contract, target_contract, stable_method, arguments, authority, live_payer, cancel_authority, next_due_time, recurrence, failure_policy, occurrence, attempt, removal_balance_id}`. The canonical schema also binds creation/profile facts and ownership/refund context. Time-based triggers are the only supported triggers; reject height/epoch trigger variants and create no placeholder queues. Do not store an old target executable version.

Registration validates caller/target authority, permitted payer, argument and timing bounds, cancellation policy and removal affordability. Atomically debit the real funder into the existing `40/128` prefunded balance, write purpose/owner metadata, primary job and one due-time locator. New purpose IDs are domain-separated and cannot impersonate legacy vote funding. A job cannot fund itself from an unrelated reserve supplied by guest input.

### Processing order — proposed engineering convention

After agreed membership, due lifecycle and approved governance effects, process eligible jobs before ordinary user transitions in the block's existing scheduled-event integration point. Wire this exact phase into both proposal paths. Ordered due keys are `(consensus_due_time, contract_id, job_id, occurrence)` with explicit canonical encodings; never use a wall clock or database iteration order outside that key order. A job created by an ordinary transition becomes eligible no earlier than a later scheduled phase.

Process bounded work and obey the contract-computation budget plus existing native event constraints. Stop deterministically at the selected bound and retain backlog. Do not admit an invocation if its required bound cannot fit the remaining permitted computation. Skipping for block capacity is not a paid attempt. Native queue bookkeeping has its own bounded work/cost specification; it must not become the rejected combined execution budget.

### Attempt state machine

For each eligible occurrence, resolve the latest target method and lifecycle at its accepted position. Frozen executing contracts pause; no guest code runs. On unfreeze advance to an eligible future run under the recurrence convention rather than replaying every missed occurrence. Proposed permanently missing method/unsupported target outcome is terminal removal using its reserve, with a structured reason. This terminal policy is an engineering proposal, explicitly tested with method removal/version updates.

Check live affordability before each real execution attempt. The first inability to pay removes the job using its prepaid removal funds, regardless of the declared execution-failure policy. It does not run the guest to discover failure. Otherwise invoke through the shared outer scope and settle once. Internal parallel retries do not increment attempts or create extra fees/receipts.

Require explicit `Drop`, `Skip`, or `Retry{max_attempts, interval, then}`. Drop removes the job. Skip advances a recurring job to its next normal occurrence; a one-shot completes. Retry preserves the current occurrence, schedules one later eligible attempt and cannot overlap itself. After its bounded attempts, `then` is Drop or Skip. The current starting proposal is at most ten total attempts with at least one later block between them; it remains a measured protocol allocation, not a confirmed production cap.

Proposed recurrence convention: keep a fixed time anchor and positive period, selecting the smallest anchor-plus-period multiple strictly after the accepted processing time when advancing. Use checked arithmetic; overflow produces a defined terminal outcome. Never burst through missed times. A retry has a due time no earlier than the accepted failure time plus its declared interval and is ineligible in that same block even if time encoding rounds down.

### Cancellation, freeze and wipe

Each job declares who can cancel. Native cancellation checks current authority, removes the job/due index, charges bounded removal and refunds remaining prefunds to their recorded owner. If that owner is wiped, route to the current processing pool. Another funder's ownership remains intact. Cancellation/removal/retry index changes and settlement are atomic and idempotent.

Network freeze cannot be bypassed by a scheduled invocation. Permitted native inbound funds/refunds to frozen recipients do not execute a guest callback; a required unavailable callback cannot be treated as successful authorization. Wipe disables execution immediately and schedules bounded native job removal. Old retained code does not revive jobs. Fee upgrades must maintain prepaid removal or settle affected jobs before an incompatible change.

## Backward compatibility and deployment

Extend the existing native scheduled-event pipeline and prefunded helpers; retain old voting IDs and purpose behavior. No jobs_due_height/jobs_due_epoch or new monetary reserve root is introduced. New job formats and clocks are protocol-versioned; historical fee context survives restarts and upgrades.

## Security considerations

Bound due scans, arguments, retries, recurrence overflow and cleanup work. Prevent same-block retry storms and duplicate settlement across crashes. A genuine scheduled host/storage fault is not a paid guest failure: the normal protocol-upgrade recovery policy remains, including its known possibility of a halt that cannot be fixed by simply dropping an ordinary transaction.

## Test vectors

Cover equal due times, one-shot/recurring success, each failure policy, first lack of funds, unpayable future fee changes, cancellation rights, empty live balance with funded removal, frozen pause/resume, missing latest method, wipe, foreign refund owner, crash between cleanup steps and scheduled-only epoch-boundary blocks. Compare proposer/validator and serial/parallel roots, queue contents, attempts, fees and receipts. Exact phase and recurrence boundary vectors are required before enabling.

## Reference implementation and rationale

Drive owns primary jobs/due indexes/prefund operations; rs-drive-contracts owns invocation adaptation; ABCI owns ordered bounded dispatch and commit; SDKs expose time-only builders and structured status. Live payment avoids locking the cost of an indefinite future schedule; prepaid removal ensures deterministic cleanup even after the live payer is exhausted.

## Related drafts and implementation tracking

[DVM-01](dip-dashvm-protocol.md) · [DVM-02](dip-dashvm-engine-abi.md) · [DVM-03](dip-dashvm-activation.md) · [DVM-04](dip-dashvm-storage.md) · [DVM-05](dip-dashvm-guards.md) · [DVM-06](dip-dashvm-execution.md) · [DVM-07](dip-dashvm-fees.md) · [DVM-09](dip-dashvm-governance.md) · [DVM-10](dip-dashvm-proofs-clients.md) · [DVM-11](dip-dashvm-rust-sdk.md) · [DVM-12](dip-dashvm-external-primitives.md)

* [50-SCHEDULE](https://github.com/dashpay/platform/issues/4688): Implement time-only live-paid schedules and removal settlement (5.0-dev).

[Complete storage mapping](https://github.com/dashpay/platform/issues/4626#issuecomment-5634141255) · [Capability catalogue and current amendments](https://github.com/dashpay/platform/issues/4626#issuecomment-5636957194) · [Module architecture](https://github.com/dashpay/platform/issues/4626#issuecomment-5636536959) · [Owner decisions and provisional limits](https://github.com/dashpay/platform/issues/4626#issuecomment-5583771268). These linked appendices retain their stated confirmed/proposed status.

## Copyright

This working proposal is released under the MIT License, following the default license of the Dash DIPs repository.
