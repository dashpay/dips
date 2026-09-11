<pre>
  DIP: Unassigned (dip-dashvm-external-primitives)
  Title: ACL and randomness integration boundaries
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

Define the contract-facing requirements for separately implemented native ACL and randomness primitives, their fail-closed stubs and activation gates. This draft specifies integration; it does not choose an unreviewed ACL policy engine or cryptographic randomness construction for those external projects.

## Motivation

Contract developers should be able to depend on native authorization and finalized randomness without importing them as guest libraries. Their delivery must appear in the dependency graph and release tracking even while the contract project provides only stubs.

## Specification

### Capability lifecycle

Declare exact required capability/generation in the bundle. Until the native implementation and validated host adapter are active in the protocol profile, a requiring contract cannot become executable. SDK presence or an operator flag is not activation. Registration may retain a structurally valid pending artifact only if the deployment policy explicitly supports it; it cannot bypass unsupported-capability admission or falsely report executable readiness.

Production stubs return a stable `CapabilityUnavailable` error and never allow authorization or provide entropy. Test-only fixtures have an explicit test feature/provider and must not link into the production profile. Pending randomness is a distinct successful `NotReady` result, not the same as an unavailable primitive or failed host call.

### ACL semantic interface

`require(Resource, Action)` receives authentic host signer/caller/executing-contract context and the current native policy/membership state. The resource names a declared contract/document/collection/asset scope, not a raw GroveDB path. Success grants only that requested operation under current native rights; denied authorization is an actual failure that poisons the outer invocation. Optional non-authorizing inspection/query methods must have distinct semantics so a Boolean check cannot be mistaken for enforcement.

Delegation is explicit and bounded by the delegator's rights. Policy updates/revocation, group membership and applicable revision are current-state observations for conflict validation. A cached allow decision cannot survive a changed predecessor policy. Host enforcement remains mandatory for handwritten Wasm and native effects; guest assertions do not create rights. Native contested-index awards remain outside custom ACL/guest veto scopes and preserve their protocol-defined native checks.

The external ACL project must specify subjects/resources/actions, inheritance and precedence, ownership/update authority, group semantics, revocation timing, delegation limits, default deny, costs, bounded evaluation, codecs, proof exposure and upgrade behavior. It must use native reusable storage/validation and pass its own conformance vectors. Contract integration cannot fill these gaps with an allow-all mock. ACL restrictions are not encryption or protection from reading public state through another route.

### Randomness semantic interface

`request(domain, application_binding)` creates a native request ID bound to network, contract, invocation/request nonce, purpose, profile and the fixed application intent. It must select a future source/round according to the native primitive so the result is not already knowable when the relevant application commitments are accepted. `get(request_id)` returns `NotReady` until the selected result is finalized, then a fixed `Ready{value, source_reference}` under the authorized native result contract. Repeated reads return the same result; a guest cannot substitute another source or resample the same intent after seeing an unfavorable result.

The native primitive owns unpredictability, bias/withholding resistance, proof verification, finality and source selection. The host validates request ownership/binding, costs and current finalized result and records dependencies. Request creation and related application commitments are atomic. Consumers must fix participants/stakes before the result can be known and handle delayed/unavailable completion; the VM cannot enforce an application's fairness merely by returning random bytes.

No immediate host entropy, timestamp/hash-of-current-block shortcut, insecure seed or automatic fallback is allowed. Node-local RNG cannot enter consensus. A pending result is ordinary control flow and may return successful `Pending` without poisoning the invocation. Genuine request/authorization/proof failures remain errors.

The external randomness project must specify cryptographic source, future-round selection, domain/hash encoding, adversary assumptions, reorg/finality behavior, withholding/timeout policy, result uniqueness, costs/storage/retention, proof exposure and upgrade/replay behavior. DIP-0029 concerns randomness for LLMQ selection; it is related work, not evidence that Platform already has this application request/result primitive or that its exact construction is selected here.

### Delivery and activation

