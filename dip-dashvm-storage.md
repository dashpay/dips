<pre>
  DIP: Unassigned (dip-dashvm-storage)
  Title: Native storage, collections and capabilities
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

Map smart-contract code, declarations, native application state, balances and lifecycle records onto Drive/GroveDB. Preserve native documents, secondary indexes, validation, atomic operations, refunds and proofs. The attached 18-area mapping and 110-capability register are integral implementation appendices; catalogue inclusion is not a claim that every host interface already exists.

## Motivation

Contracts need sum/count trees, ranked and composite queries, relations and specialized collections without rebuilding those primitives in guest code. Typed declarations let Drive enforce the real native invariants and cost bounds while exposing stable contract APIs.

## Specification

### Contract namespace

Existing root `64 / contract_id` contains raw byte `0` for contract/schema metadata and `1` for documents. Data-only contracts retain exactly this shape and receive no empty executable placeholders. Smart contracts add `2 = EXEC`, `3 = COLLECTIONS`, `4 = RUNTIME`. EXEC contains permanent modules/manifests, routing, policy and readiness; COLLECTIONS contains declared specialized instances; RUNTIME contains jobs, receipts and asset discovery indexes.

For a new smart contract, apply the existing 0/1 skeleton first and the 2/3/4 extension as a second distinct Merk application inside the same outer GroveDB transaction. This produces local root 1, left child 0, right child 3 with children 2 and 4 under the inspected GroveDB implementation. Coalescing all five into an empty-tree batch chooses a different root and is forbidden for this layout generation. AVL balancing remains enabled. Descendant changes occur in child Merks and do not add siblings. Keep namespace parents structurally stable; any future sibling/removal change requires explicit layout handling.

Authorized data-to-smart conversion preserves current schema, documents, native assets and history and adds the executable namespace atomically. Rejected conversion does not leave partial executable subtrees. Reads cannot create them. Pending, cancelled, retired or wiped smart code does not convert the contract back into a pristine data-only contract. Historical contract root shapes must be inspected and handled explicitly rather than silently rewritten.

### Native data and collection declarations

Persistent Rust records are ordinary native documents under key 1. DPP and Drive validate properties, identities, revisions, ownership, native permissions and index changes. Reuse versioned native index-update validation: the inspected current validator rejects changing existing document-type indexes; new types may declare indexes normally. This project introduces no general schema migration/backfill subsystem.

Each specialized collection template declares a stable ID, native tree/bundle kind, key/value codecs, element constraints, authorized operation set, bounds, proof/result profile, retention and owner. Instances are created only by a bounded authorized operation against an already accepted template. The host maps typed handles to native paths; guest code cannot supply arbitrary paths, raw Elements, forged owners or an undeclared tree kind. Reject unsupported option combinations rather than ignoring them.

The capability appendix covers ordinary/sum/big-sum/count/provable/ranked trees, native document/index/query families, ordinary and bidirectional references, append/MMR/commitment families, assets, identities/groups, system boundaries, proof projection, costs and lifecycle. Native private-store exposure remains unavailable until key management, ciphertext visibility, proof disclosure and availability are specified; catalogue coverage is not an encryption guarantee. ACL/randomness integration follows DVM-12.

### Ownership and authority

A capability descriptor binds namespace, schema/template, permitted operation, target contract, rights and limits. It is checked against current native authority on every use. Static declaration permits requesting an operation; it does not itself grant ownership or bypass native rules. Keep signer, caller contract and resource owner distinct. An old supported code version uses current storage permissions. Native contested-index awards cannot invoke any custom guard or guest veto; contracts only supply validated native parameters.

### Monetary areas

Use one authoritative credit holding per contract/bucket in the proposed contract-credit hierarchy, included once in conservation. Ordinary SumTree is the current engineering recommendation for the credit root and per-contract trees; prove aggregate totals through the authenticated parent element/path. ProvableSumTree remains suitable where compact arbitrary range-sum proofs are required. Exact new root allocation remains open.

Contract token holdings extend the existing per-token ledger under `16/128/token_id` through a reserved holder branch whose key shape cannot collide with an identity ID. Keep one token per aggregate and one amount per holding. Native mint/burn/transfer/freeze/enumeration/proof code must understand that branch. Asset discovery indexes contain locators, never duplicate balances or supply. Token issuer discovery must include pre-existing native tokens when a data contract becomes smart.

Contract credit/token/document transfers preserve receiving-side deposit rules, identity/group authorization, multi-recipient payout bounds and mutual permission for contract-to-contract transfers. Contracts are their own native owners, not ordinary identities without keys. No direct contract-to-Core unlock is introduced; any permitted outward movement must use the existing authorized native path through a valid recipient. Asset action validation and conservation apply even when initiated by handwritten guest code.

Reuse existing prefunded balances at `40/128`; do not create DASHVM_RESERVES. New job-removal IDs bind a versioned purpose domain, contract and job, preserving legacy vote IDs. Ownership/purpose metadata is not money. Native paths derive and check permitted purposes so a guest cannot debit a vote fund as a job reserve. Removal/refund settlement is atomic and exactly once.

### Native operations and ordered atomicity

