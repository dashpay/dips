These are the currently supported LLMQ and DKG types. Each row is a single type. Each column refers to a parameter found
in [Parameters/Variables of a LLMQ and DKG](../dip-0006.md#parametersvariables-of-a-llmq-and-dkg).

| name | quorumType | quorumSize | quorumMinSize | quorumThreshold | quorumDkgInterval | quorumDkgPhaseBlocks | quorumDkgBadVotesThreshold | quorumSigningActiveQuorumCount | Notes |
|--|--|--|--|--|--|--|--|--|--|
| LLMQ_50_60 | 1 | 50 | 40 | 30 (60%) | 24 (1 Hour) | 2 | 40 | 24 | |
| LLMQ_400_60 | 2 | 400 | 300 | 240 (60%) | 288 (12 Hours) | 4 | 300 | 4 | |
| LLMQ_400_85 | 3 | 400 | 350 | 340 (85%) | 576 (24 Hours) | 4 | 300 | 4 | |
| LLMQ_100_67 | 4 | 100 | 80 | 67 (67%) | 24 (1 Hour) | 2 | 80 | 24 | |
| LLMQ_60_75 | 5 | 60 | 50 | 45 (75%) | 288 (12 Hours) | 2 | 48 | 32 | |
| LLMQ_25_67 | 6 | 25 | 22 | 17 (68%) | 24 (1 Hour) | 2 | 22 | 24 | For Testnet only |
| LLMQ_TEST | 100 | 3 | 2 | 2 (66%) | 24 (1 Hour) | 2 | 2 | 2 | For testing only (regtest) |
| LLMQ_DEVNET | 101 | 12 | 7 | 6 (50%) | 24 (1 Hour) | 2 | 7 | 4 | For devnets only |
| LLMQ_TEST_V17 | 102 | 3 | 2 | 2 (66%) | 24 (1 Hour) | 2 | 2 | 2 | For testing only (regtest) |
| LLMQ_TEST_DIP0024 | 103 | 4 | 4 | 2 (50%) | 24 (1 Hour) | 2 | 2 | 2 | For testing only (regtest) |
| LLMQ_TEST_INSTANTSEND | 104 | 3 | 2 | 2 (66%) | 24 (1 Hour) | 2 | 2 | 2 | For testing only (regtest). Same parameters as `LLMQ_TEST` |
| LLMQ_DEVNET_DIP0024 | 105 | 8 | 6 | 4 (50%) | 48 (2 Hours) | 2 | 7 | 2 | For devnets only |
| LLMQ_TEST_PLATFORM | 106 | 3 | 2 | 2 (66%) | 24 (1 Hour) | 2 | 2 | 2 | For testing only (regtest). Same parameters as `LLMQ_TEST` |
| LLMQ_DEVNET_PLATFORM | 107 | 12 | 9 | 8 (66%) | 24 (1 Hour) | 2 | 7 | 4 | For devnets only |
