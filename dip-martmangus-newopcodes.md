<pre>
Title: Activating old and implementing new opcodes
Author: Mart Mangus
Comments: https://github.com/Dash-Dev-EE/DIP-draft/issues
Status: Draft
Layer: Consensus (hard fork)
Created: 2020-06-01
License: MIT License
</pre>

# Abstract
This DIP describes reactivation of a disabled opcodes (`OP_CAT`, `OP_AND`, `OP_OR`, `OP_XOR`, `OP_DIV`, `OP_MOD`) and activation of new opcodes (`OP_SPLIT`, `OP_BIN2NUM`, `OP_NUM2BIN`, `OP_CHECKDATASIG` and `OP_CHECKDATASIGVERIFY`) to expand the use of Dash scripting system.

# Motivation
Several opcodes were disabled in the Bitcoin scripting system due to discovery of series of bugs in early days of Bitcoin. The functionality of these opcodes has been re-examined by Bitcoin Cash developers few years ago. Many of the disabled opcodes have been enabled and few of them re-designed to replace the original ones. In addition, couple of new opcodes have been written and implemented to improve Bitcoin scripting system in Bitcoin Cash even further. Implementing these opcodes into Dash is necessary for broadening the functionality of the system and enabling developers to build new solutions, which in turn would expand the use of Dash.

# Specification
|Word                  |OpCode |Hex |Input |Output  | Description                                           |
|----------------------|-------|----|------|--------|-------------------------------------------------------|
|OP_CAT                |126    |0x7e|x1 x2 |out     |Concatenates two byte arrays                           |
|OP_SPLIT              |127    |0x7f|x n   |x1 x2   |Split byte array *x* at position *n*                   |
|OP_NUM2BIN            |128    |0x80|a b   |out     |Convert numeric *a* into byte array of length *b*      |
|OP_BIN2NUM            |129    |0x81|x     |out     |Convert byte array *x* into numeric                    |
|OP_AND                |132    |0x84|x1 x2 |out     |Boolean *AND* between each bit of the inputs           |
|OP_OR                 |133    |0x85|x1 x2 |out     |Boolean *OR* between each bit of the inputs            |
|OP_XOR                |134    |0x86|x1 x2 |out     |Boolean *EXCLUSIVE OR* between each bit of the inputs  |
|OP_DIV                |150    |0x96|a b   |out     |*a* is divided by *b*                                  |
|OP_MOD                |151    |0x97|a b   |out     |return the remainder after *a* is divided by *b*       |
|OP_CHECKDATASIG       |186    |0xba|sig&nbsp;msg&nbsp;pk|out     |If signature *sig* is valid, output to the stack|
|OP_CHECKDATASIGVERIFY |187    |0xbb|sig&nbsp;msg&nbsp;pk|-       |If signature *sig* is valid, false will cause the script to fail|

## OP_CAT

    Opcode (decimal): 126
    Opcode (hex): 0x7e

`OP_CAT` takes two byte arrays from the stack, concates and pushes the result back to the stack.

	x1 x2 OP_CAT → out

Example:
* `0x11 0x2233 OP_CAT → 0x112233`

