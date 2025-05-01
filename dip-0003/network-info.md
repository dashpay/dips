# Appendix C: Network Information

## Masternode Information

The fields below are represented as `networkInfo` and are applicable to all masternodes types as defined in
[Appendix B](masternode-types.md)

| Field     | Type    | Size | Description                                                                |
| --------- | ------- | ---- | -------------------------------------------------------------------------- |
| ipAddress | byte[]  | 16   | IPv6 address in network byte order. Only IPv4 mapped addresses are allowed |
| port      | uint_16 | 2    | Port (network byte order)                                                  |

### <a name="mninfo_rules">Validation Rules</a>

* `ipAddress` MUST be a valid IPv4 address that is routable on the global internet
* `ipAddress` MUST NOT be already used in the registered masternodes set
* `port` MUST be within the valid port range [1, 65535]
* On mainnet, `port` MUST be set to the following value

  | Field  | Value  |
  | -------| ------ |
  | port   | 9999   |
