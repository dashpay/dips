<pre>
  DIP: Unassigned (dip-dashvm-protocol)
  Title: Protocol integration and wire contracts
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

Introduce smart contracts as a protocol-versioned extension of Platform data contracts. Define the boundary between accepted wire messages, native validation, execution and persistent outcomes. DVM-02 through DVM-12 own the detailed runtime, lifecycle, storage, calls, fees and developer rules. This draft owns their shared envelope and activation contract.

## Motivation and scope

Existing documents, indexes, identities and tokens already have native rules. Executable contracts must compose with those rules and the existing nonce and fee pipeline. They must not create an alternative database, a second token ledger, or an execution path that changes when an operator changes a local setting. Smart execution targets 5.0-dev; earlier preparation does not enable it.

## Specification

### Protocol profile

Every consensus entry point resolves one immutable `PlatformVersion` profile from the active protocol version. Its DashVM descriptor references exact model/serialization generations, admitted Wasm features, validation/preparation generation, engine behavior, ABI, capability catalogue, guard grammar, metering/fee tables, storage codecs, error taxonomy and resource limits. These are independently identified components of one approved profile, not independent node configuration switches. Historical blocks resolve their historical descriptor.

Unknown profile or required capability is rejected before execution. Software-only changes may replace an engine build only with evidence that consensus-visible results, fees, limits, traps and roots are equivalent. A behavior change uses the normal protocol-upgrade mechanism. No new emergency pause, deployer allowlist, audit approval or funding gate is introduced.

### Semantic wire schemas

The following are semantic records, not final field numbers. Their concrete encoding must reuse DPP/platform serialization and the central allocation register.

| Record | Required signed/bound fields |
| --- | --- |
| Create/update smart contract | Native contract identity/authority/revision fields; contract kind; executable version; ABI/profile declarations; module bundle manifest; new canonical blobs; existing-blob references; methods/capabilities; update/freeze/receipt policy; native schemas; fee bound; applicable native nonce |
| Invoke | Contract ID; stable public method ID; optional supported version for a direct caller; canonical arguments; declared rights/read bounds; payment source and maximum charge; applicable native nonce and signer |
| Readiness report | Network domain; evonode identity; contract/version; activation round; manifest hash; preparation/engine profile; authenticated ready statement |
| Cancel/replace pending version | Contract and expected pending round/version; update authority; replacement if any; native nonce/fee context |
| Governance vote | Network domain; proposal ID; exact action/target/payload digest; voting identity and authenticated choice |
| Schedule create/cancel | Job identity; target method; canonical arguments; time policy; payer/cancellation authority; failure policy; prefunded-removal purpose; nonce and fee context |

Identity authentication and replay handling build on DIP-0011 and DIP-0030. Do not replace their nonce-window algorithm with a new sequential nonce. Proposed allocation: creation uses the existing identity nonce; updates and direct contract calls use the signer/contract nonce domain where applicable; reports/votes use their domain-bound idempotent report/proposal keys plus their native authenticated transport. Exact transition-family assignment and paid-failure nonce mappings are allocation work, with signed-byte vectors required before enabling them. Unknown fields/variants, duplicate map keys, noncanonical ordering or integer overflow cannot acquire alternate valid interpretations.

### Admission and execution phases

1. Enforce the outer message-family size cap before allocating large buffers, decompressing or decoding all code. Bound nested lengths and total manifest/blob bytes; referenced existing blobs still count toward complete-bundle limits.
2. Decode canonically; check supported protocol and message type, signature, native authority, nonce, schema and declarations. Hash every newly supplied blob and bind its exact bytes to the manifest.
3. Compute a sound full affordability bound from declared limits and native cost rules. Check current permitted payment sources. CheckTx/RecheckTx perform these structural and affordability checks without guest execution, including native expression guards.
4. During ordered block execution, revalidate against the current accepted state prefix. Apply lifecycle checks, reserve the sound bound and execute through the shared service. No client preflight endpoint is added in 5.0.
5. Accept exactly the outcome and settlement prescribed by DVM-06/07. Only Drive ABCI commits the final block transaction. Rejected speculative attempts never become independent paid invocations.

Both proposal construction and proposal validation use the same semantics. Local worker count, cache size, compilation time, OS clock and memory pressure cannot change a valid block's result. Existing native event budgeting remains; only the specified additional contract-computation budget is introduced.

### Error contract

Allocate symbolic families `Malformed`, `UnsupportedProfile`, `Unauthorized`, `NonceInvalid`, `InsufficientBound`, `InactiveVersion`, `Frozen`, `GuestRejected`, `GuestTrap`, `ResourceExceeded`, `NativeActionFailed` and `NodeFault`. Stable structured details are bounded and exclude OS strings/backtraces. A semantic read result such as absence, or a randomness `NotReady` variant, is not automatically an execution failure. Actual nested execution or action-validation failures poison the outer invocation. Genuine storage/runtime infrastructure faults do not get converted into paid guest errors merely to keep a node running.