References:
* [Detailed specification in Bitcoin Cash](https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/may-2018-reenabled-opcodes.md#op_cat)
* [Implementation in Bitcoin ABC](https://reviews.bitcoinabc.org/D1097)

## OP_SPLIT

    Opcode (decimal): 127
    Opcode (hex): 0x7f
    
`OP_SPLIT` is inverse of `OP_CAT` and a replacement operation for disabled opcodes `OP_SUBSTR`, `OP_LEFT` and `OP_RIGHT`.

`OP_SPLIT` takes a byte array, splits it at the position `n` (a number) and returns two byte arrays.

	x n OP_SPLIT → x1 x2


Examples:
* `0x001122 0 OP_SPLIT → OP_0 0x001122`
* `0x001122 1 OP_SPLIT → 0x00 0x1122`
* `0x001122 2 OP_SPLIT → 0x0011 0x22`
* `0x001122 3 OP_SPLIT → 0x001122 OP_0`

References:
* [Detailed specification in Bitcoin Cash](https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/may-2018-reenabled-opcodes.md#op_split)
* [Implementation in Bitcoin ABC](https://reviews.bitcoinabc.org/D1099)

## OP_NUM2BIN

    Opcode (decimal): 128
    Opcode (hex): 0x80

`OP_NUM2BIN` converts numeric value `n` to a byte array of length `m`.

	n m OP_NUM2BIN → x

Examples:
* `0x02 4 OP_NUM2BIN → 0x00000002`
* `0x85 4 OP_NUM2BIN → 0x80000005`

References:
* [Detailed specification in Bitcoin Cash](https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/may-2018-reenabled-opcodes.md#op_num2bin)
* [Implementation in Bitcoin ABC](https://reviews.bitcoinabc.org/D1222)

## OP_BIN2NUM

    Opcode (decimal): 129
    Opcode (hex): 0x81

`OP_BIN2NUM` converts byte array value `x` into a numeric value.

	x1 OP_BIN2NUM → n

if `x1` is any form of zero, including negative zero, then `OP_0` must be the result.

Examples:
* `0x0000000002 OP_BIN2NUM → 0x02`
* `0x800005 OP_BIN2NUM → 0x85`

References:
* [Detailed specification in Bitcoin Cash](https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/may-2018-reenabled-opcodes.md#op_bin2num)
* [Implementation in Bitcoin ABC](https://reviews.bitcoinabc.org/D1220)

## OP_AND

    Opcode (decimal): 132
    Opcode (hex): 0x84

Boolean *and* between each bit in the operands.

	x1 x2 OP_AND → out

References:
* [Detailed specification in Bitcoin Cash](https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/may-2018-reenabled-opcodes.md#op_and)
* [Implementation in Bitcoin ABC](https://reviews.bitcoinabc.org/D1211)

## OP_OR

    Opcode (decimal): 133
    Opcode (hex): 0x85

Boolean *or* between each bit in the operands.

	x1 x2 OP_OR → out
	
References:
* [Detailed specification in Bitcoin Cash](https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/may-2018-reenabled-opcodes.md#op_or)
* [Implementation in Bitcoin ABC](https://reviews.bitcoinabc.org/D1211)

## OP_XOR

    Opcode (decimal): 134
    Opcode (hex): 0x86

Boolean *xor* between each bit in the operands.

	x1 x2 OP_XOR → out

References:
* [Detailed specification in Bitcoin Cash](https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/may-2018-reenabled-opcodes.md#op_xor)
* [Implementation in Bitcoin ABC](https://reviews.bitcoinabc.org/D1211)

## OP_DIV

    Opcode (decimal): 150
    Opcode (hex): 0x96
    
Return the integer quotient of `a` and `b`. If the result would be a non-integer it is rounded *towards* zero. `a` and `b` are interpreted as numeric values.

    a b OP_DIV → out
    
References:
* [Detailed specification in Bitcoin Cash](https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/may-2018-reenabled-opcodes.md#op_div)
* [Implementation in Bitcoin ABC](https://reviews.bitcoinabc.org/D1212)

## OP_MOD

    Opcode (decimal): 151
    Opcode (hex): 0x97

Returns the remainder after dividing `a` by `b`. The output will be represented using the least number of bytes required. `a` and `b` are interpreted as numeric values.

	a b OP_MOD → out

References:
* [Detailed specification in Bitcoin Cash](https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/may-2018-reenabled-opcodes.md#op_mod)
* [Implementation in Bitcoin ABC](https://reviews.bitcoinabc.org/D1212)

## OP_CHECKDATASIG

    Opcode (decimal): 186
    Opcode (hex): 0xba
    
`OP_CHECKDATASIG` checks whether a signature is valid with respect to a message and a public key. It allows Script to validate arbitrary messages from outside the blockchain.

	sig msg pubKey OP_CHECKDATASIG → out

If the stack is well formed, then `OP_CHECKDATASIG` pops the top three elements [`sig`, `msg`, `pubKey`] from the stack and pushes true onto the stack if `sig` is valid with respect to the raw single-SHA256 hash of `msg` and `pubKey` using the secp256k1 elliptic curve. Otherwise, it pops three elements and pushes false onto the stack in the case that `sig` is the empty string and fails in all other cases.

References:
* [Detailed specification in Bitcoin Cash](https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/op_checkdatasig.md#op_checkdatasig-specification)
* [Implementation in Bitcoin ABC](https://reviews.bitcoinabc.org/D1621)
  * Implementation updates: [1](https://reviews.bitcoinabc.org/D1646), [2](https://reviews.bitcoinabc.org/D1653), [3](https://reviews.bitcoinabc.org/D1666)
  
## OP_CHECKDATASIGVERIFY

    Opcode (decimal): 187
    Opcode (hex): 0xbb

`OP_CHECKDATASIGVERIFY` is equivalent to `OP_CHECKDATASIG` followed by `OP_VERIFY`. It leaves nothing on the stack and will cause the script to fail immediately if the signature check does not pass.

	sig msg pubKey OP_CHECKDATASIG

References:
* [Detailed specification in Bitcoin Cash](https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/op_checkdatasig.md#op_checkdatasigverify-specification)
* [Implementation in Bitcoin ABC](https://reviews.bitcoinabc.org/D1621)
  * Implementation updates: [1](https://reviews.bitcoinabc.org/D1646), [2](https://reviews.bitcoinabc.org/D1653), [3](https://reviews.bitcoinabc.org/D1666)

# Compatibility
This change will be a hard-fork to the protocol and older software has to be updated to continue to operate. 

# References
* Bitcoin Cash specification of restored disabled opcodes: https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/may-2018-reenabled-opcodes.md
* Bitcoin Cash specification of OP_CHECKDATASIG and OP_CHECKDATASIGVERIFY: https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/op_checkdatasig.md
* Bitcoin Cash OP_CHECKDATASIG and OP_CHECKDATASIGVERIFY implementation:
  * https://reviews.bitcoinabc.org/D1621
  * https://reviews.bitcoinabc.org/D1646
  * https://reviews.bitcoinabc.org/D1653
  * https://reviews.bitcoinabc.org/D1666
* Bitcoin Cash OP_CAT implementation: https://reviews.bitcoinabc.org/D1097
* Bitcoin Cash OP_SPLIT implementation: https://reviews.bitcoinabc.org/D1099
* Bitcoin Cash OP_BIN2NUM implementation: https://reviews.bitcoinabc.org/D1101
* Bitcoin Cash OP_NUM2BIN implementation: https://reviews.bitcoinabc.org/D1103
* Bitcoin Cash OP_AND, OP_OR and OP_XOR implementation: https://reviews.bitcoinabc.org/D1211
* Bitcoin Cash OP_DIV and OP_MOD implementation: https://reviews.bitcoinabc.org/D1212

# Copyright
This document is licensed under the [MIT License](https://opensource.org/licenses/MIT).