EXT-ACL targets 4.3-dev and EXT-RNG targets 4.4-dev as separate native projects. STUB-ACL/STUB-RNG and INT-ACL/INT-RNG remain tracked 5.0 contract integration work. Early native delivery does not require DashVM or activate smart contracts. Conversely, the presence of a stub does not complete the native task. Integration activation requires the real native implementation, current version/capability gate, matching ABI/client vectors and bounded fees/proofs/lifecycle handling.

## Backward compatibility and security

Unknown capability generations fail closed. Preserve old native policy/request decoding through versioned dispatch; do not silently change finalized results or authorization interpretation under a cache. Freeze/wipe and revocation prevent new unauthorized actions without fabricating random failure outcomes. Retained request/results follow their separately specified native ownership and lifecycle, including wiped refund destinations.

## Test vectors

ACL: unavailable stub, allow/deny, forged context/handle, delegation escalation, revoked predecessor rights, membership change, old code/current policy and caught denial. Randomness: unavailable stub, valid pending, repeated finalized read, wrong contract/domain, premature/wrong-round result, tampered proof, replay/resampling, withheld finality and rollback of request plus application commitment. Test fixtures must be impossible to enable in a production profile. Compare serial/parallel results and cost/dependency handling.

## Reference implementation, rationale and open decisions

Native project owners implement the primitives in their appropriate DPP/Drive/versioned services. rs-drive-contracts provides gated adapters; rs-dashvm-abi and contract SDK expose typed calls; clients/proof verifier share native result definitions. The external project specification tasks remain explicitly open: this boundary draft is complete enough to implement stubs and integration contracts, but it is not a cryptographic or full native ACL specification. Keeping them separate respects the selected scope and prevents an accidental insecure default.

## Related drafts and implementation tracking

[DVM-01](dip-dashvm-protocol.md) · [DVM-02](dip-dashvm-engine-abi.md) · [DVM-03](dip-dashvm-activation.md) · [DVM-04](dip-dashvm-storage.md) · [DVM-05](dip-dashvm-guards.md) · [DVM-06](dip-dashvm-execution.md) · [DVM-07](dip-dashvm-fees.md) · [DVM-08](dip-dashvm-scheduling.md) · [DVM-09](dip-dashvm-governance.md) · [DVM-10](dip-dashvm-proofs-clients.md) · [DVM-11](dip-dashvm-rust-sdk.md)

* [43-ACL](https://github.com/dashpay/platform/issues/4677): Deliver the native ACL primitive as a separate project (4.3-dev).
* [44-AUTHOR](https://github.com/dashpay/platform/issues/4680): Settle contract declarations and the Rust author API (4.4-dev).
* [44-RNG](https://github.com/dashpay/platform/issues/4682): Deliver the native randomness primitive as a separate project (4.4-dev).
* [50-AUTHOR](https://github.com/dashpay/platform/issues/4694): Deliver contract SDK, macros, build/test tools and worked example (5.0-dev).
* [50-ACL](https://github.com/dashpay/platform/issues/4698): Integrate native ACL with fail-closed contract stubs (5.0-dev).
* [50-RNG](https://github.com/dashpay/platform/issues/4699): Integrate native randomness with fail-closed contract stubs (5.0-dev).

[Complete storage mapping](https://github.com/dashpay/platform/issues/4626#issuecomment-5634141255) · [Capability catalogue and current amendments](https://github.com/dashpay/platform/issues/4626#issuecomment-5636957194) · [Module architecture](https://github.com/dashpay/platform/issues/4626#issuecomment-5636536959) · [Owner decisions and provisional limits](https://github.com/dashpay/platform/issues/4626#issuecomment-5583771268). These linked appendices retain their stated confirmed/proposed status.

Related work: [DIP-0029, LLMQ-selection randomness](https://github.com/dashpay/dips/blob/master/dip-0029.md); its scope is not the application primitive proposed here.

## Copyright

This working proposal is released under the MIT License, following the default license of the Dash DIPs repository.
