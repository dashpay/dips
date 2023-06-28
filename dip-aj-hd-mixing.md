<pre>
  DIP: aj-hd-mixing
  Title: Coin Mix Tracking in HD Wallets via HDPath
  Authors: coolaj86
  Special-Thanks: Rion Gull
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2023-06-28
  License: CC0-1.0
</pre>

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Abstract](#abstract)
- [Prior Art](#prior-art)
- [Motivation](#motivation)
- [Specification](#specification)
  - [Coin Mix Tracking via HDPath](#coin-mix-tracking-via-hdpath)
- [Other Considerations](#other-considerations)
- [Copyright](#copyright)

## Abstract

This DIP proposes to track "coin mixing" in HD Wallets using the HDPath.

keywords: CoinJoin PrivateSend mobile coin mixing mix hdpath mixpath

## Prior Art

- [Multi-Account Hierarchy for Deterministic Wallets](https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki)

## Motivation

Currently there's no strategy for tracking "coin mixing" on mobile devices, or
sharing "coin mixing" enabled wallet accounts between devices - such as in the
case where a second device should do the mixing because the mobile device cannot
reasonably do so.

Preferably we want a strategy that doesn't require syncing indexes, especially
not in one-off formats.

This solves all of those problems with minimal complexity.

This won't break any existing wallets - those that are unaware of mixing will
still be aware - and will enable shared data via an offline indexing scheme
protocol rather than requiring a new or custom format or online synced data.

## Specification

[lextx]: https://github.com/bitcoin/bips/blob/master/bip-0069.mediawiki

[Lexicographical Indexing of Transaction Inputs and Outputs][lextx] MUST be used
for all mixing transactions.

The _Usage_ component (at index 4) of the HDPath is designated for tracking coin
mixes for mixed accounts.

HDPaths are used in this format:

```text
m/<bip44>'/<coin>'/<account>'/<mixcount>/<index>
m/44'/5'/0'/0/0
```

Accounts should be designated as either Mixed or Unmixed. However, if any path
in the format of `m/44'/5'/<account>'/0/<index>` has only a single coin which is
a recognizable denomination, it should be searched from
`m/44'/5'/<account>'/1/<index>` up through `m/44'/5'/<account>'/<n>/<index>` to
the first unused address to find unspent mixed, denominated coins.

### Coin Mix Tracking via HDPath

**Summary of BIP-44**

The index to a particular private key or address of an HDPath is defined in this
format:

```text
m/<bip44>'/<coin>'/<account>'/<usage>/<index>
m/44'/5'/0'/0/0
```

The _Usage_ path component is presently used to indicate either:

- `0` as _External_, for sending money
- `1` as _Internal_ for receiving change

**Applied to Coin Mixing**

There are many factors that effect the viability of coin mixing, so for this
specification and these examples we'll make 2 assumptions:

1. mixed coins are generally not used in a scenarios where change is returned
2. any return change is denominated and its transaction adheres to
   [Lexicographical Indexing of TX Inputs & Outputs][lextx]

Given those assumptions either A) _Usage_ will _never_ represent return change
or B) the return change will already have some measure of entropy added to it.

This means that the _Usage_ path can be used in for tracking the mix count with
coming into conflict with unmixed coins.

```text
m/<bip44>'/<coin>'/<account>'/<mixcount>/<index>
m/44'/5'/0'/0/0 - newly denominated coin
m/44'/5'/0'/1/0 - coin which has been mixed once
m/44'/5'/0'/...
m/44'/5'/0'/16/0 - a fully mixed coin
m/44'/5'/0'/... - an overmixed coin
```

## Other Considerations

1.  Mixed accounts could be designated to start at 2147483648 and count _down_
    rather than starting at 0 and counting up.
    ```text
    m/44'/5'/2147483648'/0/0 - newly denominated coin on first mixed account
    m/44'/5'/2147483647'/0/0 - newly denominated coin on second mixed account
    ```
    Counterpoint: More complexity, no benefit. Software either will or won't be
    able to restore mixed accounts. This doesn't help.
2.  A new HDPath designation path could be introduced.
    ```text
    m/dipXX'/5'/0'/0/0
    ```
    Counterpoint: Software that follows the 44' spec can still follow this spec,
    so changing the identifier probably only makes it more difficult to adapt
    otherwise working software. DASH software will know to check for mixed
    funds.
3.  A new HDPath component could be introduced.
    ```text
    m/<bip44>'/<coin>'/<account>'/<usage>/<index>/<mixcount>
    m/dipXX'/5'/0'/0/0
    ```
    Counterpoint: Same as above, but more so.

## Copyright

Copyright 2023 AJ ONeal.

DIP to Secure Transactions - Patch Data Leak Vulnerability via Deterministic
Index Ordering

Written in 2023 by AJ ONeal <coolaj86@proton.me> \
To the extent possible under law, the author(s) have dedicated all copyright \
and related and neighboring rights to this software to the public domain \
worldwide. This software is distributed without any warranty. \

You should have received a copy of the CC0 Public Domain Dedication along with \
this software. If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.
