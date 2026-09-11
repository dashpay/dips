<pre>
  DIP: Unassigned (dip-dashvm-proofs-clients)
  Title: Current-state proofs and client results
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

Extend native queries and proof verification for smart-contract manifests, current lifecycle, balances, specialized collections, schedules and retained receipts. Clearly distinguish a proven current-state fact, an accepted stored receipt and unproven execution-result text. No past-height proof service or network preflight is added in 5.0.

## Motivation

Application developers need consistent data and errors across Rust, Wasm/JavaScript and mobile clients. A contract result must not be advertised as a proof of execution merely because the same response includes a valid state proof.

## Specification

### Query families

Provide bounded native requests for contract kind/current metadata, latest/pending/supported versions, immutable manifest/module bytes and routes, readiness progress, freeze/wipe/custody, credit/token buckets, declared document/collection queries, job status and retained receipts. Reuse existing native range, projection, paging and element decoding. Capability-specific query combinations are enabled only where native semantics and proof verification are defined.

Every request binds contract/resource identity, supported query generation, selectors/limits and relevant method/schema/collection IDs. Canonical paging cursors bind the query and ordering, not a raw host path. Enforce native smaller limits even if the general guest cap is larger. Bound scanned work and encoded bytes separately; partial results explicitly indicate limits/continuation. Missing records and unavailable capabilities use distinct typed results.

### Proof verification contract

A verified result is bound to the trusted Platform state root and the complete expected path/query. Verify parent/ancestor paths, Element types, field projections, inclusion/absence, query order, range boundaries and limit semantics through existing Drive proof verification. A valid proof for another contract/version/query/root is not interchangeable. Protocol/codec IDs select the expected verifier; unknown variants fail closed.

To prove a module, bind contract, version manifest, module name/hash and exact requested bytes. Retained unsupported/cancelled/wiped code can still be proven in current state because its archive is permanent. That is not a proof of what the state was at its original deployment height. A latest-route proof must include lifecycle/routing state, not merely one older immutable manifest.

For ordinary SumTree aggregate balances, authenticate the parent Element carrying the aggregate and its full path to the trusted root; a bare child Merk hash does not authenticate arbitrary internal sum metadata. Range-sum proof interfaces use the appropriate supported provable structure. Live balance/token results must include or otherwise authenticate relevant wipe/issuer exclusion/custody facts. Old retained physical holdings after logical wipe cannot be presented as spendable balances.

### Results and receipts

Expose `ExecutionOutcome`, optional `StoredReceipt`, and optional `VerifiedStateResult` as distinct result types. Outcomes have stable bounded success/error data and actual fees. A proof of a retained receipt proves that the current state contains that outcome record under its key; it is not a zero-knowledge execution proof or arbitrary historical-state proof. Receipt absence can reflect configured omission or expired retention; clients must not equate it with a failed call. Show effective policy/status when needed to interpret it.

Readiness status must distinguish raw reported count, membership-validated tally, pending verification, established deadline and activated state. UI estimates cannot replace consensus activation. Show deprecation as a warning, unsupported as unavailable for new direct calls, and frozen/wiped as separate contract lifecycle conditions. Cross-contract/scheduled APIs expose latest-method routing; only direct-call APIs offer supported-version selection.

### Transport and cross-language parity

Use DAPI/protobuf versions only where needed; keep existing proof/result APIs where compatible. Apply code upload and response bounds consistently across gRPC, mempool/block transport, native/Wasm decoders and mobile wrappers. Keep one canonical vector corpus for schemas, method calls, values including explicit floating-point representations, errors, proofs and fee estimates. Do not allow JSON to silently round large integers or collapse required tagged values.

Rust SDK, Wasm SDK/JavaScript and Swift/Kotlin wrappers must preserve optional version/receipt/policy fields and structured errors in persistent application models. CLI/local fixture simulation is permitted, but no client method should imply an unavailable network preflight service. Downloaded native compiled artifacts are not a client-trusted substitute for canonical code/proofs.

## Backward compatibility and deployment

New query/proof variants use allocated protocol versions and old clients receive explicit unsupported errors rather than misdecoding Elements. Test saved pre-upgrade records, post-upgrade sync, historical code in current state and shared native query behavior. Existing data-contract queries remain valid.

## Security considerations

Prevent wrong-root/path substitution, misleading aggregate interpretation, pagination omission, invalid absence proofs and unproven metadata attached to proven records. Private Rust fields and ACL-restricted queries do not imply encrypted state. Proof-visible data is governed by the actual native capability, not UI labels.

## Test vectors and reference implementation

Include valid and tampered proofs for every enabled projection/tree family, wrong contract/version/root, missing/latest versus pending route, empty/limited pages, ordinary versus provable sums, wiped/destroyed-token holdings, receipt off/expired/retained and large value boundaries. Cross-language converters must produce identical verified semantics and reject the same malformed vectors. Drive/DAPI own query services; rs-drive-proof-verifier owns verification; rs-sdk/wasm-sdk/mobile layers expose it. The capability appendix identifies unsupported/private interfaces whose proof contract must be completed before enabling.

## Rationale and open allocations

Typed result separation prevents overclaiming proofs. Reusing native query/proof machinery preserves established indexing and verification semantics. Exact protobuf/query IDs, proof/result compatibility entries, paging codecs and private-store exposure remain tracked allocations; arbitrary historical proof endpoints remain out of scope.

## Related drafts and implementation tracking

[DVM-01](dip-dashvm-protocol.md) · [DVM-02](dip-dashvm-engine-abi.md) · [DVM-03](dip-dashvm-activation.md) · [DVM-04](dip-dashvm-storage.md) · [DVM-05](dip-dashvm-guards.md) · [DVM-06](dip-dashvm-execution.md) · [DVM-07](dip-dashvm-fees.md) · [DVM-08](dip-dashvm-scheduling.md) · [DVM-09](dip-dashvm-governance.md) · [DVM-11](dip-dashvm-rust-sdk.md) · [DVM-12](dip-dashvm-external-primitives.md)

* [44-GROVE](https://github.com/dashpay/platform/issues/4678): Adopt the reviewed GroveDB foundation (4.4-dev).
* [50-READS](https://github.com/dashpay/platform/issues/4686): Implement bounded current-state guest reads (5.0-dev).
* [50-PROOFS](https://github.com/dashpay/platform/issues/4692): Implement current-root queries and proof verification (5.0-dev).
* [50-CLIENTS](https://github.com/dashpay/platform/issues/4693): Deliver DAPI, Rust, Wasm/JS and mobile parity (5.0-dev).
* [50-VERIFY](https://github.com/dashpay/platform/issues/4696): Complete upgrade, sync, recovery and release evidence (5.0-dev).

[Complete storage mapping](https://github.com/dashpay/platform/issues/4626#issuecomment-5634141255) · [Capability catalogue and current amendments](https://github.com/dashpay/platform/issues/4626#issuecomment-5636957194) · [Module architecture](https://github.com/dashpay/platform/issues/4626#issuecomment-5636536959) · [Owner decisions and provisional limits](https://github.com/dashpay/platform/issues/4626#issuecomment-5583771268). These linked appendices retain their stated confirmed/proposed status.

## Copyright

This working proposal is released under the MIT License, following the default license of the Dash DIPs repository.
