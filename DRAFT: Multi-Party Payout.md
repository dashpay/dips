<pre>
  DIP: 000x
  Title: Multi-Party Payouts
  Authors: Timothy Munsell, UdjinM6
  Special-Thanks: Danny Salman
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
- [Registering a Masternode (ProRegTx) and Updating Registrar of Masternode (ProUpRegTx)](#registering-a-masternode-proregtx-and-updating-registrar-of-masternode-proupregtx)
  - [Validation Rules](#validation-rules)
- [Copyright](#copyright)

## Abstract

This DIP builds on the chain consensus for masternode lists laid forth in DIP0003 and provides for multi-party payout beyond the single owner + operator framework of the current system.

## Motivation and Previous System

In the previous system, masternodes gained entry to the masternode list after the owner created a ProRegTx. This transaction provided key IDs for up to two roles that would receive masternode rewards payouts:

 * Owner
 * Operator

### Problems with the previous system

Paying rewards to only two addresses based on a single value field prevents automatic/trustless sharing of the rewards beyond the owner and/or operator. A more flexible reward payout system is critical for enabling trustless masternode shares and introducing Dash-native DeFi opportunities through staking (among other use cases).

## Prior Work

* [DIP 0002: Special Transactions](https://github.com/dashpay/dips/blob/master/dip-0002.md)
* [DIP 0003: Deterministic Masternode Lists](https://github.com/dashpay/dips/blob/master/dip-0003.md)

## Registering a Masternode (ProRegTx) and Updating Registrar of Masternode (ProUpRegTx)

We propose introducing version 2 of these transaction types to replace the `scriptPayout` and `scriptPayoutSize` fields with `payoutShares` and `payoutSharesSize` respectively.

| Field | Type | Size | Description |
| --- | --- | --- | --- |
| payoutSharesSize | compactSize uint | 1-9 | Size of the Payout Share set |
| payoutShares | payoutShare[] | 1-100 | A set of `payoutShare` items |

Each `payoutShare` item should have the following structure:

| Field | Type | Size | Description |
| --- | --- | --- | --- |
| scriptPayoutSize | compactSize uint | 1-9 | Size of the Payee Script |
| scriptPayout | Script | Variable | Payee script (p2pkh/p2sh) |
| payoutShareReward | uint_16 | 2 | A value from 0 to 10000 |

To prove ownership of external collaterals, masternode owners must sign the following message and use the resulting signature as the ProRegTx `payloadSig`:

`<magicString><payoutSharesStr>|<operatorReward>|<ownerKeyAddress>|<votingKeyAddress>|<payloadHash>`

Where `payoutSharesStr` is:

`address(<payoutShares>[0].<scriptPayout>)>|<payoutShares>[0].<payoutShareReward>|...|address(<payoutShares>[n].<scriptPayout>)>|<payoutShares>[n].<payoutShareReward>`

### Validation Rules

A ProRegTx or ProUpRegTx is invalid if any of these conditions are true (in addition to rules defined in DIP0003):

  1. Size of `payoutShares` > 100
  1. Any `payoutShareReward` > 10000
  1. sum of `payoutShares` != 10000

## Copyright

Copyright (c) 2021 Dash Core Group, Inc. [Licensed under the MIT License](https://opensource.org/licenses/MIT)
