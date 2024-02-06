<pre>
  DIP: aj-contact-scanback
  Title: URI Extensions for Mutual Contacts (XPubs), QRCode ScanBacks, & Subscriptions
  Authors: coolaj86
  Special-Thanks: Rion Gull
  Comments-Summary: No comments yet.
  Status: Draft
  Type: Standard
  Created: 2023-07-17
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

This DIP proposes

- matching schemes for HTTP URLs and DASH URIs
- query parameters for exchanging contact, payment, and subscription information
- peer-to-peer (offline, direct, or proxied) information exchange

For example:

```text
dash:Xcu5iYBH3szP744sQ1RUp3JHTVFHrFVdYu
  ?amount=0.11001000
  &xkey=xpub....
  &denoms=0.1,0.01
  &payment_date=2023-07-17T11:59:59
  &payment_tz=America/Denver
  &nickname=BNNA%20Hosting
  &purchase_url=https://bnna.net/s/123456
  &subscription_url=https://bnna.net/s/123456
  &r=https://bnna.net/pay?h%3D2a8628fc2fbe
```

keywords: scanback, qr code, qrcode, dash uri, payment url, contacts, xpubs,
xprvs, xkeys

## Prior Art

- [BIP-20: URI Scheme](https://github.com/bitcoin/bips/blob/master/bip-0020.mediawiki)
- [BIP-21: URI Scheme](https://github.com/bitcoin/bips/blob/master/bip-0021.mediawiki)
- [BIP-70: Payment Protocol](https://github.com/bitcoin/bips/blob/master/bip-0070.mediawiki)
- [BIP-71: Payment Protocol MIME Types](https://github.com/bitcoin/bips/blob/master/bip-0071.mediawiki)
- [BIP-72: URI extensions for Payment Protocol](https://github.com/bitcoin/bips/blob/master/bip-0072.mediawiki)
- [BIP-73: Response Type Negotiation with Payment Request URLs](https://github.com/bitcoin/bips/blob/master/bip-0073.mediawiki)
- [OIDC Core: 5.1 Standard Claims][oidc-claims]

[oidc-claims]:
  https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims

## Motivation

When people are exchanging value, there's already some form of communication
they're using to do it - whether text message or email or web page or QR code,
etc.

We want to have a simple, P2P method for exchanging contacts, creating
subscriptions, and communicating other payment-related information that can work
through the communication medium that parties involved in a transaction were
already using, even if it's offline.

## Specification

The prefix `dash:` and `dash://` MUST be treated equivalently.

Server query parameters in the form of `?a=42&foo=bar` and local hash query
parameters in the form of `#?a=42&foo=bar` or `#/?a=42&foo=bar` MUST be treated
equivalently by the User-Agent.

When using web URLs, private keys MUST be passed as local hash query parameters.

### 0. URL & URI Compatibility

- `coin`
- `referrer`

If a scanned URL has the query parameter `coin` set to `dash`, it should be
treated the same as if it were a dash URI, but with the original URL and any
unrecognized query parameters set as the `referrer`.

For example, these two URIs MUST be treated as equivalent:

```text
https://example.com/p/foo
    ?coin=dash
    &nickname=nick
    &bar=baz
    #?xprv=...
```

```text
dash:
    ?xprv=...
    &nickname=nick
    &referrer=https://example.com/p/foo%3Fbar=baz
```

### 1. Contact Exchange

- `xpub`
- `xprv`
- `sub`
- `profile`
- `picture`
- `nickname`
- `nonce`
- `request_claims`

Applications that support contacts MUST recognize the `xprv` and `xpub`
parameters which may be, respectively:

- an XPrv (ex: Shared Account with Trusted Contact)
- or XPub (ex: Contact)

Since most Dash users are not sophisticated in regards to the safe storage of
Wallet Phrases, XPrvs SHOULD be used instead of XPubs with trusted contacts so
that there is a mechanism to retrieve funds that would otherwise be lost.

ALL [OIDC Standard Claims][oidc-claims] SHOULD be supported, and the following
claims MUST be supported:

- `sub` a Pairwise Pseudonymous Identifier (PPID) that the sharer will use the
  describe the receiver
- `profile` a URL to a JSON description of the contact, including the [OIDC
  Standard Claims][oidc-claims], as well as any other claims described in this
  document
- `picture` a URL to an image representing the contact
- `nickname` an UNTRUSTED suggestion for what the sharer should be called
- `nonce` an idempotency key to prevent duplicate transactions (preferably ULID)

The User-Agent MUST also support these non-standard claims:

- `request_claims` like `request` or `request_uri`, but as a comma (or space)
  delimited list
- `response_uri` an encrypted or local URL to which a response can be POSTed

The sender MAY omit all except the `sub` PPID, `nonce`, and the `profile` URL.

The User-Agent SHOULD display the full domain and prompt the user before showing
the picture, or other data that a bad actor may reasonably use to attack the
receiver.

```text
dash:xpub=xpub6FKUF6P1ULrfvSrhA9DKSS3MA3digsd27MSTMjBxCczsfYz7vcFLnbQwjP9CsAfEJsnD4UwtbU43iZaibv4vnzQNZmQAVcufN4r3pva8kTz
  &sub=01H5KG2NGES5RVMA85YB3M6G0G
  &nickname=Prime%208
  &profile=https://imgur.com/gallery/y6sSvCr.json
  &picture=https://i.imgur.com/y6sSvCr.jpeg
  &scope=sub,nickname,profile,xpub
  &redirect_uri=https://
```

### 2. Contact Scan Back

After having received a contact, the User-Agent MUST give the user an option to
produce a Dash URI, URL, or QR Code that can sent, uploaded to, or scanned by
the other party, or otherwise automatically (after approval) send the requested
information to the `response_uri`.

For example:

- after scanning a contact from a web page on my phone, I can reverse my phone
  screen to the web cam on the computer to complete the process
- after receiving a DASH URI via text message from a contact including an OIDC
  `phone`, I can text back a link with the requested information
- I can send a contact request link from my online live wallet to which the
  contact response can be `POST`ed.

The `sub` (pairwise identifier) and `xpub` (or `xprv`) MUST always be provided.

The End-User may choose to provide additional requested information.

### 3. Payment Request

- `amount`
- `denoms`

The response to a payment request MAY include an `xprv` (shared account) or a
list of comma- (or space-) separated WIFs as a `wif`.

### 4. TODO

- Subscription URL
- Next `n` payment dates
- Balance URL

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
