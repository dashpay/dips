# DIP-0033 Test Vectors

These vectors cover the [identity shielded account](../dip-0033.md#identity-shielded-accounts), the [per-contact diversifier index](../dip-0033.md#per-contact-diversifier-index), the 64-byte encoding of [`encryptedShieldedAddress`](../dip-0033.md#per-contact-shielded-addresses), and the [`ContactTag`](../dip-0033.md#shielded-memo-kinds) memo. All byte strings are hexadecimal.

Inputs common to all vectors:

* Mnemonic `abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about`, empty passphrase.
* `ownerId` = 32 bytes of `0x11`; Bob's identity = 32 bytes of `0x22`; Carol's identity = 32 bytes of `0x33`.
* `accountReference` `0x01234567` for version 0 requests and `0x11234567` for the version 1 rotation (DIP-15 version in the top four bits).
* For the encryption and memo vectors: DIP-15 shared key `000102...1f` (bytes `0x00` to `0x1f`), IV `a0a1...af`, nonce `5051...5f`. Real implementations MUST draw the IV and nonce at random.

In each account block, `fvk` is the 96-byte raw full viewing key, `profile addr` is the address at diversifier index 0, and `K` is the contact index key. Per-contact vectors are given for mainnet, identity index 0.

## Output

```text
mnemonic            : abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about
seed                : 5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc19a5ac40b389cd370d086206dec8aa6c43daea6690f20ad3d8d48b2d2ce9e38e4

== mainnet (coin_type 5), identity_index 0, account 0x40000000
fvk                 : c0120eb660f8dd2f769e199bcc540476fec169b60f3e7508ffd42a21bd274337b2301310b489575eb68a8adacfed66b88fd07b961d1ca366c7e7e6e619b29a2bfce2cf9cb05a6439997f6f7ad4d9eb4b3d5a0672e571036cff9c8a600439063d
profile addr (j=0)  : e126993647eb0c9a4b476e2823380ead099e803ea52c980146e6fa42cfeb9d2ef8f7b1d6e764821d706397
K                   : 1c868b6adb3123f5ff837d236e5c645dd940f3e6f1f5469e960396c0ffc1e4aa
-- bob v0: ownerId 1111.. toUserId 2222.. accountReference 0x1234567
   t                : 8f83dcd11b2e71581e47543c7f9b3a603d665da783c7a9bf3b0024d528cb2482
   j (11 bytes LE)  : 8f83dcd11b2e71581e47d4
   j (integer)      : 0xd4471e58712e1bd1dc838f
   address (43 B)   : 89231e35d309bf8979a7662efc2723b796a5c2b97fabdb5901fe14c18b975190586d080d0b10231ec3bf1a
-- carol v0: ownerId 1111.. toUserId 3333.. accountReference 0x1234567
   t                : aade0fbb97fe88eccfa32b534c553513592b11d26f9b482cbb80e9425cf82df5
   j (11 bytes LE)  : aade0fbb97fe88eccfa3ab
   j (integer)      : 0xaba3cfec88fe97bb0fdeaa
   address (43 B)   : 67e737f5ca9a3ef4766915a4be09ff3d0933412984ea46a49e5cf88e4b15f3180a9dde78780e1cf4d44eb4
-- bob v1: ownerId 1111.. toUserId 2222.. accountReference 0x11234567
   t                : f8fbdcb909400ac429af1aab1215642dc89429b269fad9615bf49c81bcc1d960
   j (11 bytes LE)  : f8fbdcb909400ac429af9a
   j (integer)      : 0x9aaf29c40a4009b9dcfbf8
   address (43 B)   : adcc2868980cd98d1a813e9e0a4bbc1256ac91a35cd1348fb53cbb7eff7285b9606210225caa6f4c26ba31

== mainnet (coin_type 5), identity_index 1, account 0x40000001
fvk                 : 5317987e38a2dd272cebe41d317c33980e53d77c14ed166abc097aaaa1612837d315ce0f5dc87a85557ce30362cd330aaf0396b51c4970e2ddd7e7861dc069224581992d96f19f367bff3f7bbfee475fd5f61e8edccc550d98d9e2f98f7fdb0c
profile addr (j=0)  : 936389bea5f4472a82d8c933ce9763f88ce0d8955ebc61b0cbe42914350f1c9b38978c673e4a1247b890ba
K                   : 1a94e000a31d4b4cdd6a7f3389039d5110f31c5c0398944e4db623e3d790c5cd

== testnet (coin_type 1), identity_index 0, account 0x40000000
fvk                 : e82418aaf0c953565e04048cedfecb0fcd0bd1f9a5ab05be2d36a4fbcc5cd4046aecdbc3837ace5abf1b727bded47346872cdee34bdd36521ae81031fd92f00ecfd073865caa1e41baae4f378be748672b77c55e631f2ac2e7ccb2d205095c35
profile addr (j=0)  : 335feafaef3927edd1dffc09b7af7f2d14be582f5ba3a4501c691f044a4af5a881ddd3951496c6a877c32f
K                   : 2ea2b1ef93609c7f7c9b8faa6897f504da6bff3bf1755bb91b244668f6999ab0

== testnet (coin_type 1), identity_index 1, account 0x40000001
fvk                 : b5de92085e87846e0d1d28ddb4971451002b703298ef8d47162d4879ce79a206e4fa29154530eab7ce56526dc6dd93206603df9ea42d532b7ccacdf41920023f0083bff0b5af75f1fd9359e8cc20a73fc76f6c64f0411740b859d18f949efd28
profile addr (j=0)  : 8e039daad501d94c15ad9628ecfc1238d75054db98292b52b6307db9b0e707d88a0d8c7ad6fcfdc16ab895
K                   : 7fbe5fabd624237901a29c892fc7fc5c9e8ba0ae2e640702ee25e9c84505a044

== encryptedShieldedAddress v1
shared key          : 000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f
iv                  : a0a1a2a3a4a5a6a7a8a9aaabacadaeaf
plaintext (43 B)    : 89231e35d309bf8979a7662efc2723b796a5c2b97fabdb5901fe14c18b975190586d080d0b10231ec3bf1a
field (64 B)        : a0a1a2a3a4a5a6a7a8a9aaabacadaeaf3b53627ca8c440c7612ba9af8d7e95eaa5c080e0b8c5fa82100aeba7d41ada3b3fef6d06d30c6de649e6255282cd864d

== ContactTag memo (kind 4)
shared key          : 000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f
nonce               : 505152535455565758595a5b5c5d5e5f
payer identity      : 2222222222222222222222222222222222222222222222222222222222222222
memo (36 B)         : 04000000505152535455565758595a5b5c5d5e5fba18e0ee86eab80d47d70466850ecad8
```

## Generator

The vectors were produced by the program below, built against the Orchard implementation Dash Platform uses (`dashpay/orchard`, tag `dashified-0.14.1`), with `zip32 0.2`, `hmac 0.12`, `sha2 0.10`, `bip39 2.2`, `aes 0.8`, `cbc 0.1` (feature `alloc`), and `hex 0.4`. It asserts that every per-contact index lies in the per-contact range and that the index recovered from each address with the incoming viewing key equals the derived one.

```rust
//! DIP-33 amendment test vectors: identity shielded account, per-contact
//! diversifier index, encryptedShieldedAddress v1, ContactTag memo.
use aes::cipher::{block_padding::Pkcs7, BlockDecryptMut, BlockEncryptMut, KeyIvInit};
use hmac::{Hmac, Mac};
use orchard::keys::{DiversifierIndex, FullViewingKey, Scope, SpendingKey};
use orchard::Address;
use sha2::Sha256;

type Enc = cbc::Encryptor<aes::Aes256>;
type Dec = cbc::Decryptor<aes::Aes256>;

const KEY_LABEL: &[u8] = b"DashPay/DIP-0033/contact-index-key/v1";
const INDEX_LABEL: &[u8] = b"DashPay/DIP-0033/contact-index/v1";
const TAG_LABEL: &[u8] = b"DashPay/DIP-0033/contact-tag/v1";
const ACCOUNT_BASE: u32 = 0x4000_0000;

fn hmac(key: &[u8], msg: &[u8]) -> [u8; 32] {
    let mut m = Hmac::<Sha256>::new_from_slice(key).unwrap();
    m.update(msg);
    m.finalize().into_bytes().into()
}

fn contact_index(k: &[u8; 32], owner: &[u8; 32], to: &[u8; 32], account_ref: u64) -> ([u8; 32], [u8; 11]) {
    let mut msg = INDEX_LABEL.to_vec();
    msg.extend_from_slice(owner);
    msg.extend_from_slice(to);
    msg.extend_from_slice(&account_ref.to_le_bytes());
    let t = hmac(k, &msg);
    let mut j = [0u8; 11];
    j.copy_from_slice(&t[..11]);
    j[10] |= 0x80;
    (t, j)
}

fn main() {
    let phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
    let seed = bip39::Mnemonic::parse(phrase).unwrap().to_seed("");
    println!("mnemonic            : {phrase}");
    println!("seed                : {}", hex::encode(seed));

    let owner = [0x11u8; 32];
    let bob = [0x22u8; 32];
    let carol = [0x33u8; 32];
    // DIP-15 accountReference: version in the top 4 bits.
    let ref_v0: u64 = 0x0123_4567;
    let ref_v1: u64 = 0x1123_4567;

    for (net, coin) in [("mainnet", 5u32), ("testnet", 1u32)] {
        for identity_index in [0u32, 1u32] {
            let account = ACCOUNT_BASE + identity_index;
            let sk = SpendingKey::from_zip32_seed(&seed, coin, zip32::AccountId::try_from(account).unwrap()).unwrap();
            let fvk = FullViewingKey::from(&sk);
            let ivk = fvk.to_ivk(Scope::External);
            let fvk_bytes = fvk.to_bytes();
            let k = hmac(KEY_LABEL, &fvk_bytes);
            println!("\n== {net} (coin_type {coin}), identity_index {identity_index}, account {account:#x}");
            println!("fvk                 : {}", hex::encode(fvk_bytes));
            println!("profile addr (j=0)  : {}", hex::encode(fvk.address_at(0u32, Scope::External).to_raw_address_bytes()));
            println!("K                   : {}", hex::encode(k));
            if !(net == "mainnet" && identity_index == 0) { continue; }
            for (name, to, r) in [("bob v0", bob, ref_v0), ("carol v0", carol, ref_v0), ("bob v1", bob, ref_v1)] {
                let (t, j) = contact_index(&k, &owner, &to, r);
                let di = DiversifierIndex::from(j);
                let addr = fvk.address_at(di, Scope::External);
                let raw = addr.to_raw_address_bytes();
                let back = ivk.diversifier_index(&Address::from_raw_address_bytes(&raw).unwrap()).unwrap();
                assert_eq!(back, di);
                let ju = u128::from(di);
                assert!(ju >= 1u128 << 87 && ju < 1u128 << 88);
                println!("-- {name}: ownerId {}.. toUserId {}.. accountReference {r:#x}", hex::encode(&owner[..2]), hex::encode(&to[..2]));
                println!("   t                : {}", hex::encode(t));
                println!("   j (11 bytes LE)  : {}", hex::encode(j));
                println!("   j (integer)      : {ju:#x}");
                println!("   address (43 B)   : {}", hex::encode(raw));
            }
        }
    }

    // encryptedShieldedAddress v1 over the "bob v0" address.
    let sk = SpendingKey::from_zip32_seed(&seed, 5, zip32::AccountId::try_from(ACCOUNT_BASE).unwrap()).unwrap();
    let fvk = FullViewingKey::from(&sk);
    let k = hmac(KEY_LABEL, &fvk.to_bytes());
    let (_, j) = contact_index(&k, &owner, &bob, ref_v0);
    let addr = fvk.address_at(DiversifierIndex::from(j), Scope::External).to_raw_address_bytes();
    let shared_key: [u8; 32] = core::array::from_fn(|i| i as u8);
    let iv: [u8; 16] = core::array::from_fn(|i| 0xa0 + i as u8);
    let ct = Enc::new(&shared_key.into(), &iv.into()).encrypt_padded_vec_mut::<Pkcs7>(&addr);
    let mut field = iv.to_vec();
    field.extend_from_slice(&ct);
    assert_eq!(field.len(), 64);
    let pt = Dec::new(&shared_key.into(), &iv.into()).decrypt_padded_vec_mut::<Pkcs7>(&ct).unwrap();
    assert_eq!(pt, addr);
    println!("\n== encryptedShieldedAddress v1");
    println!("shared key          : {}", hex::encode(shared_key));
    println!("iv                  : {}", hex::encode(iv));
    println!("plaintext (43 B)    : {}", hex::encode(addr));
    println!("field (64 B)        : {}", hex::encode(&field));

    // ContactTag memo (kind 4).
    let nonce: [u8; 16] = core::array::from_fn(|i| 0x50 + i as u8);
    let payer = bob;
    let mut msg = TAG_LABEL.to_vec();
    msg.extend_from_slice(&nonce);
    msg.extend_from_slice(&payer);
    let mac = hmac(&shared_key, &msg);
    let mut memo = 4u32.to_le_bytes().to_vec();
    memo.extend_from_slice(&nonce);
    memo.extend_from_slice(&mac[..16]);
    assert_eq!(memo.len(), 36);
    println!("\n== ContactTag memo (kind 4)");
    println!("shared key          : {}", hex::encode(shared_key));
    println!("nonce               : {}", hex::encode(nonce));
    println!("payer identity      : {}", hex::encode(payer));
    println!("memo (36 B)         : {}", hex::encode(&memo));
}
```
