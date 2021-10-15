<pre>
  DIP: 000x
  Title: Multi-Party Payouts
  Author(s): Timothy Munsell,
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2021-05-08
  License: MIT License
</pre>

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Abstract](#abstract)
- [Motivation and Previous System](#motivation-and-previous-system)
  - [Problems with the previous system](#problems-with-the-previous-system)
- [Prior Work](#prior-work)
- [New Stake Holder Reward Fields within ProRegTx and ProUpRegTx](#new-stake-holder-reward-fields-within-proregtx-and-proupregtx)
- [Registering a Masternode (ProRegTx)](#registering-a-masternode-proregtx)
- [Updating Masternode Information](#updating-masternode-information)
  - [Updating Registrar of Masternode (ProUpRegTx)](#updating-registrar-of-masternode-proupregtx)
- [Validation Rules](#validation-rules)
  - [ProRegTx and ProUpRegTx](#proregtx-and-proupregtx)
  - [ProUpRevTx](#prouprevtx)
- [Masternode Rewards](#masternode-rewards)
- [Copyright](#copyright)

## Abstract

This DIP builds on the chain consensus for masternode lists laid forth in DIP0003 and provides for multi-party payout beyond the single owner + operator framework of the current system.

## Motivation and Previous System

In the previous system, Masternodes gained entry to the masternode list after the owner created a ProRegTx (DIP3). This tx provided key IDs for up-to 2 roles that would receive masternode rewards payouts:

 * Owner
 * Operator

Masternode rewards are payed to the Owner by default, and when defined, to the Operator. Current updatesto the masternode registrar  (relevant to this DIP) could only:

  * Define new Operator
  * Define payout to Operator

### Problems with the previous system

While elegant, under the current system, the masternode reward is paid to the operator based on the `<operatorReward>` field and any difference from 100% is automatically paid to the owner address.

The limitation of rewards paid to only 2 addresses based on a single value field prevents automatic/trustless sharing of the rewards beyond the owner and/or operator, a critical element for enabling trustless shares in a masternode and introducing Dash native DeFi opportunities through staking (among other use cases).

## Prior Work

* [DIP 0002: Special Transactions](https://github.com/dashpay/dips/blob/master/dip-0002.md)
* [DIP 0003: Deterministic Masternode Lists](https://github.com/dashpay/dips/blob/master/dip-0003.md)

## New Stake Holder Reward Fields within ProRegTx and ProUpRegTx

In the new system the ProRegTx and ProUpRegTx (DIP3) may include an additional fields to define additional parties to receive rewards beyond the owner and operator and the % of owner rewards each party receives.

This DIP defines:

  1. the sharedReward field
  2. the shareHolderReward field
  3. corresponding update to the ProRegTx
  4. corresponding update to the ProUpRegTx

All other transactions, transaction fields, the mechanisms for adding or removing masternodes and defining MN quorum and valid subset remain unchanged.

## Registering a Masternode (ProRegTx)

To join the masternode list, masternode owners must submit a special transaction (DIP2) to the network. DIP 3 defines the ProRegTx and the ProRegUpTx message, parts, and payload: `<magicString><payoutStr>|<operatorReward>|<ownerKeyAddress>|<votingKeyAddress>|<payloadHash>`

We propose adding an additional part (`<sharedReward>`)to produce a message that includes:

`<magicString><payoutStr>|<operatorReward>|<ownerKeyAddress>|<votingKeyAddress>|<sharedReward>|<payloadHash>`

The individual parts of the message are:

1. `<magicString>`: (DIP3) A fixed string which is always "DarkCoin Signed Message:" with a newline character appended.
Please note that existing tools (e.g. the RPC command `signmessage`) usually add the magicString internally, making it
unnecessary to manually add it.
2. `<payoutStr>`: (DIP3) The Dash address corresponding to the scriptPayout field of the ProRegTx. In case scriptPayout is not a
P2PK/P2PKH/P2SH script, `<payoutStr>` must be set to the hex representation of the full script.
3. `<operatorReward>`: (DIP3) The operatorReward field of the ProRegTx.
4. `<ownerKeyAddress>`: (DIP3) The Dash address corresponding to the keyIdOwner field of the ProRegTx.
5. `<votingKeyAddress>`: (DIP3) The Dash address corresponding to the keyIdVoting field of the ProRegTx.
6. `<sharedReward>`: (NEW) the sharedReward field of the ProRegTx.
7. `<payloadHash>`: (DIP3) The SHA256 hash of the ProRegTx payload with the payloadSig being empty.

The ProRegTx descretely specifies 2 rewards, the operatorReward and the sharedReward. The combined calculation of these two rewards then defines the owner's reward:
* The percentage of the masternode reward paid to the operator is calculated by dividing the operatorReward field by 100.
* The total percentage of the masternode reward to be paid to shareHolders is calculated by dividing the sharedReward field by 100.
* The remainder of the masternode reward is paid fully to the owner address.
* The percentage of the sharedReward paid to each shareHolder is the defined in the shareHolders field.

The ProRegTx also specifies a new field, shareHolders, that contains the addresses and percentage of the sharedReward each address is paid. This field is an array of key:value pairs. The key is Dash addresses that will receive rewards. The value is an integer between 1 and 100 (inclusive). This value is the percentage of the sharedReward the address will receive. To mitigate potential block size issues: this field is limited to a length of 100.

The transaction consists of the following data in the payload area:

| Field | Type | Size | Description | (DIP) |
| --- | --- | --- | --- |
| version | uint_16 | 2 | Provider transaction version number.  Currently set to 1. | DIP0003 |
| type | uint_16 | 2 | Masternode type. Default set to 0. | DIP0003 |
| mode | uint_16 | 2 | Masternode mode. Default set to 0. | DIP0003 |
| collateralOutpoint | COutpoint | 36 | The collateral outpoint. | DIP0003 |
| ipAddress | byte[] | 16 | IPv6 address in network byte order. Only IPv4 mapped addresses are allowed (to be extended in the future) | DIP0003 |
| port | uint_16 | 2 | Port (network byte order) | DIP0003 |
| KeyIdOwner | CKeyID | 20 | The public key hash used for owner related signing (ProTx updates, governance voting) | DIP0003 |
| PubKeyOperator | BLSPubKey | 48 | The public key used for operational related signing (network messages, ProTx updates) | DIP0003 |
| KeyIdVoting | CKeyID | 20 | The public key hash used for voting. | DIP0003 |
| operatorReward | uint_16 | 2 | A value from 0 to 10000. | DIP0003 |
| sharedReward | uint_16 | 2 | A value from 0 to 10000. | current |
| shareHolders | Array | Variable | An array of length between 1 - 100 of key value pairs `shareHolder address` : `percentage of sharedReward` (expressed an an integer from 1-100) | current |
| scriptPayoutSize | compactSize uint | 1-9 | Size of the Payee Script. |
| scriptPayout | Script | Variable | Payee script (p2pkh/p2sh) |
| inputsHash | uint256 | 32 | The SHA256 hash of all the outpoints of the transaction inputs |
| payloadSigSize | compactSize uint | 1-9 | Size of the Signature |
| payloadSig | unsigned char[] | Variable | Signature of the hash of the ProTx fields. Signed with the key corresponding to the collateral outpoint in case the collateral is not part of the ProRegTx itself, empty otherwise. |

## Updating Masternode Information

There are multiple ways to update masternodes only the ProUpRegTx is relevant to this DIP.

### Updating Registrar of Masternode (ProUpRegTx)

To registrar update a masternode, the masternode owner must submit another special transaction (DIP2) to the network. This special transaction is called a Provider Update Registrar Transaction and is abbreviated as ProUpRegTx. It can only be done by the owner.

A ProUpRegTx is only valid for masternodes in the registered masternodes subset. When processed, it updates the metadata of the masternode entry. It does not revive masternodes previously marked as PoSe-banned. (DIP3)

The special transaction type used for ProUpRegTx Transactions is 3.

The transaction consists of the following data in the payload area:

| Field | Type | Size | Description | DIP |
| ----- | ---- | ---- | ----------- | DIP3 |
| version | uint_16 | 2 | Upgrade Provider Transaction version number.  Currently set to 1. | DIP3 |
| proTXHash | uint256 | 32 | The hash of the provider transaction | DIP3 |
| mode | uint_16 | 2 | Masternode mode | DIP3 |
| PubKeyOperator | BLSPubKey | 48 | The public key used for operational related signing (network messages, ProTx updates) | DIP3 |
| KeyIdVoting | CKeyID | 20 | The public key hash used for voting. | DIP3 |
| sharedReward | uint_16 | 2 | A value from 0 to 10000. | current |
| shareHolders | Array | Variable | An array of length between 1 - 100 of key value pairs `shareHolder address` : `percentage of sharedReward` (expressed an an integer from 1-100) | current |
| scriptPayoutSize | compactSize uint | 1-9 | Size of the Payee Script. | DIP3 |
| scriptPayout | Script | Variable | Payee script (p2pkh/p2sh) | DIP3 |
| inputsHash | uint256 | 32 | The SHA256 hash of all the outpoints of the transaction inputs | DIP3 |
| payloadSigSize | compactSize uint | 1-9 | Size of the Signature | DIP3 |
| payloadSig | unsigned char[] | Variable | Signature of the hash of the ProTx fields. Signed by the Owner. | DIP3 |


## Validation Rules

### ProRegTx and ProUpRegTx

A ProRegTx is invalid if any of these conditions are true (all defined in DIP3 except conditions 11-13):

  1. collateralOutpoint `hash` is null but an output with 1000 DASH is not present at position `n` of the ProRegTx outputs
  2. collateralOutpoint `hash` is not null but an output with 1000 DASH can't be found in the UTXO specified by the `hash` and `n`
  3. Any KeyId* field is null (KeyIdOwner, KeyIdOperator or KeyIdVoting)
  4. KeyIdOwner or PubKeyOperator was already used by any entry in the registered masternodes set
  5. scriptPayout is not a P2PKH or P2SH script
  6. When scriptPayout is P2PKH script and the public key hash equals any of KeyIdOwner or KeyIdVoting
  7. ipAddress is set and port is not set to the default mainnet port
  8. ipAddress is set and not routable or not an IPv4 mapped address
  9. ipAddress is set and already used in the registered masternodes set
  10. operatorReward > 10000
  11. sharedReward > 10000 (Current DIP)
  12. sharedReward > 0 and shareHolders field is null (Current DIP)
  13. sum of values in shareHolders field != 100 (Current DIP)
  14. The inputsHash does not match the calculated hash
  15. collateralOutpoint `hash` is null and payloadSig is not empty (zero size)
  16. collateralOutpoint `hash` is not null and payloadSig is not a valid signature signed with the collateral key
  17. collateralOutpoint `hash` is not null and the referenced collateral is not a P2PKH output

Please note that while deploying this DIP, additional and temporary validation rules may apply. The details of these temporary rules will be described in the deployment plan.

### ProUpRevTx

A ProUpRevTx is invalid if any of these conditions are true:

1. proTxHash can not be found in the registered masternode set (DIP3)
2. sharedReward > 10000 (Current DIP)
3. sharedReward > 0 and shareHolders field is null (Current DIP)
4. sum of values in shareHolders field != 100 (Current DIP)
5. The inputsHash does not match the calculated hash (DIP3)
6. payloadSig is invalid (DIP3)

## Masternode Rewards

The new system allows to deterministically ascertain the recipient of the masternode’s portion of the next block reward (DIP3) beyond the owner/operator paradigm, but doesn't change any of the mechanisms to determine reward payment.

The rules to determine the next block’s payee are will continue to be (DIP3):

  1. Take the valid masternode subset of the previous block
  2. Sort the set in ascending order by "testHeight" and “ProRegTx hash”. “testHeight” is determined for each individual entry and equals the “last paid height” (or “registered height” if the masternode was never paid). If the masternode was PoSe-banned before and revived later, the “revival height” of the masternode is used instead of the “registered height”. If the “testHeight” of two masternodes is identical, the ProRegTx hash acts as a deterministic tie breaker.
  3. Take the first entry of the resulting list and use this as the next block’s payee.

This calculation is performed for every block to enforce proper payment of the block's masternode reward (both payee and amount). Previously, masternode payment enforcement was skipped for superblocks, so miners received the full mining reward. With DIP3, masternode payment enforcement is also performed on superblocks.

The "testHeight" logic in next block payee rule #2 (above) is used to ensure that masternodes must wait at least one full payment cycle before receiving their first reward. This is to incentivise long running masternodes and to avoid paying non-functioning masternodes before PoSe verification can remove them. It also ensures that new masternodes are not able to get a jump start in the payment queue.

## Copyright

Copyright (c) 2021 Dash Core Group, Inc. [Licensed under the MIT License](https://opensource.org/licenses/MIT)