rs-drive-contracts requests typed native actions; DPP/Drive enforce shared validation and Drive produces operations including all secondary index/reference/aggregate effects. Canonical replay applies them in the required order under one ABCI-owned outer transaction. Never merge speculative physical Merk deltas. Track storage and cost dependencies as DVM-06 specifies. Fee estimation and actual application must use matching native paths and include the two-stage namespace insertion where relevant.

### Retention, cleanup and synchronization

Accepted module blobs/manifests are permanent, deduplicated only within their contract; original storage ownership survives reuse. Receipt retention is contract-controlled. Proposed cleanup records contain bounded deterministic phase/cursor information, use atomic step+cursor updates and can resume after crashes. A logical wipe immediately removes spendability/authority before physical cleanup. Cleanup does not delete code, re-credit settled money or resurrect destroyed tokens. Checkpoint, state sync and proof verification must understand every new Element/record version and durable progress state.

## Compatibility and deployment

All new keys, codecs, root variants and native dispatch are versioned. Preserve existing 0/1 data-only behavior, voting prefunds, identity token leaves and historical refund flags. Rehearse upgrade with populated trees and rollback/retry, including nodes syncing directly to post-upgrade state. No empty namespace migration is permitted for ordinary contracts.

## Security considerations

Enforce nonnegative monetary bounds and checked sums. Reject cross-purpose prefund access, wrong token namespaces, forged handles, unauthorized schema mutations and unbounded cascades. Bound derived work, not only explicit writes. Retained inner sums after logical wipe are not available balances; query/proof consumers must apply lifecycle exclusion.

## Test vectors and acceptance

For every capability, cover declaration, authorized/unauthorized operation, atomic derived effects, cost upper bound, rollback, current-root proof/result behavior and lifecycle disposition. Required storage vectors include fresh/reopened root-1 shape, data-only absence proofs, conversion rollback, ordinary versus provable aggregates, token-holder separation, mixed voting/job prefunds, code reuse, wipe cleanup restart and sync compatibility. Full capability/storage/task coverage is mechanically checked in the tracking manifest; production tests remain open.

## Reference implementation, rationale and allocations

Drive owns paths, native trees, operations, indexes and proofs. Integration owns guest-to-native adaptation; ABCI owns block order and commit. The detailed storage appendix supplies S01–S18 paths/record semantics; symbolic inner tags and new root values require collision checks against actual registries. Reusing native primitives avoids a second indexing implementation and preserves Platform query/proof behavior.

## Related drafts and implementation tracking

[DVM-01](dip-dashvm-protocol.md) · [DVM-02](dip-dashvm-engine-abi.md) · [DVM-03](dip-dashvm-activation.md) · [DVM-05](dip-dashvm-guards.md) · [DVM-06](dip-dashvm-execution.md) · [DVM-07](dip-dashvm-fees.md) · [DVM-08](dip-dashvm-scheduling.md) · [DVM-09](dip-dashvm-governance.md) · [DVM-10](dip-dashvm-proofs-clients.md) · [DVM-11](dip-dashvm-rust-sdk.md) · [DVM-12](dip-dashvm-external-primitives.md)

* [44-GROVE](https://github.com/dashpay/platform/issues/4678): Adopt the reviewed GroveDB foundation (4.4-dev).
* [44-AUTHOR](https://github.com/dashpay/platform/issues/4680): Settle contract declarations and the Rust author API (4.4-dev).
* [50-DEPLOY](https://github.com/dashpay/platform/issues/4684): Implement permanent bundles, registration, readiness and version routing (5.0-dev).
* [50-READS](https://github.com/dashpay/platform/issues/4686): Implement bounded current-state guest reads (5.0-dev).
* [50-CALLS](https://github.com/dashpay/platform/issues/4687): Implement atomic calls, delegation and ordered parallel execution (5.0-dev).
* [50-NATIVE](https://github.com/dashpay/platform/issues/4690): Implement the full native capability and collection adapters (5.0-dev).
* [50-CAP-COST](https://github.com/dashpay/platform/issues/4691): Validate cost and refund bounds for every native capability (5.0-dev).
* [50-PROOFS](https://github.com/dashpay/platform/issues/4692): Implement current-root queries and proof verification (5.0-dev).
* [50-AUTHOR](https://github.com/dashpay/platform/issues/4694): Deliver contract SDK, macros, build/test tools and worked example (5.0-dev).
* [50-GOV](https://github.com/dashpay/platform/issues/4695): Implement governance, bounded wipes and vestige recovery (5.0-dev).
* [50-ACL](https://github.com/dashpay/platform/issues/4698): Integrate native ACL with fail-closed contract stubs (5.0-dev).
* [50-RNG](https://github.com/dashpay/platform/issues/4699): Integrate native randomness with fail-closed contract stubs (5.0-dev).

[Complete storage mapping](https://github.com/dashpay/platform/issues/4626#issuecomment-5634141255) · [Capability catalogue and current amendments](https://github.com/dashpay/platform/issues/4626#issuecomment-5636957194) · [Module architecture](https://github.com/dashpay/platform/issues/4626#issuecomment-5636536959) · [Owner decisions and provisional limits](https://github.com/dashpay/platform/issues/4626#issuecomment-5583771268). These linked appendices retain their stated confirmed/proposed status.

## Copyright

This working proposal is released under the MIT License, following the default license of the Dash DIPs repository.
