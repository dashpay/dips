# Dash Improvement Proposals (DIPs)

DIP stands for Dash Improvement Proposal. Similar to Bitcoin's [BIPs](https://github.com/bitcoin/bips/), a DIP is a design document providing information to the Dash community, or describing a new feature for Dash or its processes or environment. The DIP should provide a concise technical specification of the feature and a rationale for the feature.

Because Dash is forked from the Bitcoin codebase, many of the BIPs can be applied to Dash as well (a list of the BIPs updated to include Dash-specific details can be found [here](https://github.com/dashevo/bips)). The purpose of the DIPs is not to duplicate those which exist as BIPs, but to introduce protocol upgrades or feature specifications which are unique to Dash.

## Contributions

We use the same general guidelines for introducing a new DIP as specified in [BIP 2](https://github.com/bitcoin/bips/blob/master/bip-0002.mediawiki), with a few differences. Specifically:

* Instead of the BIP editor, initiate contact with the Dash Core development team and your request should be routed to the DIP editor(s). The DIP workflow mimics the BIP workflow.
* Recommended licenses include the MIT license
* Markdown format is the preferred format for DIPs
* Following a discussion, the proposal should be submitted to the DIPs git repository as a pull request. This draft must be written in BIP/DIP style as described in [BIP 2](https://github.com/bitcoin/bips/blob/master/bip-0002.mediawiki), and named with an alias such as "dip-johndoe-infinitedash" until the editor has assigned it a DIP number (authors MUST NOT self-assign DIP numbers).

## Dash Improvement Proposal Summary

Number | Layer | Title | Owner | Type | Status
--- | --- | --- | --- | --- | ---
[1](dip-0001.md) | Consensus | Initial Scaling of the Network | Darren Tapp | Standard | Final
[2](dip-0002.md) | Consensus | Special Transactions | Samuel Westrich, Alexander Block, Andy Freer | Standard | Final
[3](dip-0003.md) | Consensus | Deterministic Masternode Lists | Samuel Westrich, Alexander Block, Andy Freer, Darren Tapp, Timothy Flynn, Udjinm6, Will Wray | Standard | Final
[4](dip-0004.md) | Consensus | Simplified Verification of Deterministic Masternode Lists | Alexander Block, Samuel Westrich, UdjinM6, Andy Freer | Standard | Final
[5](dip-0005.md) | Consensus | Blockchain Users | Alexander Block, Cofresi, Andy Freer, Nathan Marley, Anton Suprunchuk, Darren Tapp, Thephez, Udjinm6, Alex Werner, Samuel Westrich | Standard | Withdrawn
[6](dip-0006.md) | Consensus | Long-Living Masternode Quorums | Alexander Block | Standard | Final
[7](dip-0007.md) | Consensus | LLMQ Signing Requests / Sessions | Alexander Block | Standard | Final
[8](dip-0008.md) | Consensus | ChainLocks | Alexander Block | Standard | Final
[9](dip-0009.md) | Applications | Feature Derivation Paths | Samuel Westrich | Informational | Proposed
[10](dip-0010.md) | Consensus | LLMQ InstantSend | Alexander Block | Standard | Final
[11](dip-0011.md) | Consensus | Identities | Ivan Shumkov, Anton Suprunchuk, Samuel Westrich, Cofresi | Standard | Proposed
[12](dip-0012.md) | Consensus | Dash Platform Name Service | Ivan Shumkov, Anton Suprunchuk | Standard | Proposed
[13](dip-0013.md) | Applications | Identities in Hierarchical Deterministic Wallets | Samuel Westrich | Informational | Proposed
[14](dip-0014.md) | Applications | Extended Key Derivation using 256-Bit Unsigned Integers | Samuel Westrich | Informational | Proposed
[15](dip-0015.md) | Applications | DashPay | Samuel Westrich, Eric Britten | Standard | Proposed
[16](dip-0016.md) | Applications | Headers First Synchronization on Simple Payment Verification Wallets | Samuel Westrich | Informational | Proposed
[20](dip-0020.md) | Consensus | Dash Opcode Updates | Mart Mangus | Standard | Final
[21](dip-0021.md) | Consensus | LLMQ DKG Data Sharing | dustinface | Standard | Final
[22](dip-0022.md) | Consensus | Making InstantSend Deterministic using Quorum Cycles | Samuel Westrich, UdjinM6 | Standard | Final
[23](dip-0023.md) | Consensus | Enhanced Hard Fork Mechanism | Pasta | Standard | Final
[24](dip-0024.md) | Consensus | Long-Living Masternode Quorum Distribution and Rotation | Samuel Westrich & Virgile Bartolo | Standard | Final
[25](dip-0025.md) | Peer Services | Compressed Block Headers | gabriel-bjg, Thephez, UdjinM6 | Standard | Proposed
[26](dip-0026.md) | Consensus | Multi-Party Payout | Timothy Munsell, UdjinM6 | Standard | Proposed
[27](dip-0027.md) | Consensus | Dash Core Credit Pool | Ivan Shumkov, Anton Suprunchuk, Thephez, Samuel Westrich | Standard | Proposed
[28](dip-0028.md) | Consensus | Evolution Masternodes | Paul DeLucia, Odysseas Gabrielides, Łukasz Klimek, Ivan Shumkov, Samuel Westrich | Standard | Final
[29](dip-0029.md) | Consensus | Randomness Beacon For LLMQ Selection | Virgile Bartolo | Standard | Proposed
[30](dip-0030.md) | Consensus | Replay Attack Prevention and State Transition Nonces | Samuel Westrich | Standard | Proposed
[31](dip-0031.md) | Consensus | Platform Proof of Service | Ivan Shumkov, Pasta | Standard | Proposed

## License

Unless otherwise specified, Dash Improvement Proposals (DIPs) are released under the terms of the MIT license. See [LICENSE](LICENSE) for more information or see the [MIT License](https://opensource.org/licenses/MIT).
