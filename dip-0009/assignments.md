## Registered Features

Here is a table of current feature paths and any associated DIP. Future DIPs may introduce more types.


| Feature Index * | Feature | DIP Number and Name | Note |
| ------------------ | ------------ | ------------------- | ---- |
| `3'` | Masternode Keys | [DIP 0003: Deterministic Masternode List](https://github.com/dashpay/dips/blob/master/dip-0003.md) | The masternode related keys are located in the following sub-paths:  <br>`0'/*` - _Reserved_<br>`1'/*` - Voting Key<br>`2'/*` - Owner Key<br>`3'/*` - Operator Key<br><br>For example, the first voting key for Dash would be at `m/9'/5'/3'/1'/0` |

Note: all DIP 0009 paths are of the format: `m / 9' / coin_type' / feature' / *`

\* Where applicable, the feature index matches the number of the DIP that defines the feature(s)