## Backward compatibility and deployment

Data-only contracts retain their existing representation and native behavior; smart namespace insertion is specified in DVM-04. Unsupported transitions are rejected before the corresponding protocol feature activates. Release branch names 4.3-dev/4.4-dev/5.0-dev are engineering destinations, not assigned protocol numbers. The existing plan's PV15–PV17 budget must be reconciled with real version registries; this draft does not invent three required activations.

## Security considerations

Sign the entire execution intent, network and payment bound; never let an unsigned module route, recipient or delegated right alter it. Decode with checked arithmetic and bounded expansion. Recheck authority and nonces against accepted predecessor state, including shared signers used by multiple transitions. No CheckTx execution means admission is not a promise of later success.

## Test vectors and acceptance

Require byte vectors for every envelope, signature/hash domain, empty/duplicate/unknown fields, maximum lengths and one byte over each bound. Exercise duplicate nonces, paid failures, changed balances between CheckTx and execution, pre-activation rejection and historical decoding. Compare both proposal paths, serial/parallel execution and supported architectures. These are required vectors, not tests claimed to have passed.

## Reference implementation and open allocations

Models: rs-dpp; profile: rs-platform-version; encoding: rs-platform-serialization/value and rs-dashvm-abi; orchestration: rs-drive-abci; execution adapter: rs-drive-contracts. The shared allocation register owns exact profile, message/error/field IDs, nonce-family mappings, hash encodings and production limits. Drafting does not close those implementation tasks.

## Rationale and alternatives

One versioned descriptor prevents partially upgraded nodes from selecting incompatible pieces. Native nonces and validation preserve existing replay protection. Running contracts in CheckTx was rejected because it repeats expensive execution against state that may change. Per-node execution limits and a second storage/index engine were rejected because they break deterministic behavior or duplicate existing guarantees.

## Related drafts and implementation tracking

[DVM-02](dip-dashvm-engine-abi.md) · [DVM-03](dip-dashvm-activation.md) · [DVM-04](dip-dashvm-storage.md) · [DVM-05](dip-dashvm-guards.md) · [DVM-06](dip-dashvm-execution.md) · [DVM-07](dip-dashvm-fees.md) · [DVM-08](dip-dashvm-scheduling.md) · [DVM-09](dip-dashvm-governance.md) · [DVM-10](dip-dashvm-proofs-clients.md) · [DVM-11](dip-dashvm-rust-sdk.md) · [DVM-12](dip-dashvm-external-primitives.md)

* [43-PLAN](https://github.com/dashpay/platform/issues/4676): Establish specifications and implementation tracking (4.3-dev).
* [44-CODEC](https://github.com/dashpay/platform/issues/4679): Extract the shared guest value and codec foundation (4.4-dev).
* [50-DEPLOY](https://github.com/dashpay/platform/issues/4684): Implement permanent bundles, registration, readiness and version routing (5.0-dev).
* [50-CALLS](https://github.com/dashpay/platform/issues/4687): Implement atomic calls, delegation and ordered parallel execution (5.0-dev).
* [50-FEES](https://github.com/dashpay/platform/issues/4689): Implement contract bounds, actual charging, receipts and historical refunds (5.0-dev).
* [50-CLIENTS](https://github.com/dashpay/platform/issues/4693): Deliver DAPI, Rust, Wasm/JS and mobile parity (5.0-dev).
* [50-VERIFY](https://github.com/dashpay/platform/issues/4696): Complete upgrade, sync, recovery and release evidence (5.0-dev).
* [50-DOCS](https://github.com/dashpay/platform/issues/4697): Maintain public documentation and protocol-change checklist (5.0-dev).

[Complete storage mapping](https://github.com/dashpay/platform/issues/4626#issuecomment-5634141255) · [Capability catalogue and current amendments](https://github.com/dashpay/platform/issues/4626#issuecomment-5636957194) · [Module architecture](https://github.com/dashpay/platform/issues/4626#issuecomment-5636536959) · [Owner decisions and provisional limits](https://github.com/dashpay/platform/issues/4626#issuecomment-5583771268). These linked appendices retain their stated confirmed/proposed status.

Related native specifications: [DIP-0011 identities](https://github.com/dashpay/dips/blob/master/dip-0011.md), [DIP-0030 nonces](https://github.com/dashpay/dips/blob/master/dip-0030.md).

## Copyright

This working proposal is released under the MIT License, following the default license of the Dash DIPs repository.
