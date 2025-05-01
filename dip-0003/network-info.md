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

The fields below are represented as `networkInfo` and subsume the responsibility of `platformInfo`.
Applicability of fields based on masternode type will be defined by the field individually.

| Field     | Type    | Size     | Description                                                                                    |
| --------- | ------- | -------- | ---------------------------------------------------------------------------------------------- |
| p_count   | uint_8  | 1        | Number of purposes for which addresses are defined                                             |
| p_entries | byte[]  | variable | Array of pairings between purpose codes and arrays of addresses containing network information |

### `p_count` field

* The value of this field MUST correspond to the number of [`p_entries`](#p_entries-field)

### `p_entries` field

This field is an array of [`p_count`](#p_count-field) elements of type [`p_entry`](#p_entry-type) where:

* `p_entries[0]`
    * MUST have [`purpose`](#p_entrypurpose-field) code `CORE_P2P`
    * MUST be registered regardless of masternode type (as defined in [Appendix B](masternode-types.md)).
    * [`entries[0]`](#p_entryentries-field):
      * MUST have a [`type`](#entrytype-field) of `0x01` (IPv4 address).
      * On mainnet, MUST use [`port`](#entryport-field) of `9999`.
    * [`entries`](#p_entryentries-field) MUST NOT have a [`type`](#entrytype-field) of `0xD0` (domain name).
* `p_entries[1]`
    * MUST have [`purpose`](#p_entrypurpose-field) code `PLATFORM_P2P`.
    * MUST be registered for EvoNodes (type 1).
    * MUST NOT be registered for regular masternodes (type 0).
    * [`entries[0]`](#p_entryentries-field):
      * MUST have a [`type`](#entrytype-field) of `0x01` (IPv4 address).
      * MUST have the same [`address`](#entryaddress-field) as `p_entries[0][0]`
      * On mainnet, MUST use [`port`](#entryport-field) of `26656`.
    * [`entries`](#p_entryentries-field) MUST NOT have a [`type`](#entrytype-field) of `0xD0` (domain name).
* `p_entries[2]`
    * MUST have [`purpose`](#p_entrypurpose-field) code `PLATFORM_HTTPS`.
    * MUST be registered for EvoNodes (type 1).
    * MUST NOT be registered for regular masternodes (type 0).
    * [`entries[0]`](#p_entryentries-field):
      * MUST have a [`type`](#entrytype-field) of `0x01` (IPv4 address).
      * MUST have the same [`address`](#entryaddress-field) as `p_entries[0][0]`
      * On mainnet, MUST use [`port`](#entryport-field) of `443`.
    * [`entries`](#p_entryentries-field) MAY have a [`type`](#entrytype-field) of `0xD0` (domain name).
      * The element's [`address`](#entryaddress-field) MUST resolve to any [`address`](#entryaddress-field) in
        `p_entries[1]` of [`type`](#entrytype-field) `0x01` (IPv4 address) or `0x02` (IPv6 address)
        * This resolution check MUST be done during PoSe verification and is RECOMMENDED to be done by clients when
          attempting to connect to nodes using the [`address`](#entryaddress-field) supplied.

### `p_entry` type

| Field     | Type    | Size     | Description                                                                        |
| --------- | ------- | -------- | ---------------------------------------------------------------------------------- |
| purpose   | uint_8  | 1        | Network activity associated with address information                               |
| count     | uint_8  | 1        | Number of addresses through which the masternode is accessible                     |
| entries   | byte[]  | variable | Array of length `count` containing network information used to connect to the node |

#### `p_entry.purpose` field

The value of this field MUST be set to one of the values given below

| Purpose Code | Name             | Description                                              |
| ------------ | ---------------- | -------------------------------------------------------- |
| `0x01`       | `CORE_P2P`       | A node running Dash Core, exposing P2P functionality     |
| `0x02`       | `PLATFORM_P2P`   | A node running Dash Platform, exposing P2P functionality |
| `0x03`       | `PLATFORM_HTTPS` | A node running Dash Platform HTTPS API endpoints         |

#### `p_entry.count` field

* The value of this field MUST correspond to the number of [`entry`](#entry-type) elements in the
  [`entries`](#entries-field) field.

#### `p_entry.entries` field

This field is an array of [`p_entry.count`](#p_entrycount-field) elements of type [`entry`](#entry-type) where:

* There MUST be at least one element and at most thirty-two elements.

* Elements in `entries` MUST allow duplicate [`type`](#entrytype-field)s but MUST NOT allow duplicate
  [`address`](#entryaddress-field)es irrespective of associated [`type`](#entrytype-field) unless
  * It is registered under a dissimilar [`purpose`](#p_entrypurpose-field)
  * It is differentiated by [`port`](#entryport-field).

#### `entry` type

| Field   | Type    | Size     | Description                                                     |
| ------- | ------- | -------- | --------------------------------------------------------------- |
| type    | uint_8  | 1        | Network identifier                                              |
| address | byte[]  | variable | Address of `type` that can be used to connect to the masternode |
| port    | uint_16 | 2        | Port (network byte order)                                       |

##### `entry.type` field

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

The network identifier field MUST support the following [extensions](#extensions):

| Network ID | Address Length (bytes) | Description                            | Support |
| ---------- | ---------------------- | -------------------------------------- | ------- |
| `0xD0`     | variable               | Domain name (globally routed internet) | Yes     |

* Network IDs not enumerated in the above tables MUST NOT be permitted

##### `entry.address` field

* [`address`](#entryaddress-field) of [`type`](#entrytype-field)s originating from BIP 155 MUST be compliant with
  encoding standards as defined by BIP 155 (e.g.
  [TorV3](https://github.com/bitcoin/bips/blob/17c04f9fa1ecae173d6864b65717e13dfc1880af/bip-0155.mediawiki#appendix-b-tor-v3-address-encoding),
  [I2P](https://github.com/bitcoin/bips/blob/17c04f9fa1ecae173d6864b65717e13dfc1880af/bip-0155.mediawiki#appendix-c-i2p-address-encoding),
  [CJDNS](https://github.com/bitcoin/bips/blob/17c04f9fa1ecae173d6864b65717e13dfc1880af/bip-0155.mediawiki#appendix-d-cjdns-address-encoding)).
* `address` of [`type`](#entrytype-field)s originating from [extensions](#extensions) MUST be compliant with the
  specification as defined (e.g. [Internet domain names](#extension-a-internet-domain-names))

##### `entry.port` field

* This field MUST be any integer between 1024 and 65535 unless the [`purpose`](#p_entrypurpose-field) is `PLATFORM_HTTPS`,
  where they may opt for these ports in addition.

  | Port Number | Description                           |
  | ----------- | ------------------------------------- |
  | 443         | HTTP over TLS                         |

* This field MUST NOT permit a value considered "prohibited" (see below)

  <details>

  <summary>Prohibited ports:</summary>

  | Port Number | Description                           |
  | ----------- | ------------------------------------- |
  | 1719        | H.323 registration                    |
  | 1720        | H.323 call signaling                  |
  | 1723        | Point-to-Point Tunneling Protocol     |
  | 2049        | Network File System                   |
  | 3659        | Apple SASL                            |
  | 4045        | NFS lock daemon                       |
  | 5060        | Session Initiation Protocol (SIP)     |
  | 5061        | SIP over TLS                          |
  | 6000        | X11                                   |
  | 6566        | Scanner Access Now Easy (SANE) daemon |
  | 6665-6666   | Internet Relay Chat (Unofficial)      |
  | 6667        | IRC (Official)                        |
  | 6668-6669   | IRC (Unofficial)                      |
  | 6697        | IRC over TLS (Official)               |
  | 8332        | Bitcoin JSON-RPC server               |
  | 8333        | Bitcoin P2P                           |
  | 10080       | Amanda                                |
  | 18332       | Bitcoin JSON-RPC server (Testnet)     |
  | 18333       | Bitcoin P2P (Testnet)                 |

  </details>

* This field MUST be set to `0` if the port number is immaterial for the [`type`](#entrytype-field) of [`address`](#entryaddress-field)
  and MUST be ignored when attempting to make a connection. Listed are the [`type`](#entrytype-field)s where the port number is immaterial.

  | Network ID | Description                             |
  | ---------- | --------------------------------------- |
  | `0x05`     | I2P overlay network address             |

## Extensions

Extensions are supported types of addresses that are beyond the types enumerated in BIP 155. Their network IDs are defined
in the [`entry.type`](#entrytype-field) extensions table.

### Extension A: Internet domain names

Domain names resolved by DNS on the globally routed internet have the following [`entry.address`](#entryaddress-field) structure

| Field   | Type   | Size     | Description                                                     |
| ------- | ------ | -------- | --------------------------------------------------------------- |
| size    | uint_8 | 1        | Length of the domain name in bytes                              |
| name    | byte[] | variable | Domain name encoded in US-ASCII                                 |

DNS records for a domain name MUST have a valid `A` or `AAAA` entry.

#### `size` field

* This field MUST hold a value of at least 4
* This field MUST NOT hold a value greater than 253 pursuant to [RFC 1035](https://datatracker.ietf.org/doc/html/rfc1035#section-2.3.4),
  taking into consideration the leading and trailing bytes as specified in [Section 3.1](https://datatracker.ietf.org/doc/html/rfc1035#section-3.1)

#### `name` field

* This field MUST only permit letters, digits and a hyphen (`-`) in each label pursuant to
  [RFC 1035](https://datatracker.ietf.org/doc/html/rfc1035#section-2.3.1).
  * A label is defined as a string of 63 characters or less beginning with a letter and ending with a letter or number
    separated by the period (`.`) delimiter.
* This field MUST NOT permit upper-case letters despite being permitted by RFC 1035 in light of its case-insensitivity.
* This field MUST have a string containing at least two labels separated by the specified delimiter.
  * "Dotless domains" (as described by [RFC 7085](https://datatracker.ietf.org/doc/html/rfc7085#section-2)) MUST NOT be
    permitted.
* This field MUST NOT permit top level domains associated with private/internal networks, including but not limited to,
  the TLD assigned by [RFC 6762](https://datatracker.ietf.org/doc/html/rfc6762#section-3) for multicast DNS, alternatives
  to it enumerated in [Appendix G](https://datatracker.ietf.org/doc/html/rfc6762#appendix-G) or the special-use domain
  assigned by [RFC 8375](https://datatracker.ietf.org/doc/html/rfc8375).

# References

* [BIP 0155: addrv2 message](https://github.com/bitcoin/bips/blob/17c04f9fa1ecae173d6864b65717e13dfc1880af/bip-0155.mediawiki)
* [RFC 1035: Domain Names - Implementation and Specification](https://datatracker.ietf.org/doc/html/rfc1035)
* [RFC 6762: Multicast DNS](https://datatracker.ietf.org/doc/html/rfc6762)
* [RFC 7085: Top-Level Domains That Are Already Dotless](https://datatracker.ietf.org/doc/html/rfc7085)
* [RFC 8375: Special-Use Domain 'home.arpa.'](https://datatracker.ietf.org/doc/html/rfc8375)
