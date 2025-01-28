<pre>
  DIP: aj-locale-decimal-places
  Title: User-Friendly, Locale-based Significant Digits
  Authors: coolaj86
  Special-Thanks: Rion Gull
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2023-06-30
  License: CC0-1.0
</pre>

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Abstract](#abstract)
- [Prior Art](#prior-art)
- [Motivation](#motivation)
- [Specification](#specification)
- [Copyright](#copyright)

## Abstract

This DIP proposes to only show DASH in increments that are useful to the end
user, rounding down excess digits.

Before:

```text
You've received 0.99999807 DASH
```

After:

```text
You've received 0.999 DASH
```

keywords: denominations denominated floor round down locale

## Motivation

The value of DASH can be quite volatile from one day, hour, or even second to
next. So much so that showing 8 decimal places of "sats" is not helpful to end
users. In fact, it probably degrades user experience significantly for most
people.

Also, there are no delimiters for the right side of a decimal place:

```
10,000,000.00000000
```

Although terms such as "mDash" exist, they are not widely used in Dash software
and, since they don't follow general scientific notation that most people are
familiar with internationally (DASH uses 8 decimal places, not 9), they can be
confusing to try to use.

The volatility alone from one (literal) minute to the next make it unreasonable
to track so many decimal places.

Also, exchanges such as Kraken do not honor DASH coins less than `0.01`.

Other price estimators rarely go to the full 8 decimal places.

In Dash Discord channels this is often associated with the "mental gymnastics"
necessary to use DASH.

If DASH is to be "Digital Cash", the value shown to the user should be limited
to "spendable" amounts (ex: how much DASH would I need for a casual, low cost
commodity such as pack of gum, breath mints, bottle of water, or bread).

## Specification

Due to the volatile nature of DASH a fixed number of decimal places may not
always apply, but we can apply locale information and a simple set of rules that
will almost always be correct.

1. Select the lowest, known-cost commodity, priced in DASH.
2. If the price in DASH is not available, use data based on the user's preferred
   local currency and convert that value into DASH.
3. Round up (`ceil`) to the next most significant decimal place.
4. Divide by 10.
5. This is the maximum number of decimal places that SHOULD be shown to the
   user.
6. DASH shown in this amount should be rounded down. \
   Ex: if 3 decimal places are used, `0.99999807` MUST be shown as `0.999`

Example:

```text
Bottle of Water:    $1.19 (USD, my Locale)
Water in  Dash:     0.031654 DASH (as of the date of this publication)
Significant Digit:  0.04 DASH
Divide by 10:       0.004
Number of Decimals: 3
```

Caveats:

- The User Agent MUST allow the user to override this in settings
- The User Agent MUST NOT exceed this by more than 1 decimal place by default
  ```
  Algorithm suggests 0.001 as lowest denomination
  Usage Agent MUST NOT show lower than 0.0001 by default
  ```
- In the absence of the appropriate data, the number of decimal places to be
  shown SHOULD be 3 and MUST NOT be more than 4.
- When possible the software should warn the user if they are sending an amount
  to a contact or service that will not honor that number of decimal places

## Copyright

Copyright 2023 AJ ONeal.

Written in 2023 by AJ ONeal <coolaj86@proton.me> \
To the extent possible under law, the author(s) have dedicated all copyright \
and related and neighboring rights to this software to the public domain \
worldwide. This software is distributed without any warranty. \

You should have received a copy of the CC0 Public Domain Dedication along with \
this software. If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.
