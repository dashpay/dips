# Compressed block headers

## Motivation

Block headers as exchanged by nodes over the p2p network are currently 81 bytes each.

For low bandwidth nodes who are doing a headers-only sync, reducing the size of the headers can provide a significant bandwidth saving. Also, nodes can support more header-only peers for IBD and protection against eclipse attacks if header bandwidth is reduced.

### Background

Currently headers are sent over the p2p network as a vector of `block_headers`, which are composed of the following sized fields:

|Field | Size |
| - | - |
|Version             | 4 bytes
|Previous block hash | 32 bytes
|Merkle root hash    | 32 bytes
|Time                | 4 bytes
|nBits               | 4 bytes
|nonce               | 4 bytes
|txn_count           | 1 byte
|*Total*             | 81 bytes

Some fields can be removed completely, others can be compressed under certain conditions.

## Prior work

This work is a derivation of the following:

* [bitcoin-dev: "Compressed" headers stream - August 2017](https://lists.linuxfoundation.org/pipermail/bitcoin-dev/2017-August/014876.html)
  * [Further discussion - December 2017](https://lists.linuxfoundation.org/pipermail/bitcoin-dev/2017-December/015385.html)
* [bitcoin-dev: Optimized Header Sync](https://lists.linuxfoundation.org/pipermail/bitcoin-dev/2018-March/015851.html)
* [Compressed block headers (Will Clark)](https://github.com/willcl-ark/compressed-block-headers/blob/v1.0/compressed-block-headers.adoc)

## Proposed specification

### block_header2 data type

The following table illustrates the proposed `block_header2` data type specification.

|Field               | Size     | Compressed |
| -                  | -        | -          |
|Bitfield            | 1 byte   | 1 byte
|Version             | 4 bytes  | 0 \| 4 bytes
|Previous block hash | 32 bytes | 0 \| 32 bytes
|Merkle root hash    | 32 bytes | 32 bytes
|Time                | 4 bytes  | 2 \| 4 bytes
|nBits               | 4 bytes  | 0 \| 4 bytes
|nonce               | 4 bytes  | 4 bytes
|*Total*             | 81 bytes | range: 39 - 81 bytes

This compression results in a maximum reduction from an 81 byte header to best-case 39 byte header. In bitcoin a continuous header sync from genesis (requiring a single full 81 byte header followed by only compressed `block_header2`) to height 629,474 was tested using this method and it resulted in a bandwidth reduction from 50.98MB down to 25.86MB, a saving of 49%.

#### Bitfield

To make parsing of header messages easier and further increase header compression, a single byte bitfield was suggested by [gmaxwell](https://lists.linuxfoundation.org/pipermail/bitcoin-dev/2017-December/015397.html). We propose the following amended bitfield meanings (bits re-ordered to match `headers2` field order):

|Bit | Meaning + field size to read |
| -  | -                            |
|0<br>1<br>2    | version: same as the last *distinct* value 1st ... 7th (0 byte field) or a new 32bit distinct value (4 byte field).
|3   | prev_block_hash: is omitted (0 byte field) or included (32 byte field)
|4   | timestamp: as small offset (2 byte field) or full (4 byte field).
|5   | nbits: same as last header (0 byte field) or new (4 byte field).
|6   | possibly to signal "more headers follow" to make the encoding self-delimiting.
|7   | currently undefined

This bitfield adds 1 byte for every block in the chain.

#### Version

In most cases the Version field will be identical to one referenced in one of the previous 7 unique versions, as indicated by bits 0,1,2 of the Bitfield.

In bitcoin testing to block 629,474, there were 616,137 blocks whose version was in the previous 7 distinct versions and only 13,338 blocks that were not.

| Genesis to block | Current (B) | Compressed (B) | Saving (%) |
| -                | -           | -              | -          |
| 629,474          | 2,517,896   | 53,352         |98          |

#### Previous block hash

The previous block hash will always be the X11 hash of `previous_header` so it is redundant given that you have the previous header in the chain.

| Genesis to block | Current (B) | Compressed (B) | Saving (%) |
| -                | -           | -              | -          |
| 629,474          | 20,143,168  | 0              | 100

#### Time

The timestamp (in seconds) is consensus bound, based both on the time in the previous header: `MAX_FUTURE_BLOCK_TIME = 2 * 60 * 60 = 7200`, and being greater than the `MedianTimePast` of the previous 11 blocks. Therefore this can be safely represented as an offset from the previous headers' timestamp using a 2 byte `signed short int`.

| Genesis to block | Current (B) | Compressed (B) | Saving (%) |
| -                | -           | -              | -          |
| 629,474          | 2,517,896   | 1,258,952      | 50

#### nBits

nBits currently changes once every 2016 blocks. It could be entirely calculated by the client from the timestamps of the previous 2015 blocks footnote:[2015 blocks are used in the adjustment calculation due to an off-by-one error: https://bitcointalk.org/index.php?topic=43692.msg521772#msg521772"].

To simplify 'light' client implementations which would otherwise require consensus-valid calculation of the adjustments, we propose to transmit this according to the <<Bitfield>> specification above.

To block 629,474 there have been 298 nBits adjustments (vs an expected 311 -- there was none before block 32,256).

| Genesis to block | Current (B) | Compressed (B) | Saving (%) |
| -                | -           | -              | -          |
| 629,474          | 2,517,896   | 1,196          | 99.6

#### txn_count

txn_count is included to make parsing of these messages compatible with parsing of `block` messages footnote:[https://bitcoin.stackexchange.com/questions/2104/why-is-the-block-header-txn-count-field-always-zero]. Therefore this field and its associated byte can be removed for transmission of compact headers.

| Genesis to block | Current (B) | Compressed (B) | Saving (%) |
| -                | -           | -              | -          |
| 629,474          | 629,474     | 0              | 100

### Service Bit

A new service bit would be required so that the nodes can advertise their ability to supply compact headers.

### P2P Messages

Three new messages would be used by nodes that enable compact block header support, two query messages: `getheaders2` and `sendheaders2` and one response: `headers2`.

#### `getheaders2` -- Requesting compact headers

The new p2p message required to request compact block headers would require the same fields as the current `getheaders` message:

|Field Size | Description          | Data type | Comments
| -         | -                    | -         | -
|4          |version              |uint32_t  |the protocol version
|1+         |hash count           |var_int   |number of block locator hash entries
|32+        |block locator hashes |char[32]  |block locator object; newest back to genesis block (dense to start, but then sparse)
|32         |hash_stop            |char[32]  |hash of the last desired block header; set to zero to get as many blocks as possible (2000)

#### `sendheaders2` -- Request compact header announcements

Since [BIP-130](https://github.com/bitcoin/bips/blob/master/bip-0130.mediawiki), nodes have been able to request to receive new headers directly in `headers` messages, rather than via an `inv` of the new block hash and subsequent `getheader` request and `headers` response (followed by a final `getdata` to get the tip block itself, if desired). This is requested by transmitting an empty `sendheaders` message after the version handshake is complete.]

Upon receipt of this message, the node is permitted, but not required, to preemptively announce new headers with the `headers2` message (instead of `inv`). Preemptive header announcement has been supported by the protocol version ≥ 70206 | Dash Core version ≥ 0.12.1.

For the motivational use-case it makes sense to also update this mechanism to support sending header updates using compact headers using a new message.

#### `headers2` -- Receiving compact headers

A `headers2` message is returned in response to `getheaders2` or at new header announcement following a `sendheaders2` request. It contains both `length` and `headers` fields. The `headers` field contains a variable length vector of `block_header2`:

|===
| Field Size | Description | Data type       | Comments
| -          | -           | -               | -
|1+         |length      |var_int         |Length of `headers`
|39-81x?    |headers     |block_header2[] |Compressed block headers in [block_header2 data type](#block_header2-data-type) format

### Implementation

* The first header in the first `block_header2[]` vector to a newly-connected client MUST contain the full `nBits`, `timestamp`, `version` and `prev_block_hash` fields, along with a correctly populated `bitfield` byte.
* Subsequent headers in a contiguous vector SHOULD follow the compressed [block_header2 data type](#block_header2-data-type) format.
* Subsequent compressed headers supplied to an already-connected client (requesting compressed headers), SHOULD follow the compressed [block_header2 data type](#block_header2-data-type) format.
