These are the currently supported LLMQ and DKG types. Each row is a single type. Each column refers to a parameter found
in [Parameters/Variables of a LLMQ and DKG](../dip-0006.md#parametersvariables-of-a-llmq-and-dkg).

| name | quorumType | quorumSize | quorumMinSize | quorumThreshold | quorumDkgInterval | quorumDkgPhaseBlocks | quorumDkgBadVotesThreshold | quorumSigningActiveQuorumCount | Notes |
|--|--|--|--|--|--|--|--|--|--|
| LLMQ_50_60 | 1 | 50 | 40 | 30 (60%) | 24 (1 Hour) | 2 | 40 | 24 | |
| LLMQ_400_60 | 2 | 400 | 300 | 240 (60%) | 288 (12 Hours) | 4 | 300 | 4 | |
| LLMQ_400_85 | 3 | 400 | 350 | 340 (85%) | 576 (24 Hours) | 4 | 300 | 4 | |
| LLMQ_100_67 | 4 | 100 | 80 | 67 (67%) | 24 (1 Hour) | 2 | 80 | 24 | |
| LLMQ_TEST | 100 | 3 | 2 | 2 (66%) | 24 (1 Hour) | 2 | 2 | 2 | For testing only |
| LLMQ_DEVNET | 101 | 10 | 7 | 6 (60%) | 24 (1 Hour) | 2 | 7 | 3 | For devnets only |
