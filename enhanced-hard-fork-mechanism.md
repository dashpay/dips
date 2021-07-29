<pre>
  DIP: 00xx
  Title: Enhanced Hard Fork Mechanism
  Author(s): Pasta
  Special-Thanks:
  Comments-Summary: No comments yet.
  Status: Proposed
  Type: Standard
  Created: 2021-07-29
  License: MIT License
</pre>

## Abstract

This DIP aims to introduce an improved hard fork activation mechanism that includes both masternodes and miners while also ensuring sufficient upgrade time is available to partners.

## Motivation

Currently, we utilize a heavily modified version of BIP-9 for hard fork activation in Dash Core. In the previous version of Dash Core, this calculation took into account the percentage of both miners and masternodes that had upgraded. However, since the introduction of the Deterministic Masternode List, the activations have purely been based on miner signalling.

## Previous Work

* [BIP-0009: Version bits with timeout and delay](https://github.com/bitcoin/bips/blob/master/bip-0009.mediawiki)
* [Dash dynamic activation thresholds](https://github.com/dashpay/dash/pull/3692)

## Current System

The current system declares a start timestamp. The first block of `height % 4032 == 0` with a timestamp greater than the start timestamp begins the first signalling cycle. Each signalling cycle has a threshold that must be met in order for the hard fork to lock-in. In our modified BIP-9 style activation, this threshold decreases at an exponential rate (slow at first then accelerating) from 80% down to 60% after 10 cycles have passed. In any cycle, if the final percentage of blocks signalling is greater than the threshold, the activation is locked in. Then after another cycle completes, the hard fork activates.

This system has a number of problems. First, it is actually problematic if the miners upgrade faster than the masternodes. This could lead to a situation where the miners fork, yet masternodes create ChainLocks on the “legacy” fork. In practice this has never been an issue, but it could be. Second, it is possible that this system results in very quick upgrades and forks (as quick as only 2 weeks) which are disruptive for services utilizing Dash. In practice this has resulted in the developers setting the startTime to a month or two after the release.

## New System

**Stage 0:** Miners signal, however this signalling does not have any effect on consensus. It is impossible to lock-in at this point. The purpose of this signalling is to enable monitoring of which miners have upgraded their software and get an idea of the adoption rate. Additionally, it is important to note that this signalling does not take up any space, and as such there is no incentive to minimize the time where signalling is done.

**Stage 1:** Any valid `LLMQ_400_85` must produce an `mn_hf_sig` message signalling that the masternode network has been upgraded. Since this is done by the `LLMQ_400_85` quorum, it will in effect only occur once 85% of the masternode network has upgraded to this version. Once this message has been created, it should be included in a block as a zero fee special transaction, similar to quorum commitments. This can be done by any miner in any block, but should only be included once. For testnet the `LLMQ_50_60` quorum should be used instead.

The `mn_hf_sig` message should look like:

| Field | Type | Size | Description |
|-|-|-|-|
| version | uint8_t | 1 | The version bits associated with the hard fork |
| quorumHash | uint256 | 32 | `quorumHash` of the quorum signing this message |
| sig | CBLSSig | 96 | BLS signature on version by public key associated with the quorum associated with `quorumHash` |

**Stage 2:** Once this `mn_hf_sig` message has been mined, two parameters are set: `masternode_activation_height` and `min_activation_height`. The cycle beginning at `masternode_activation_height` is the first cycle where mining signalling matters. It’s starting height is calculated based on the `mn_hf_sig` message height as shown here:

    masternode_activation_height = mined_height - (mined_height % 4032) + 4032

This cycle’s threshold is `nThresholdStart` (the maximum threshold value). Each subsequent cycle will see its threshold decreased until it reaches `nThresholdMin` (the minimum threshold value).

Regardless of miner signalling, activation only occurs once the height defined by the `min_activation_height` parameter is met. This is set to be 6 signalling windows (~6 weeks) after the `masternode_activation_height`. It is calculated as shown here:

    min_activation_height = masternode_activation_height + 4032 * 6

If the threshold is met at the end of a cycle activation_height is calculated as shown here:

    activation_height = max((height + 4032), min_activation_height)

# Copyright

Copyright (c) 2021 Dash Core Group, Inc. [Licensed under the MIT License](https://opensource.org/licenses/MIT)