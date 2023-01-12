<pre>
  Title: DIP-24 Addendum - Parameter Choices
  Author(s):  Virgile Bartolo
  Special-Thanks: Samuel Westrich
  Comments-Summary: No comments yet.
  Type: Supporting Document
  Created: 2022-09-15
  License: MIT License
</pre>

# Table of Contents

1. [Abstract](#abstract)
1. [Prior Work](#prior-work)
1. [Structure of the document](#structure-of-the-document)
1. [Introduction](#introduction)
    * [Overview of mining attacks](#overview-of-mining-attacks)
    * [Near future considerations](#near-future-considerations)
1. [Mining Attacks](#mining-attacks)
    * [Security Considerations & Threat Model](#security-considerations--threat-model)
    * [Double Signing Threshold](#double-signing-threshold)
    * [Probabilities Of Success: Numerical Values](#probabilities-of-success-numerical-values)
    * [Success Rate Of The Attack: The Theory](#success-rate-of-the-attack-the-theory)
    * [Monetary Scope Of The Attack: A Toy Model](#monetary-scope-of-the-attack-a-toy-model)
1. [Conclusion](#conclusion)
1. [Copyright](#copyright)

# Abstract

With the upcoming release of Dash Platform, a higher security model is required for InstantSend
locks. As such, in [DIP-24](../dip-0024.md), a new quorum renewal mechanism called rotation has been
introduced for InstantSend quorums. In this addendum, we will explain the security considerations
behind [DIP-24](../dip-0024.md) in more detail.

# Prior work

* [DIP-0006: Long-Living Masternode
  Quorums](https://github.com/dashpay/dips/blob/master/dip-0006.md)
* [DIP-0008: ChainLocks](https://github.com/dashpay/dips/blob/master/dip-0008.md)
* [DIP-0010: LLMQ InstantSend](https://github.com/dashpay/dips/blob/master/dip-0010.md)
* [DIP-0024: Long-Living Masternode Quorum Distribution and
  Rotation](https://github.com/dashpay/dips/blob/master/dip-0024.md)

# Structure of the document

We will briefly describe mining attacks and quickly discuss near-term security implementations. Then
we will dive into greater detail so interested users can gain greater insight into the mathematics
and the attack model. Finally, we will present the results in the conclusion to assist users in
better understanding the design choices.

# Introduction

## Overview of mining attacks

[DIP-24](../dip-0024.md) considers attacks that we name _double sign attacks_. Therein it is assumed
that attackers have a certain number of nodes in the quorum without evaluating the actual difficulty
of introducing this number of byzantine nodes into the quorum. This introduction of byzantine nodes
is done through what we call mining attacks. We will present a probability model for this creation
of bias because the success rate is the relevant parameter for mining attacks.

For clarity, it is critical to recognize the difference between the _double sign attacks_ presented
in [DIP-24](../dip-0024.md) and _mining attacks_ which we describe in greater detail in that
document. Mining attacks serve _only_ to sway the random distribution of nodes in the system and
artificially render edge cases of the distribution more likely. Consequently, a realized atypical
distribution would enable _double sign attacks_ by giving would-be attackers the majority of nodes
in a quorum.

Indeed, an entity controlling a large amount of hash power could attempt to alter the otherwise
uniform distribution of masternodes inside quorums to increase their chances of getting control over
a single targeted quorum. The attack consists of finding valid hashes quickly and discarding those
not providing enough byzantine entries to gain control of the targeted quorum.

Here and in the following sections, _taking control_ means being able to perform a double sign as
presented in [DIP-24](../dip-0024.md). Otherwise, the same reasoning holds, and the logic of the
calculations remains identical for taking total control of a quorum (the attacker would then be able
to sign messages of any kind with the quorum). Instead of considering the _Double Sign Threshold_
(DST), one would simply consider the usual threshold.

## Near future considerations

The costs of such mining attacks are substantial, but the rewards are too. In any case, a successful
attack would be unacceptable; thus, we cannot let such bias be created. Quorum rotation inherently
limited the degree of protection that could be provided without increasing thresholds significantly,
a change that could render the system less resistant to a small number of byzantine nodes denying
service. Therefore, we decided to make InstantSend quorums of size 60 with a threshold of 75%. These
parameters provide sufficient resistance against attackers with access to a hashrate equivalent to
that of the rest of the network and keep both the threshold and quorum size secure until a more
seamless design is adopted and rolled out. It should be noted that double sign attacks are, in their
own right, inherent to the setting of group voting in networks.

# Mining Attacks

We will now present the mining attack in more detail. First, we will define our threat model, then
introduce the concept of a Double Signing Threshold. Following that, we will showcase the attack’s
success rate. Finally, we will quickly analyze the attack with an overly simplified model under a
monetary scope.

## Security Considerations & Threat Model

Quorum members are chosen by ordering a list of masternodes by calculating `sha256(sha256(proTxHash,
confirmedHash), sha256(sha256(llmqType, cycleBlockHash)))`. Thus by having a limited ability to
select the quorumHash, miners can influence the hashed values that order the masternodes, albeit
restricted by their hash power.

We first notice that the upper bound of this attack is set by the number of byzantine nodes and the
amount of hash power the attacker can generate.

In this document, we make the following security consideration:

1. An attacker has control over at most 20% of the masternode network.
2. An attacker has access to at most 2 times the combined hashrate of the rest of the network.
3. We also assume that it is possible for an attacker to easily communicate with subsets of quorums
   faster than messages can be relayed between those subsets. For example, if the attacker sends one
   message to 20 nodes in a quorum and another message to a different subset of 20 nodes in the same
   quorum, both subsets will receive and sign the attacker’s initial messages before the message is
   relayed from the other group.
4. The network has 5000 masternodes.

## Double Signing Threshold

As presented in [DIP-24](../dip-0024.md), the _Double Sign Threshold_ (DST) is the percentage of the
quorum an attacker must control to sign _correct_ but _contradictory_ locks while under assumption
3. This percentage is lower than the actual quorum threshold.

This DST is equal to:

$$DST=(2*t-1/S - 1) |U|$$

with $t$ the actual threshold of the quorum, $S$ the number of shares, and $|U|$ the size of the
quorum.

In the following, when we refer to threshold, we mean the actual threshold of the quorums. The
percentage required to double sign will be called DST (Double Sign Threshold).

## Probabilities Of Success: Numerical Values

### The Case Of Usual Quorums

These are the probabilities to attain the DST against a 400 masternode quorum that doesn’t use
rotation and has a threshold of 60% (= 0.2 DST). However, this attack is pointless, as previously
stated, and the numbers are calculated just for educational purposes.

|Hash power | 10% (500)<br>byzantine masternodes | 20% (1000)<br>byzantine masternodes | 1/3 (1667)<br>byzantine masternodes |
| - | - | - | - |
| 1 | 2.37e-8% | 52% | 99% |
| 2 | 4.73e-6% | 77%* | 99% |
| 5 | 1.18e-7% | 97%* | 99% |

\* As is expected, a subset representing 20% of the masternodes will, on average, be present in each
quorum with equal proportion.

400 masternodes, 66% (= 0.33 DST) threshold:

|Hash power | 10% (500)<br>byzantine masternodes | 20% (1000)<br>byzantine masternodes | 1/3 (1667)<br>byzantine masternodes |
| - | - | - | - |
| 1 | 8.80e-39% | 1.12e-8% | 52% |
| 2 | 1.76e-38% | 2.24e-8% | 77%* |
| 5 | 4.40e-38% | 5.59e-8% | 97%* |

\* Once again, this is unsurprising.

### The Case Of InstantSend Quorums (using rotation)

In the following table, the $hashpower$ indicated is the hash power sustained through each of the
four cycles.

60 masternodes, 75%  (= 0.25 DST) threshold, rotation on:

|Hash power | 10% (500)<br>byzantine masternodes | 20% (1000)<br>byzantine masternodes |
| - | - | - |
| 1 | 2.25e-7% | 0.018% |
| 2 | 1.76e-6% | 0.12% |
| 5 | 2.63e-5% | 1.29%* |
| 10 | 1.97e-4% | 6.26% |

\* This is what we want to avoid in the near future, a set of byzantine nodes smaller than the DST
by a non-negligible margin which still has a non-negligible chance of attaining it.

The next section will showcase the formulas behind the attack success rate. Independent
verifications of the calculations and models are more than welcome to be forwarded to
research[at]dash[dot]org.

## Success Rate Of The Attack: The Theory

We will present the mining attack against a normal quorum first and then on rotation quorums. While
attacking a non-InstantSend quorum is pointless, we still show it as a simple example demonstrating
the foundation of the attack.

Both attacks will rely on the same principle:

* The attacker has $hashPower$ valid hashes per round.
* They hash blocks and either discard the hashes, or if one gives them control, they broadcast it to
  the rest of the network so that the block is included in the blockchain.

Besides that, there will be slight differences in how the attack is carried out.

Some parameters with slightly less influence will be ignored, such as the fact that the network
itself can find a hash giving control to the attacker (this is somewhat less advantageous for the
attacker than having one more $hashPower$).

### The Case Of Usual Quorums

We recall that to choose members of a non-rotating quorum, we randomly order masternodes and pick
the first ones as members. For the attacker, getting a valid hash is equivalent to blindly picking
$quorumSize$ balls at once in a bag containing $n$ balls, with $c$ balls being black and the rest
being white. If more than DST black balls are selected, then the attack is a success. In
mathematical terms, this is an _experiment_ following the cumulative distribution of the
hyper-geometric law with parameters:

* $n$ the total number of masternodes in the network.
* $c$ the number of byzantine nodes in the network.
* $qs$ the quorum size.
* $t$ the targeted number of byzantine nodes in the quorum.

We note the probability of that experiment $P(control | hash)$. It is calculated with the following
formula:

Let $X_{byz}$ be the variable counting the number of byzantine nodes picked by a valid hash.

$$
\begin{equation*}
\begin{aligned}
P(control|hash) &= P(X_{byz} \geq t)\\
&=\sum_{k=t}^{k=q_s}P(X_{byz}=k)\\
&=\sum_{k=t}^{k=q_s} \frac{ \binom{c}{k} \binom{n-c}{q_s-k}}{\binom{n}{q_s}}\\
\end{aligned}
\end{equation*}
$$

We now know the probability of one valid hash giving control to the attacker. The attacker gets to
choose from $hashPower$ valid hashes, and they only need one of those hashes to gain control of the
quorum. To calculate it, we look at this event another way, as is common practice in probabilities.
It is the same event as: "not every valid hash failed to give control."

Thus the probability of success of the attack is:

$$
\begin{equation*}
\begin{aligned}
P(control) &=1- [P(no\ control|hash)]^{Hashpower}\\
&=1- [1- P(control|hash)]^{Hashpower}\\
\end{aligned}
\end{equation*}
$$

### The Case Of InstantSend Quorums And Rotation

The first step of the attack consists of waiting for a quorum to have as few byzantine nodes as
possible in a quorum; this will be the target quorum.

We will make a logical error here to simplify the calculations. This results in a slight
overestimate of the attack but speeds up calculations. The simplification is to assume that the
attacker has no nodes in the 3 most recent shares of the targeted quorum at the start of the attack.
On average, their byzantine nodes would actually be distributed evenly among the quorums.

After this initial step, they must take control of the target quorum over a span of 3 cycles. To
gain control of the quorum, the attacker needs $T_{tot}=(2t-1-1/4)%$ byzantine nodes in the quorum.
They do so by picking $hashPower$ valid hashes every cycle, choosing the hash that inserts the most
byzantine nodes into the quorum, and broadcasting it to the rest of the network. Then, that
experiment is repeated 3 times.

We thus consider the following simplified experiment to model the attack:

* The attacker has $hashPower$ (denoted $hp$) valid hashes to choose from before the network finds
  share 1.
* The same process is followed in the subsequent two cycles. The attacker gets to choose among $hp$
  hashes before the network finds shares 2 and 3.
* At the start of the attack, the attacker has 0 byzantine nodes in the 3 most recent shares of the
  target quorum.

These considerations will make the calculations possible while producing results that remain
somewhat close to the real-life experiment.

A valid hash will insert a certain number of byzantine nodes to the current share; this is
equivalent to the hash blindly picking $shareSize$ balls all at once from a bag containing black and
white balls. Once again, this is an experiment following a hyper-geometric law.

Let $X_{i}$ be the variable counting the number of byzantine nodes inserted in the $i^{th}$ share by
the attacker. Then, to get control of the quorum, the attacker needs $X_1+X_2+X_3\geq T$ (where
$X_1+X_2+X_3$ refer to the three oldest shares of the new quorum).

Thus, to calculate the probability of success, we loop over the possible values $(x_1,x_2,x_3)$ of
$(X_1,X_2,X_3)$, calculating $P = P(X_1)*P(X_2)*P(X_3)$ when the sum of the $x_{i}$ is over $T$ and
then summing all those probabilities together:

$$P(control)=\sum_{x_1+x_2+x_3\geq T} P(X_1=x_1)*P(X_2=x_2)*P(X_3=x_3)$$

Note: each experiment depends on the previous ones, so while the calculations are correct, this
notation is technically not proper. This is because this document is not, per se, a mathematical
paper; its goal is to explain the logic behind [DIP-24](../dip-0024.md) choices to a broader
audience.

To calculate this sum, we need to calculate $P(X_i=x_i)$. $X_i$ is a repetition of $hp$ times the
same experiment that we call $X_i^{(k)}$. Then the maximum is taken, and thus, the event is
$\max(X_i^{(1)},\ ...,X_i^{(hp)})$.

$X_{i}^{(k)}$ is the $k^{th}$ experiment corresponding to the $k^{th}$ hash selecting balls at cycle
$i$.

With that in mind, we calculate the probability of a value $x_{i}$ being attained (explanations just
below):

$$
\begin{equation*}
\begin{aligned}
P(X_i=x_i)&=P(X_i\leq x_i\cap X_i >x_i-1)\\
&=P(X_i\leq x_i)-P(X_i\leq x_i-1)\\
&=P(X_i^{(1)}\leq x_i\cap\ ...\ \cap X_i^{(hp)}\leq x_i) -P(X_i^{(1)}\leq x_i-1\cap\ ...\ \cap X_i^{(hp)}\leq x_i-1)\\
&=P(X_i^{(1)}\leq x_i)^{hp} - P(X_i^{(1)}\leq x_i-1)^{hp}
\end{aligned}
\end{equation*}
$$

* The first equality is self-explanatory.
* The second line is because the event $X_i\leq x_i-1$ is included in $X_i\leq x_i$.
* The third line means that the maximum of multiple values is under a threshold if and only if they
  all are.
* The last line is because the variables are independent and identically distributed.

Now, we need to calculate $P(X_i^{(1)}\leq x_{i}) = \sum_k P(X_i^{(1)}= k)$ for $k$ between 0 and
$x_i$.

For that, we need $P(X_i^{(1)}= k)$ for all $i$. We look closely at the experiments:

* $X_1^{(1)}$ is simply the hypergeometric law. $X_1^{(1)}\sim \operatorname{Hypergeometric} (M_a, c, qs)$ with $M_a$ being the total number of available masternodes to choose from, equal to $n - qs * 3/4$.
* $X_2^{(1)}$ is the hypergeometric law $X_2^{(1)}\sim \operatorname{Hypergeometric} (M_a, c - x_1, qs)$. Indeed now there are $x_1$ fewer byzantine nodes to choose from.
* $X_3^{(1)}$ is the hypergeometric law $X_3^{(1)}\sim \operatorname{Hypergeometric} (M_a, c - x_1 - x_2, qs)$.

These are known laws and thus easily calculated for specific values. We now have all the information
required for the calculations.

### Miscellaneous considerations on the attack

1. Quorums with a low index are slightly more likely to be successfully attacked if the number of
   nodes used by the system is greater than half the total number of masternodes in the masternode
   lists. This is because the selection algorithm goes through the unused nodes first. To deviate
   from the average cases, a hash should contain more byzantine nodes in the targeted quorum while
   having as few nodes as possible in other quorums. Thus the byzantine nodes will be found in the
   first part of the sorted list during the selection phase presented in [DIP-24](../dip-0024.md).
2. An adversary could also try to spread their hash power over multiple less efficient attacks;
   however, this is less likely to succeed and thus not optimal for an attacker.
3. Each valid hash determines the composition of QuorumNumber quorum shares. These are **not**
   independent experiments and, as such, are out of this paper’s scope as they would be too lengthy
   to model. Additionally, the difference in success chances would be minimal given that it would be
   highly unlikely to have multiple quorums meet the required criteria during the first rounds. This
   could be modeled by having QuorumNb hypergeometric laws every cycle but with a catch. While the
   first one would have perfect conditions, the others would be worse for the attacker since nodes
   would very likely be taken away by previous quorum indexes (at a rate of $c/n * shareSize$ of
   byzantine nodes per index on average).
4. The value $c/n-t$ is an important parameter, as seen in the tables. Its importance is exacerbated
   by the size of quorums _and_ the total number of masternodes in the system.  

## Monetary Scope Of The Attack: A Toy Model

A mining attack on InstantSend would enable a form of money duplication. As such, the motives for
this attack would most likely be monetary. We will now outline a toy model of the scope of the
attack.

The average turnover of this attack is denoted E[A]. Ideally, the goal would be that E[A] is less
than (or close to) 0. This would mean that, on average, the attack produces minimal benefit for the
attacker. Moreover, financial attackers would be fully deterred if the attack had a return on
investment (ROI) less than that of the average mildly risky investment.

The formula for average turnover is:

$$E[A] = GainOnFailure * ProbaOfFailure + GainOnSuccess * ProbaOfSuccess$$

GainOnFailure is just the cost of the attack, and it is negative. GainOnSuccess is the economic gain
minus the cost of the attack. The probability of the attack failing is 1 - ProbaOfSuccess.

The estimations will use dramatically oversimplified models for the costs to simplify calculations.
Note that this is simply a toy model and shouldn't be used for any estimation because costs for an
attacker are heavily underestimated and are not representative of reality.

### Simplification Of The Cost Model

The attack has multiple sources of cost:

1. **The cost of acquiring the hardware** needed to carry out the attack. An attacker could either
   accumulate it gradually and risk hardware obsolescence or acquire it quickly at an enormous
   premium due to market forces for such a massive buy. Alternatively, they could manufacture the
   hardware to avoid such a situation. That would then expose the attacker as a state actor, a large
   hardware company, or a potent crime organization.
2. **The cost of discarding hashes** that are valid but do not give them control of the quorum. The
   cost of a single hash equals the pure CPU cost plus the reward being ignored. This might seem
   counterintuitive since the reward is purely speculative, but this is an actual loss for an
   adversary aiming at financial gain. As such, the attacker’s **hashing cost** is bounded by the
   mining reward on the lower side and by twice the reward on the upper side.
3. **The stake** that the attacker needs to be in control of masternodes. If such a critical attack
   were to be carried out, the value associated with those masternodes would decrease quickly and
   substantially. This devaluation is hard to estimate as it is entirely dependent on the market’s
   reaction to the attack; it is a major cost of such an attack.

It is noteworthy that obtaining control of a sizable number of masternodes isn’t trivial. Buying 20%
of the existing masternodes would be (with DASH = 100 USD) an investment of:

$5000 * 0.2 * 1000$ = 1 million DASH = 100 million USD

While creating enough nodes on top of the ~5000 existing ones would be an investment of:

$1300*1000$ = 1.3 million DASH = 130 million USD

Thus, an effective way to increase the attack’s cost is to increase both the inertia of withdrawing
DASH from collaterals and the inertia of withdrawing credits to the main chain.

In comparison, at the moment of writing this document, the total daily volume of DASH is 200 million
USD.

It is also worth noting that the price of Dash is not proportional to the turnover of the attack.
Below a certain threshold, higher prices should lend more average turnover by disproportionately
increasing the GainOnSuccess more than they decrease the ProbaOfFailure. But above this threshold, a
price that is too high decreases the viability of the attack. This is mainly due to the impact of
the hash power: increases in hashing power result in non-proportional increases in success rate.

### Cost of discarding hashes

In this section, we consider the cost of abandoned rewards to highlight how to model such an attack
under a monetary scope.

We consider an attacker with access to $hashPower$ times the hash power of the rest of the network
combined. This means that, on average, they will get $hashPower$ valid hashes by the time the
network finds one. To simplify, we assume that the attacker always outputs $hashPower$ hashes on an
attack round.

We now calculate the reward of a single hash:

    Oct 26, 2021: 1.23 DASH * $198/DASH = $244
    Jan 14, 2022: 1.21 DASH * $141/DASH = $171
    Feb 28, 2022: 1.20 DASH * $89/DASH  = $107

As stated beforehand, we take the baseline of 1.20 Dash per hash and $100/Dash. This lends a price
per hash of $120.

* For a normal non-rotated quorum, the attacker will find $hashPower$ valid hashes. Each of those
  valid hashes will cost them, on average, $hashCost$. Thus the cost of the hashing is:

$$Total\ hashing\ cost = hashPower * hashCost$$

For example, at the baseline price of <span>$</span>120/hash, to get a target hash power of 10 $hashPower$ would require <span>$</span>1200.

* For a rotation quorum, there are 3 cycles to complete. On average, the attacker will find
  $hashPower$ valid hashes each cycle, and those hashes will cost them $hashCost$. Thus the cost of
  the attack is:

$$Total\ hashing\ cost=3 * hashPower * hashCost$$

The hash cost here is 3 times higher than for a usual quorum, but the attack is more efficient since
much lower hash power is required.

# Conclusion

Before the changes introduced in [DIP-24](../dip-0024.md), an attacker could make an InstantSend
quorum sign contradictory locks with a well-timed attack.

Now the attacker must also own, on average, 25% of all the masternodes in the system to be
successful. As we have seen, an adversary with high hash power could also try to bias the selection
of nodes, but the new parameters make this bias insignificant. Complete elimination of this bias is
possible and will be done when the resources to do so become available. Then the mining attacks
presented in this document will be entirely nullified, and the total number of byzantine nodes in
the system will be the sole parameter the attacker can manipulate.

We also increased the size of InstantSend quorums, making deviation from expected cases harder.

As a final summary, the protection levels are as of now:

| | Double Sign Threshold | Threshold |
| - | - | - |
| InstantSend quorums | 25%* | 75% |
| ChainLock quorums | 20%** | 60% |

\* Updates should increase this value significantly in the near future

\** But pointless, as stated in [DIP-24](../dip-0024.md). It would only create concurrency between
ChainLocks. Moreover, there is a low incentive as consecutive inconsistent ChainLocks would probably
devalue the DASH collaterals too much to render a few double-spend transactions worthwhile.

# Copyright

Copyright (c) 2022 Dash Core Group, Inc. [Licensed under the MIT
License](https://opensource.org/licenses/MIT)
