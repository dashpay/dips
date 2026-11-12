# Private Document Envelope: Test Vector

One entry of the DashPay `privateContactRequest` type, built as [Standard Envelope](../dip-quantumexplorer-anonymous-contact-requests.md#standard-envelope) and [DashPay Private Contact Requests](../dip-quantumexplorer-anonymous-contact-requests.md#dashpay-private-contact-requests) specify, in signature mode. All byte strings are hexadecimal.

Inputs:

* The contract id is the DashPay contract's, and `entrySize` is 589.
* The sender identity is 32 bytes of `0xa1`. Its encryption key has id 2 and secret key 32 bytes of `0x11`, from which the outgoing viewing key is derived. Its signing key has secret key 32 bytes of `0x33`.
* The recipient identity is 32 bytes of `0xb2`, and the recipient key's secret key is 32 bytes of `0x22`.
* `eskSeed` is 32 bytes of `0x55`. Real implementations MUST draw it at random for every entry.
* The payload is `accountReference` `0x01234567`, an `extendedPublicKey` of bytes `0x01` to `0x45`, no `accountLabel`, no `autoAcceptProof`, and a `shieldedAddress`: 8 + 69 + 1 + 1 + 44 = 123 bytes.

The entry is `cm || epk || body_ct || out_ct`, 32 + 33 + 443 + 81 = 589 bytes.

## Output

```text
contract id                : a2a1b4ac6fef22ea2a1a68e8123644b357875f6b412c18109281c146e7b271bc
document type              : privateContactRequest
entry size                 : 589
sender identity id         : a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1
sender encryption key id   : 2
sender encryption secret   : 1111111111111111111111111111111111111111111111111111111111111111
sender signing secret      : 3333333333333333333333333333333333333333333333333333333333333333
sender signing public key  : 023c72addb4fdf09af94f0c94d7fe92a386a7e70cf8a1d85916386bb2535c7b1b1
recipient identity id      : b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2
recipient secret key       : 2222222222222222222222222222222222222222222222222222222222222222
recipient public key R     : 02466d7fcae563e5cb09a0d1870bb580344804617879a14949cf22285f1bae3f27
esk_seed                   : 5555555555555555555555555555555555555555555555555555555555555555
payload (123 B)            : 00000000012345670102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f40414243444500000125611685f1aa7c3b7a2f7a758ea2f98ca16e32e20e0d3b403a1d81421f1185d67f47054ae98e55e05e839c
signing data m             : 4ae9182d57eb14a5dfdbfb21bb2100a0cb6b2597fa3dc5b5312fe4b6fad08650
signature (65 B)           : 208db7638094e0972e1a33e6bc2b73587bdcd17aa91c241e02bff50b9c5ac4cb7753e976ba868d568d1cab5f9a66b9abb9c02ab2537a39300f497c57741e55c647
ovk                        : e9ad1442172a2a0fa464334a245814fdba0fd83b09468190e576e174a2a3d30a
cm                         : 44e17df1a8f4244d0f6e34061cf3df8637c8a036adfaa455204b834640f91de7
epk                        : 031ab0e922099ceeeafcf1d408f5ed8f626b130cd8c1f8f73a21618180ee5c07ac
body_ct (443 B)            : 5b9fd1ceca8dcc780d161cfc2d9ae27b77a707cbcd46774820655ee9eccc0ce49e01906eaadac9bf922333424db28deb5622e4ce0ccbe44cca2b8638c27173534107876c235ee118a08ae3857e2cc7c580c33de0ac36e68912396d8bdf0d3521688dd89249b8fa39b297c6ce1c567ae0112ed1ec9921f3afbd60ce0b6b72952a09582d4a1b75f2719b312af3656efa7f0c66cacfa6d31f7becabba73816dc900e6d17d51da5c7e851a1f85205d9039491abad3863cc4f45c4bed8f2200d22b1b7aa94f3ec5e146c593fca6d85ba62a3bd875111af21e7f990030d80f280d0e1923f03e778a2cb14da7a490510ea2f4298cd1871f5a07a707df14b0df7645924c307739a72601894cb4a6e7aa90a3c48e923950b51ad54f0858734b793a0a29689a1187212e977fa933228dc33db833a6e0736420d1ac5c24511068ba7fa390d79991ef706629ca6e82fd2040f1717824ba4d8e8d6ca608015d2bc7642b00b31f09f12f60ee5553c120a67b34209805c25925245f8de0ab4828e6c70f0eca40f5acec0ec2d2146604b6f22addbbfb9d7d15231ef0be0bf28e3047869e469115e1b9a9f30824b89e5f87fc45bf874a1a8b626f2087413129c1ea7724
out_ct (81 B)              : d43e633f98500c96cc84ebec7ec18ac8910f99dafc1ff09f314393655c3af504e6519b2dc147e10b7650c65e6bcb9162aa80b56a290e7ec22a90fe525294544f3e3c51e575d7147943080c011b839e58cb
```

## Generator

The vector was produced by the program below, built against the `platform-encryption` crate of Dash Platform (`packages/rs-platform-encryption`, branch `v5.1-dev`), with `secp256k1 0.33` (feature `recovery`) and `hex 0.4`. It asserts that the entry opens for the recipient key, that the signature recovers the sender's signing key, and that the sender recovers the entry with its outgoing viewing key.

```rust
//! Private document envelope test vector: one DashPay privateContactRequest entry in
//! signature mode, opened by its recipient and recovered by its sender.
use platform_encryption::{
    open_private_document_entry, private_document_outgoing_viewing_key,
    private_document_signing_data, recover_sent_private_document_entry,
    seal_private_document_entry, sign_private_document_signing_data, PrivateDocumentRecipient,
    PrivateDocumentSender, PrivateDocumentTarget,
};
use secp256k1::{PublicKey, SecretKey};

fn main() {
    // The DashPay contract id.
    let contract_id: [u8; 32] = [
        162, 161, 180, 172, 111, 239, 34, 234, 42, 26, 104, 232, 18, 54, 68, 179, 87, 135, 95,
        107, 65, 44, 24, 16, 146, 129, 193, 70, 231, 178, 113, 188,
    ];
    let target = PrivateDocumentTarget {
        contract_id,
        document_type_name: "privateContactRequest",
    };
    let entry_size = 589;

    let sender_identity_id = [0xa1u8; 32];
    let sender_encryption_key_id = 2u32;
    let sender_encryption_secret = SecretKey::from_secret_bytes([0x11; 32]).unwrap();
    let sender_signing_secret = SecretKey::from_secret_bytes([0x33; 32]).unwrap();
    let recipient_identity_id = [0xb2u8; 32];
    let recipient_secret = SecretKey::from_secret_bytes([0x22; 32]).unwrap();
    let recipient_public = PublicKey::from_secret_key(&recipient_secret);
    let recipient = PrivateDocumentRecipient {
        identity_id: recipient_identity_id,
        public_key: &recipient_public,
    };
    let esk_seed = [0x55u8; 32];

    // Payload: accountReference 0x01234567 (i64, big-endian), extendedPublicKey bytes
    // 0x01..=0x45, no accountLabel, no autoAcceptProof, a shieldedAddress.
    let mut payload = Vec::new();
    payload.extend_from_slice(&0x0123_4567i64.to_be_bytes());
    payload.extend((1u8..=69).collect::<Vec<u8>>());
    payload.push(0);
    payload.push(0);
    payload.push(1);
    payload.extend_from_slice(
        &hex::decode("25611685f1aa7c3b7a2f7a758ea2f98ca16e32e20e0d3b403a1d81421f1185d67f47054ae98e55e05e839c")
            .unwrap(),
    );
    assert_eq!(payload.len(), 123);

    let signing_data = private_document_signing_data(
        &target,
        &sender_identity_id,
        sender_encryption_key_id,
        &recipient,
        &payload,
    );
    let signature = sign_private_document_signing_data(&signing_data, &sender_signing_secret);
    let ovk = private_document_outgoing_viewing_key(&sender_encryption_secret.secret_bytes());
    let entry = seal_private_document_entry(
        &target,
        entry_size,
        &recipient,
        &PrivateDocumentSender::Signature {
            identity_id: sender_identity_id,
            key_id: sender_encryption_key_id,
            signature: &signature,
        },
        &payload,
        &ovk,
        &esk_seed,
    )
    .unwrap();
    assert_eq!(entry.len(), entry_size);

    let opened = open_private_document_entry(&entry, &target, &recipient_identity_id, &[recipient_secret])
        .unwrap()
        .expect("opens for the recipient");
    assert_eq!(opened.payload(), payload.as_slice());
    assert_eq!(
        opened.recover_signer().unwrap(),
        PublicKey::from_secret_key(&sender_signing_secret)
    );
    let recovered = recover_sent_private_document_entry(&entry, &target, &ovk)
        .unwrap()
        .expect("recovers for the sender");
    assert_eq!(recovered.payload(), payload.as_slice());

    let h = |b: &[u8]| hex::encode(b);
    println!("contract id                : {}", h(&contract_id));
    println!("document type              : privateContactRequest");
    println!("entry size                 : {entry_size}");
    println!("sender identity id         : {}", h(&sender_identity_id));
    println!("sender encryption key id   : {sender_encryption_key_id}");
    println!("sender encryption secret   : {}", h(&sender_encryption_secret.secret_bytes()));
    println!("sender signing secret      : {}", h(&sender_signing_secret.secret_bytes()));
    println!("sender signing public key  : {}", h(&PublicKey::from_secret_key(&sender_signing_secret).serialize()));
    println!("recipient identity id      : {}", h(&recipient_identity_id));
    println!("recipient secret key       : {}", h(&recipient_secret.secret_bytes()));
    println!("recipient public key R     : {}", h(&recipient_public.serialize()));
    println!("esk_seed                   : {}", h(&esk_seed));
    println!("payload (123 B)            : {}", h(&payload));
    println!("signing data m             : {}", h(&signing_data));
    println!("signature (65 B)           : {}", h(&signature));
    println!("ovk                        : {}", h(&ovk));
    println!("cm                         : {}", h(&entry[..32]));
    println!("epk                        : {}", h(&entry[32..65]));
    println!("body_ct (443 B)            : {}", h(&entry[65..508]));
    println!("out_ct (81 B)              : {}", h(&entry[508..]));
}
```
