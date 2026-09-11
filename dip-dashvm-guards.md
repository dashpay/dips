<pre>
  DIP: Unassigned (dip-dashvm-guards)
  Title: Bounded guards and native action rules
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

Define a small typed, bounded native expression guard and the context shared with read-only Wasm predicates. Both enforce ordinary document actions through native validation; neither can interfere with a native contested-index award. The grammar below is a concrete engineering proposal for review, not a previously approved language.

## Motivation

Simple rules such as immutable ownership, monotonic scores and permitted updates should not require compiling an entire Wasm program. More complex rules can use metered Wasm predicates while sharing the same target binding, current-state visibility and atomic failure behavior.

## Specification

### Proposed typed expression model

Persist a canonical versioned AST, not Rust source or an arbitrary expression string. Initial nodes are `Literal`, `Field(context,path)`, `Exists`, `IsNull`, `Eq`, `Ne`, ordered comparisons, checked integer `Add/Sub/Mul`, `And`, `Or`, `Not` and `If`. No loops, recursion, dynamic code, unbounded regex, dynamic field traversal or ambient time/entropy are admitted. Explicit bounded byte/string equality and length operations may be added only with type and cost vectors. Floating-point expression arithmetic is excluded from this initial guard proposal without removing scalar floats from the Wasm profile.

Nodes carry typed operands. There is no implicit signed/unsigned, string/number or null/missing coercion. Field paths are validated against the declared schema, with bounded depth and stable serialized property identity. `Missing`, `Null` and a present value are distinct. `Exists` handles missing; an inappropriate operand otherwise produces a typed guard error. Integers use schema-declared widths; overflow is an error, not wraparound. Comparisons require matching ordered types; bytes/strings use the canonical native ordering, not a locale. Final result must be Boolean.

Evaluation order is left to right. `And`/`Or` short circuit and `If` evaluates one selected branch. Static admission computes a sound maximum over reachable alternatives and operation/byte bounds; actual charging follows evaluated work. Do not invoke an unbounded query from an AST node. Add future read expressions only with typed capability, range and cost limits under a new grammar generation. Wasm predicates may perform the explicitly permitted bounded reads under DVM-02/06.

### Action context and old/new binding

The host constructs `ActionContext{contract, document_type, document_id, action, signer, caller, native_origin, policy_generation}`. `old` is the actual target record immediately before this operation in accepted order, including this transition's earlier operations. `new` is the complete native-validated candidate for that same target. Create has no old record; delete has no new record. Reject ID/type substitution and forged old snapshots. Fields such as owner, revision and storage flags remain host/native-controlled.

Proposed first action scopes are ordinary create, replace/update and delete plus separately enumerated native actions where the existing contract model supports rules. No generic wildcard that silently covers every future action is accepted. Native triggers, index maintenance and cascades retain their native authorization; specify whether each derived action invokes an ordinary rule through the capability/action matrix. The rule must never recursively authorize itself.

### Native contested awards

Award origin is an unforgeable internal native action. Existing contested-index eligibility, locks, tally, finalization, document validation and atomic index effects govern it. Contracts may declare validated supported parameters. Guest callbacks, Wasm predicates and the native generic guard evaluator are not invoked to approve, reject, delay, redirect or retry an award. Reject declarations that claim that scope. Ordinary guarded writes remain guarded. Freeze/wipe handling belongs to deterministic native lifecycle rules, never a contract veto over a poll outcome.

### Registration, updates and legacy data

Validate AST types, action scopes, maximum cost and supported generations during contract registration/update. Rule declarations are part of the signed schema/manifest. A direct call to a supported older module does not select stale authorization. Proposed guard update policy: current accepted rules apply prospectively to ordinary actions on all existing documents, with `old` decoded using its stored native format and `new` validated under current applicable native schema. Existing documents are not eagerly rewritten. Native contract-update validation must reject incompatible changes.

If a promised rule policy requires creation-time applicability, represent it explicitly through a versioned native stamp with a defined legacy fallback; do not infer a stamp from code version or silently assign one. Such an extension is not activated until its encoding and old-document/deletion vectors are complete. Protected deletion remains enforced on the actual stored target. This avoids inventing a blanket migration or bypass for legacy documents.

### Execution and failures

Check full affordability before evaluating guards. CheckTx/RecheckTx type-check declarations and bounds but do not evaluate user guards. Freeze rejects affected ordinary execution; skipping a frozen guard must never permit its write. A false result, evaluation error, Wasm trap or native rule rejection fails the outer invocation under DVM-06/07, even if guest code catches a returned error. Read-only predicates cannot mutate state, create schedules or reenter an active contract through nested execution. Dependencies and costs are revalidated before accepting speculative results.

## Backward compatibility and deployment

Introduce new schema/evaluator generations only through the central profile. Old unguarded contracts retain their historical behavior; guard installation is an authorized native-compatible update, not an automatic protocol migration. Target 5.0-dev in the current release allocation. No separate early guard activation is assigned by this draft.

## Security considerations

AST depth, operator count, value expansion and comparison bytes are bounded before execution. Host-supplied old/new binding prevents validating one record and writing another. Native validation remains mandatory for handcrafted Wasm and clients that bypass generated SDK checks. Contract-only write permission and ACL authorization are independent of Rust method visibility.

## Test vectors

Test `Missing` versus `Null`, checked overflow, short-circuit costs, maximum depth and one over, invalid types/paths, create/delete absence, two writes to one record, changed predecessor data, failed outer rollback and cross-architecture equality. Award vectors must prove that even trap/false/infinite-loop guest guards are never invoked for native awards. Include freeze, legacy records, current-rule updates and protected deletion.

## Reference implementation, rationale and open allocations

DPP owns AST/declarations/type validation; a bounded native evaluator and rs-drive-contracts supply execution context; Drive owns action validation and writes. SDK macros emit the canonical rule model. Exact opcode tags, error IDs, initial supported operations, legacy applicability and costs are review entries. A small typed AST was chosen over unrestricted scripting to support sound admission bounds and stable cross-language serialization.

## Related drafts and implementation tracking

[DVM-01](dip-dashvm-protocol.md) · [DVM-02](dip-dashvm-engine-abi.md) · [DVM-03](dip-dashvm-activation.md) · [DVM-04](dip-dashvm-storage.md) · [DVM-06](dip-dashvm-execution.md) · [DVM-07](dip-dashvm-fees.md) · [DVM-08](dip-dashvm-scheduling.md) · [DVM-09](dip-dashvm-governance.md) · [DVM-10](dip-dashvm-proofs-clients.md) · [DVM-11](dip-dashvm-rust-sdk.md) · [DVM-12](dip-dashvm-external-primitives.md)

* [44-AUTHOR](https://github.com/dashpay/platform/issues/4680): Settle contract declarations and the Rust author API (4.4-dev).
* [50-GUARDS](https://github.com/dashpay/platform/issues/4685): Implement native guards and preserve contested-index awards (5.0-dev).
* [50-NATIVE](https://github.com/dashpay/platform/issues/4690): Implement the full native capability and collection adapters (5.0-dev).

[Complete storage mapping](https://github.com/dashpay/platform/issues/4626#issuecomment-5634141255) · [Capability catalogue and current amendments](https://github.com/dashpay/platform/issues/4626#issuecomment-5636957194) · [Module architecture](https://github.com/dashpay/platform/issues/4626#issuecomment-5636536959) · [Owner decisions and provisional limits](https://github.com/dashpay/platform/issues/4626#issuecomment-5583771268). These linked appendices retain their stated confirmed/proposed status.

## Copyright

This working proposal is released under the MIT License, following the default license of the Dash DIPs repository.
