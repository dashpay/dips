<pre>
  DIP: aj-stamped-denominations
  Title: Securing Denominated Send by using Dust as Transaction Stamps
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
  - [Turning Dust into Transaction Fee Stamps](#turning-dust-into-transaction-fee-stamps)
- [Copyright](#copyright)

## Abstract

This DIP proposes to use the dust created by denominating coins as stamps for
transaction fees, rather than being immediately donated to the network.

This applies to TWO categories of software:

- Software which ONLY denominates in special cases, like CoinJoin \
  (for example, Private Send DOES NOT denominate its outputs)
- Software which ALWAYS denominates, except in special cases, like DashWallet \
  (always denominates inputs and outputs, except when sending via legacy protocols)

Current:

Lots of DASH is simply wasted, and the fee "stamps" don't actually cover the fee
of a single coin in many cases. XPub Sends are not possible.

```text
5.000 =>
    4x 1.0000 1000
    9x 0. 10000 100
    9x 0.0 10000 10
    9x 0.00 10000 1

Spendable Dash: 4.999
Transactions per Denom: < 1
Dash Wasted: (0.00049900 + 0.00050010) - 1077 (0.019%)
```

Proposed:

Almost no DASH is wasted, and each coin has several fee "stamps" that are
guaranteed to cover the cost of many transactions. This means that XPub Sends do
not undo any mixing that may have taken place.

```text
5.000 =>
    4x 1.000 03200
    9x 0.100 03200
    9x 0.010 03200
    5x 0.001 03200
    4x 0.001 03000

Spendable Dash: 4.999
Transactions per Denom: 15+
Dash Wasted: 0.00000160 (0.000%)
```

This is **NOT** specific to CoinJoin / "mixing" / PrivateSend, but **ALL**
current and future forms of denominated DASH.

keywords: Stamp Dust Transaction Tx Fee Denominated coins CoinJoin PrivateSend
mixing coin mix

## Prior Art

- [Dash Glossary: Denominations](https://docs.dash.org/projects/core/en/stable/docs/resources/glossary.html#denominations)
- [Dash Core: Denominations](https://docs.dash.org/projects/core/en/stable/docs/guide/dash-features-coinjoin.html#wallet-preparation)

[lextx]: https://github.com/bitcoin/bips/blob/master/bip-0069.mediawiki

**DashCore Code References**

These are some areas that would need to be refactored as a semver-breaking
change to apply this DIP:

- [IsValidDenomination](https://github.com/dashpay/dash/blob/549e347b742cb4dc63807a292729e658218d7d0f/src/coinjoin/coinjoin.h#L409C10-L409C10)
- [DenominationToAmount](https://github.com/dashpay/dash/blob/549e347b742cb4dc63807a292729e658218d7d0f/src/coinjoin/coinjoin.h#L431)
- [vecStandardDenominations](https://github.com/dashpay/dash/blob/549e347b742cb4dc63807a292729e658218d7d0f/src/coinjoin/coinjoin.h#L391)

## Motivation

Currently the only type of denominated coins that DashCore supports have several
drawbacks (and vulnerabilities in leaking user information) related to how they
are are split and "stamped" for fees:

- much of the denomination value is **burned as dust**: \
  `5.0000 0000` burns about `0.00093761` at time of denomination \
  (which could have been used for over 468 single-coin transactions)
- small single coins have a stamp value **too low to pay fees** (min fee is
  `193`):
  ```text
  0. 10000 100
  0.0 10000 10
  0.00 10000 1
  ```
- large coins waste DASH that could have been used to pay fees elsewhere:
  ```text
  10.000 1000
  ```
- they must always be de-denominated and de-mixed to be spent \
  (XPub Send is not feasible)

  ```text
  To Pay 0.221, I'd need 6 coins:
  (one of which is entirely wasted)

  0. 10000 100 \
  0. 10000 100 -\
  0.0 10000 10 --\
  0.0 10000 10 ---- 0.2220 0222 -> 0.2210 0000 + 938 (fee)
  0.00 10000 1 --/
  0.00 10000 1 -/
  ```

Similar issues are also discussed in
[DashCore: CoinJoin Fees](https://docs.dash.org/projects/core/en/stable/docs/guide/dash-features-coinjoin.html#fees).

## Specification

This makes assumptions based on present conditions of DASH:

- Symbolic "fees" are required for each transaction
- The minimum fee value is 193.

Given those assumptions, the specification is as follows:

- All denominations (CoinJoin, XPub, or otherwise) MUST redistribute "stamp"
  values".
- These stamp values SHOULD be denominated themselves.
- A single stamp value MUST be large enough to pay for a single transaction. \
  (at least the minimum guaranteed fee - currently 193 sats, \
  preferably a multiple of the lowest denomination, such as 200)
- Remainder values for stamps SHOULD be redistributed with a minimum stamp
  value. \
  (minimum value MAY change based on network conditions)
- Stamp values MUST NOT be distributed in a way that leaks user data. \
  (such as apply one user's stamp values only to that user's coins)

**How to Declare Acceptable Denominations**

A denomination has two distinct components:

- The user-visible value
- The embedded stamp value (for paying fees)

A denomination MUST include a minimum number of "stamps" for paying fees.

Pseudocode:

```js
// 1. Declare the stamp value
const STAMP_DENOM = 200;
const MIN_STAMPS_VALUE = 3 * STAMP_DENOM;
```

```js
// 2. Declare and store the denominations
//    (in descending order for efficiency and ease-of-use)
const LOWEST_DENOM = 10_000;
let DENOMS = [
  // 10.0
  10_0000_0000,
  // 1.0
  1_0000_0000,
  // 0.1
  1000_0000,
  // 0.01
  100_0000,
  // 0.001
  LOWEST_DENOM,
];
```

**How to Determine a Coin is Denominated**

To test whether or not a coin is denominated:

- subtract the lowest denomination
- check if the result is greater than the lowest denomination
- if not, check if the result is a valid stamp value
- if not, reject the coin as not denominated

Pseudocode:

```js
// 3. Check if the coin is denominated
function isDenominated(sats) {
  if (sats < LOWEST_DENOM) {
    return false;
  }

  sats -= LOWEST_DENOM;
  // note: 2x the lowest denomination *may* be considered denominated
  if (sats > LOWEST_DENOM) {
    return false;
  }

  let remainder = sats % STAMP_DENOM;
  if (remainder !== 0) {
    return false;
  }

  let hasMinimumStamps = remainder >= MIN_STAMPS_VALUE;
  if (!hasMinimumStamps) {
    return false;
  }

  return true;
}
```

**How to Distribute Stamp (Fee) Values to Outputs**

For a coin to be considered denominated, it must have a minimum stamp value.

The initial stamp value distribution can be calculated as the sum of the inputs
(denominated, or non-denominated), minus fees, applied to the outputs evenly:

```js
const VERSION_SIZE = 4;
const INPUT_COUNT_SIZE = 1;
const OUTPUT_COUNT_SIZE = 1;
const LOCKTIME_SIZE = 4;
const CONTAINER_SIZE =
  VERSION_SIZE + INPUT_COUNT_SIZE + OUTPUT_COUNT_SIZE + LOCKTIME_SIZE;

const MAX_PKH_UNLOCK_SCRIPT_SIZE = 149;
const MAX_PKH_LOCK_SCRIPT_SIZE = 34;

// note: in this example the preliminary denomination
// of outputs has already occurred
function distributeStamps(inputs, outputs) {
  let fee = CONTAINER_SIZE;
  fee += inputs.length * MAX_PKH_UNLOCK_SCRIPT_SIZE;
  fee += outputs.length * MAX_PKH_LOCK_SCRIPT_SIZE;

  let inSats = 0;
  for (let input of inputs) {
    inSats += input.satoshis;
  }

  let outSats = 0;
  for (let output of outputs) {
    outSats += output.satoshis;
  }

  let dust = inStats - outSats;
  let numStamps = dust / STAMP_DENOM;
  numStamps = Math.floor(numStamps);

  let evenStamps = numStamps / outputs.length;
  evenStamps = Math.floor(eventStamps);

  let stampValue = evenStamps * STAMP_DENOM;
  for (let output of outputs) {
    output.satoshis += stampValue;
  }

  let extraStamps = numStamps % outputs.length;
  return extraStamps;
}
```

The extra remaining stamps MAY be applied to the outputs. If so, they MUST be
**distributed deterministicly**:

The outputs MUST sorted according to [Lexicographical Indexing of Transaction
Inputs and Outputs][lextx], and the excess MUST be applied to each output in
order, until there is no excess (a single round-robin pass).

```js
// Distributes extra stamps to sorted outputs in round-robin fashion
function distributeExtraStamps(outputs, extraStamps) {
  outputs.sort(byLexOutIndex);

  for (let output of outputs) {
    if (extraStamps <= 0) {
      break;
    }

    outputs.satoshis += STAMP_DENOM;
    extraStamps -= 1;
  }
}
```

```js
// Sorts outputs by script order
function byLexOutIndex(a, b) {
  if (a.amount < b.amount) {
    return 1;
  }
  if (a.amount > b.amount) {
    return -1;
  }

  let aScript;
  let bScript;

  if (a.script && b.script) {
    aScript = a.script;
    bScript = b.script;
  } else if (a.pubKeyHash && b.pubKeyHash) {
    aScript = a.pubKeyHash;
    bScript = b.pubKeyHash;
  } else if (a.address && b.address) {
    aScript = a.address;
    bScript = b.address;
  } else {
    console.error(a);
    console.error(b);
    throw new Error("cannot compare incompatible lockscript types");
  }

  if (aScript < bScript) {
    return 1;
  }
  if (aScript > bScript) {
    return -1;
  }

  return 0;
}
```

**Guidance on How to Account for Received Transactions**

When sending to an XPub the user agent SHOULD send denominated coins to
individual XPub addresses in a 1:1 fashion (less fees, and accounting for stamp
redistribution):

```text
10000 5000 => 1 0000 4000
 5000 5200 =>   5000 4200
  100 2800 =>    100 4200

(fee is 559, which rounds to 600,
 or 3 stamps consuming 41 dust)
```

In this case, the "transaction amount" displayed to the user SHOULD BE be the
SINGLE TRANSACTION's whole amount, NOT the individual UTXOs.

The stamp/fee values (values below the lowest denomination) SHOULD NOT be shown
in the calculation to the user.

Consider this example where the `LOWEST_DENOM` is (for the purpose of
illustration) set to `10000` (`0.0001`) and each coin will be stamped with 20 to
21 transaction fees of `200`:

1. The receiver requests `1.5100`
2. The outputs received as as follows:
   ```text
   outputs:
       1.00004000
       0.50004200
       0.01004200
   ```
3. The following calculations are made
   ```text
       Sat value: 1 51012400
   Shown to User: 1.5100     (NOT 1.5101, NOT 3 transactions)
   ```

**Guidance for Sending to Legacy (non-XPub) Addresses**

There are two cases which break denominated sending:

1. Sending an exact, 8-decimal place (single sat denominated) amount to a legacy
   protocol
2. Sending a denominated amount to a single, legacy address

In these cases the sum total of the stamp values may add up to one or more whole
denominated, stamped coins.

Since the constraints which prevent leaked data are already broken in these
cases anyway, the user agent MAY prompt the user as to whether or not they would
like denominated return change.

The user agent SHOULD NOT return non-denominated change.

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
