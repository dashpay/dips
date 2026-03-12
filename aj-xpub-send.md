<pre>
  DIP: aj-xpub-send
  Title: XPub Send (Denominated, Cash-Like Send)
  Authors: coolaj86
  Special-Thanks: Rion Gull
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2023-07-18
  License: CC0-1.0
</pre>

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Abstract](#abstract)
- [Prior Art](#prior-art)
- [Motivation](#motivation)
- [Specification](#specification)
  - [Natural Denominations](#natural-denominations)
- [Copyright](#copyright)

## Abstract

This DIP proposes how to send coins to contacts in a Cash-Like fashion:

- give every send a similar inherent "mixing" quality to cash
- make it so that coins do not lose their face value when transacted \
  (the 0.99999807 problem)
- prevent the "unmixing" coins on send

This also provides guidance for whether using denominated coins or not, and
whether returning change or not.

This is **NOT** specific to CoinJoin / "mixing" / PrivateSend, but **ALL**
current and future forms of denominated DASH.

Note: A future DIP may enforce this behavior at the protocol layer, much like
[Enforce Transaction Hygiene][enforce-hygiene] enforces [Lexicographical
Indexing][lex-sort-tx].

[enforce-hygiene]: https://github.com/dashpay/dips/pull/129

keywords: Cash-Like Send CashSend XPub Send denominated denominations

## Prior Art

- [User-Friendly Significant Digits][locale-denoms]
- [Multi-Account Hierarchy for Deterministic Wallets][hd-wallet]
- [Securing Denominated Send by using Dust as Transaction Stamps][self-stamp]
- [Lexicographical Indexing of Transaction Inputs and Outputs][lex-sort-tx]

[hd-wallet]: https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki
[lex-sort-tx]: https://github.com/bitcoin/bips/blob/master/bip-0069.mediawiki
[locale-denoms]: https://github.com/dashpay/dips/pull/132
[self-stamp]: https://github.com/dashpay/dips/pull/131

## Motivation

The current methods of sending DASH present two problems:

1. Data **Leakage** Vulnerability
   - the current Send mechanism may leak user data on each send, especially when
     return change is generated
   - the current Private Send mechanism unmixes coins in order to send them
2. The **0.99999807** problem
   - to spend a 1 DASH coin, the receiver only gets 0.99999807 DASH
   - when sending 1 DASH, the receiver can only send it as 0.99999807 DASH

In other words:

I expect Dash to be secure, but combining multiple coin inputs publicly leaks
more information about the transaction, sender, and receiver than is necessary
for the transaction. Through casual or statistical analysis, this may be used,
including by malicious parties, in ways that were not intended by the user and
which the user is not aware of.

Rather than unmixing all inuputs into a single output, the non-leaky nature of
cash should be preserved with DASH.

Also, when I send someone $1 cash, they get $1 cash. I expect that when I send 1
DASH, the receiver should get 1 DASH. It simply doesn't _feel_ good to have the
value misrepresented, even slightly.

## Specification

Coins are sent with both a Face Value (what the user sees) and a Stamp Value (to
be applied to current and future transaction fees).

- Contacts SHOULD be associated with XPrv or XPub addresses (typically depth-4)
- A lowest practical denomination SHOULD be defined (i.e. 0.001) \
  (no more than specified by [User-Friendly Significant Digits][locale-denoms])
- The value sent SHOULD be limited to the magnitude of the lowest denom
- Any coins can be used as inputs, but fewer coins SHOULD be preferred
- The sent value SHOULD be split into respective denominated, stamped coins
- All value below the lowest denom SHOULD be put towards stamp values (fees)
- Stamp values SHOULD themselves be denominated as multiples of 200
- The Face Value of the transaction is total Face Value sent to the XPub address

This MUST apply to all DASH "Wallet" software that recognizes Contacts and
accounts - such as friends, street vendors, business associates, etc - by one or
more XPubs.

This MAY or MAY NOT apply to all uses of XPubs generally.

When sending to one or more XPub Contacts (or multiple XPubs for a single
contact) in a single transaction, the number of addresses used to send to the
receiving party MUST NOT be artificially limited to a single address.

Notes:

1. Unless otherwise specified, the "natural" denominations (doubles, wholes, and
   halves) from 1000 (or higher) to 0.001 SHOULD be used:
2. The **optimal number of coins** to send is fewest coins required to represent
   the amount, typically just under 2 coins per digit (ex: 11.111 requires 5
   coins and 99.999 requires 15 coins).
3. Non-denominated coins should be used especially when doing so would reduce
   the number of coins sent (including change) below the _optimal number of
   coins_ for that amount.

### Pseudocode

```js
const STAMP_VALUE = 200;
const MIN_STAMPS = 3;
const MIN_STAMP_VALUE = MIN_STAMPS * STAMP_VALUE;

let faceValue = 1.234;
let contact = "@bob";
let changeAccount = "@me";

let outputs = Wallet.denominate(faceValue);
// 1.0
// 0.2
// 0.02
// 0.01
// 0.002
// 0.002
for (let output of outputs) {
  outputs.satoshis += MIN_STAMP_VALUE;
}

await Wallet.indexNextAddresses(contact, outputs.length);
await Wallet.indexChangeAddresses(changeAccount);

let addresses = Wallet.getNextAddresses(change, outputs.length);
for (let output of outputs) {
  output.address = addresses.pop();
}

let coins = Wallet.getAllCoins();
let inputs = Wallet.selectEnoughCoinsForOutputAndFees(coins, outputs, fee);

let changeAddrs = [];
let changeCoins = [];
outputs = Wallet.redistributeStampsAndChange(inputs, outputs, changeXPub);
for (let output of outputs) {
  if (output.address) {
    continue;
  }
  output.address = Wallet.getNextChangeAddress(changeAccount);
  changeAddrs.push(output.address);
  changeCoins.push(output);
}

let tx = Wallet.createTx(inputs, outputs);

// updated local caches for coins spent and received
await Wallet.reserveNextAddresses(contact, outputs.length);
await Wallet.reserveChangeAddresses(changeAccount, outputs.length);
await Wallet.reserveCoins(inputs);
await Wallet.expectCoins(changeCoins);

await Wallet.broadcastTx(tx);

await Wallet.commitReservationsAndExpectations();
```

### Face Value vs Stamp Value

The Face Value of a coin is the amount the user will see and interact with.

The Stamp Value of the coin represents how many times the coin can be transacted
as a single coin before it has to be broken down into change (or transacted with
other coins that have an excess of stamp values to apply to it).

For example:

- Sat Value: `1.00001000`
- Face Value: `1.0`
- Stamp Value: `1000` (can be transacted 5 times)

If DASH reaches a price where the cost of a transaction approaches 1% of the
smallest spendable unit, then it fails to serve as Digital Cash and loses its
cost advantage over conventional forms of digital payment.

### Natural Denominations

The "natural" denominations are the doubles, wholes, and halves (i.e. 2x, 1x,
0.5x) of each order of magnitude (i.e. 10x or 1/10x).

The denominations can go arbitrarily high (i.e. 10,000,000) but, due to the
current limitations imposed by the symbolic transaction fees, they cannot go
arbitrarily low.

The denominations SHOULD NOT go below `0.001` - and MUST not go below `0.0001` -
otherwise change has to be broken often to include the cost of spending the coin
in the coin's denomination and value / fee ratio becomes very low.

```text
1000
 500
 200
 100
  50
  20
  10
   5
   2
   1
   0.5
   0.2
   0.1
   0.05
   0.02
   0.01
   0.005
   0.002
   0.001
```

These are selected because:

- they are what many societies tend towards in their cash and coinage
- they work with the logarithmic scale of the human brain
- each number is fully represented in exactly one order of magnitude
- they tend to reduce the number of inputs required for arbitrary payments \
  at the lowest possible complexity in Base 10

Selected

- 1x (same as 10x or 1/10x)
  - represents an order of magnitude
- 2x, or 1/5x (of 10x)
  - commonly used $20, $2, 2¢
- 1/2x, or 5x (of 1/10x)
  - commonly used $50, $5, 50¢, 5¢

Not Selected

- 7x, 3x
  - not commonly used (i.e. "as strange as a $3 bill")
- 1/3
  - cannot be fully represented in decimal form (0.333)
  - cannot be recombined into a whole (0.999 ~= 1.000)
  - doesn't mix cleanly with other numbers (0.333 + 0.5 = 0.833)
- 1/4
  - does not fit within an order of magnitude (0.25 = 2x 0.1, 5x 0.01)
- 1/5
  - is already the same as 2x of the 1/10x
  - ex: 2 is 1/5 of 10, but can already be represented as 2x of 1
- 1/6
  - is not a commonly used number for pricing (0.167)
  - has similar issues to 1/3
- 1/8
  - similar issues to 1/4x (0.125 = 1x 0.1, 2x 0.01, 5x 0.001)
- 1/9
  - similar issues to 1/3x (9x 0.111 = 0.999)
- 1/11+
  - cannot be represented within an order of magnitude

### Stamp Denominations

The stamp denomination is any multiple of 200 less than 200 + the lowest
denomination (i.e. < 100,200). \

It represents how many times a coin can be spent before it has to be broken down
into change to pay for itself (or dissolved into stamps among other coins).

For example: A stamp value of 1,000 or 100,000 represents that a coin can be
spent 5 or 500 times, respectively.

Note: The lowest order of magnitude denominations could therefore be represented
as `DENOM + LOWEST_DENOM` (i.e. 200,000 = 100,000 + 500xS, as well as 300,000
and 600,000)

#### Rationale

The minimum fee for a transaction to be guaranteed to succeed is 193.

(the common fee of 192 and occasional fee of 191 is due to the random nature of
the presence of the high-order bit padding in ASN.1-encoded signatures)

Since it would be untenable to pay anywhere between 1/10x to 100x the cost of a
good or service in order to pay the cost of digital processing, we can safely
say that the lower 3 orders of magnitude of sats are not practical for payments.

Also, as the transaction cost approaches 1% of the value transferred, the
analogy of Digital Cash is lost, which makes 0.001 the lowest possible whole
denomination.

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
