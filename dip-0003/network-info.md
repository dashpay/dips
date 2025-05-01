# Appendix C: Network Information

## Legacy Format

### Masternode Information

The fields below are represented as `networkInfo` and are applicable to all masternodes types as defined in
[Appendix B](masternode-types.md)

| Field     | Type    | Size | Description                                                                |
| --------- | ------- | ---- | -------------------------------------------------------------------------- |
| ipAddress | byte[]  | 16   | IPv6 address in network byte order. Only IPv4 mapped addresses are allowed |
| port      | uint_16 | 2    | Port (network byte order)                                                  |

#### <a name="mninfo_rules">Validation Rules</a>

* `ipAddress` MUST be a valid IPv4 address that is routable on the global internet
* `ipAddress` MUST NOT be already used in the registered masternodes set
* `port` MUST be within the valid port range [1, 65535]
* On mainnet, `port` MUST be set to the following value

  | Field  | Value  |
  | -------| ------ |
  | port   | 9999   |

### Platform Information

The fields below are represented as `platformInfo` and are only applicable for EvoNodes as defined in
[Appendix B](masternode-types.md)

| Field            | Type    | Size   | Description                                                         |
| ---------------- | ------- | ------ | ------------------------------------------------------------------- |
| platformP2PPort  | uint_16 | 0 or 2 | TCP port of Dash Platform peer-to-peer communication between nodes. |
| platformHTTPPort | uint_16 | 0 or 2 | TCP port of Platform HTTP/API interface.                            |

#### <a name="plinfo_rules">Validation Rules</a>

* `platformP2PPort` and `platformHTTPPort` MUST be within the valid port range [1, 65535]
* `platformP2PPort`, `platformHTTPPort`, and [`port`](#masternode-information) from `networkInfo` MUST be distinct
* On mainnet, `platformP2PPort` and `platformHTTPPort` MUST be set to the following values

  | Field              | Value  |
  | ------------------ | ------ |
  | platformP2PPort    | 26656  |
  | platformHTTPPort   | 443    |

## Extended Format

The fields below are represented as `networkInfo` and are applicable to all masternodes types as defined in
[Appendix B](masternode-types.md).

| Field   | Type    | Size     | Description                                                                              |
| ------- | ------- | -------- | ---------------------------------------------------------------------------------------- |
| count   | uint_8  | 1        | Number of addresses through which the masternode is accessible                           |
| entries | byte[]  | variable | Array of length `count` containing network information used to connect to the masternode |
| port    | uint_16 | 2        | Port (network byte order)                                                                |

### `count` field

* The value of this field MUST correspond to the number of [`entry`](#entry-type) elements in the
  [`entries`](#entries-field) field.

### `entries` field

This field is an array of [`count`](#count-field) elements of type [`entry`](#entry-type) where:

* There MUST be at least one element and at most thirty-two elements.

* `entries[0]` MUST have a [`type`](#entrytype-field) of `0x01` (IPv4 address).

* On mainnet, `entries[0]` must be set to the following value

  | Field  | Value  |
  | -------| ------ |
  | port   | 9999   |

* Elements in `entries` MUST allow duplicate [`type`](#entrytype-field)s but MUST NOT allow duplicate
  [`address`](#entryaddress-field)es irrespective of associated [`type`](#entrytype-field).

#### `entry` type

| Field   | Type   | Size     | Description                                                     |
| ------- | ------ | -------- | --------------------------------------------------------------- |
| type    | uint_8 | 1        | Network identifier                                              |
| address | byte[] | variable | Address of `type` that can be used to connect to the masternode |

#### `entry.type` field

The network identifier field MUST comply with the following table of BIP 155 [network IDs](https://github.com/bitcoin/bips/blob/17c04f9fa1ecae173d6864b65717e13dfc1880af/bip-0155.mediawiki#specification):

| Network ID | Address Length (bytes) | Description                             | Support |
| ---------- | ---------------------- | --------------------------------------- | ------- |
| `0x01`     | 4                      | IPv4 address (globally routed internet) | Yes     |
| `0x02`     | 16                     | IPv6 address (globally routed internet) | Yes     |
| `0x03`     | 10                     | Tor v2 hidden service address           | No      |
| `0x04`     | 32                     | Tor v3 hidden service address           | Yes     |
| `0x05`     | 32                     | I2P overlay network address             | Yes     |
| `0x06`     | 16                     | CJDNS overlay network address           | Yes     |
| `0x07`     | 16                     | Yggdrasil overlay network address       | No      |

#### `entry.address` field

* [`address`](#entryaddress-field) of [`type`](#entrytype-field)s originating from BIP 155 MUST be compliant with
  encoding standards as defined by BIP 155 (e.g.
  [TorV3](https://github.com/bitcoin/bips/blob/17c04f9fa1ecae173d6864b65717e13dfc1880af/bip-0155.mediawiki#appendix-b-tor-v3-address-encoding),
  [I2P](https://github.com/bitcoin/bips/blob/17c04f9fa1ecae173d6864b65717e13dfc1880af/bip-0155.mediawiki#appendix-c-i2p-address-encoding),
  [CJDNS](https://github.com/bitcoin/bips/blob/17c04f9fa1ecae173d6864b65717e13dfc1880af/bip-0155.mediawiki#appendix-d-cjdns-address-encoding)).

### `port` field

* This field MUST be any integer between 1024 and 65535.

* This field MUST be ignored for connecting to [`entry.address`](#entryaddress-field) of [`entry.type`](#entrytype-field)
  where ports are immaterial.

# References

* [BIP 0155: addrv2 message](https://github.com/bitcoin/bips/blob/17c04f9fa1ecae173d6864b65717e13dfc1880af/bip-0155.mediawiki)
