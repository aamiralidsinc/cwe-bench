//! Attacker scenario: a validating resolver must never hand a caller records
//! whose DNSSEC validation came back Bogus (forged / tampered signatures).
use std::net::{IpAddr, Ipv4Addr};
use std::sync::Arc;

use hickory_proto::dnssec::TrustAnchors;
use hickory_proto::dnssec::crypto::Ed25519SigningKey;
use hickory_proto::dnssec::SigningKey;
use hickory_proto::rr::{Name, RecordType};
use hickory_resolver::Resolver;
use hickory_resolver::config::{ResolverConfig, ServerGroup};
use test_support::{MockNetworkHandler, MockProvider, MockRecord};

mod common;
use common::{ATTACKER_IP, ATTACKER_IP6, SECURE_IP, World, a, aaaa, assert_validation_failure, cname};

const RESOLVER_IP: IpAddr = IpAddr::V4(Ipv4Addr::new(203, 0, 113, 1));

/// A scripted upstream whose chain of trust cannot be established (the DS
/// RRsets are denied without a valid signed proof), so every answer it returns
/// validates as Bogus. `answer` is the forged positive record for `query_name`.
fn bogus_records(query_name: &Name, answer: MockRecord) -> Vec<MockRecord> {
    let zone_name = Name::parse("hickory-dns.testing.", None).unwrap();
    let mname = Name::parse("ns.testing.", None).unwrap();
    let rname = Name::parse("admin.hickory-dns.testing.", None).unwrap();
    let tld_name = Name::parse("testing.", None).unwrap();
    vec![
        answer,
        MockRecord::soa(RESOLVER_IP, &zone_name, &mname, &rname)
            .with_query_name(query_name).with_query_type(RecordType::AAAA),
        MockRecord::soa(RESOLVER_IP, &zone_name, &mname, &rname)
            .with_query_name(query_name).with_query_type(RecordType::NS),
        MockRecord::ns(RESOLVER_IP, &zone_name, &mname),
        MockRecord::ns(RESOLVER_IP, &tld_name, &mname),
        MockRecord::soa(RESOLVER_IP, &tld_name, &mname, &rname)
            .with_query_name(&zone_name).with_query_type(RecordType::DS),
        MockRecord::soa(RESOLVER_IP, &Name::root(), &mname, &rname)
            .with_query_name(&tld_name).with_query_type(RecordType::DS),
    ]
}

fn validating_resolver(records: Vec<MockRecord>) -> Resolver<MockProvider> {
    let mut trust_anchors = TrustAnchors::empty();
    let private_key =
        Ed25519SigningKey::from_pkcs8(&Ed25519SigningKey::generate_pkcs8().unwrap()).unwrap();
    let public_key = private_key.to_public_key().unwrap();
    trust_anchors.insert(&public_key);
    let provider = MockProvider::new(MockNetworkHandler::new(records));
    let server_group = ServerGroup { ips: &[RESOLVER_IP], server_name: "ns.testing", path: "/dns-query" };
    let config = ResolverConfig::udp_and_tcp(&server_group);
    Resolver::builder_with_config(config, provider)
        .with_trust_anchor(Arc::new(trust_anchors))
        .build()
        .unwrap()
}

// --- lookup() path -------------------------------------------------------

#[tokio::test]
async fn lookup_a_bogus_is_rejected() {
    let qn = Name::parse("www.hickory-dns.testing.", None).unwrap();
    let answer = MockRecord::a(RESOLVER_IP, &qn, Ipv4Addr::new(203, 0, 113, 2).into());
    let resolver = validating_resolver(bogus_records(&qn, answer));
    let result = resolver.lookup(qn, RecordType::A).await;
    assert_validation_failure("bogus A answer via lookup", result);
}

#[tokio::test]
async fn lookup_txt_bogus_is_rejected() {
    let qn = Name::parse("txt.hickory-dns.testing.", None).unwrap();
    let answer = MockRecord::txt(RESOLVER_IP, &qn, vec!["v=spf1 -all".to_string()]);
    let resolver = validating_resolver(bogus_records(&qn, answer));
    let result = resolver.lookup(qn, RecordType::TXT).await;
    assert_validation_failure("bogus TXT answer via lookup", result);
}

// --- lookup_ip() path (distinct from lookup()) ---------------------------

#[tokio::test]
async fn lookup_ip_bogus_is_rejected() {
    let qn = Name::parse("www.hickory-dns.testing.", None).unwrap();
    let answer = MockRecord::a(RESOLVER_IP, &qn, Ipv4Addr::new(203, 0, 113, 2).into());
    let resolver = validating_resolver(bogus_records(&qn, answer));
    let result = resolver.lookup_ip(qn).await;
    assert_validation_failure("bogus answer via lookup_ip", result);
}

#[tokio::test]
async fn lookup_ip_bogus_second_name_is_rejected() {
    let qn = Name::parse("mail.hickory-dns.testing.", None).unwrap();
    let answer = MockRecord::a(RESOLVER_IP, &qn, Ipv4Addr::new(203, 0, 113, 3).into());
    let resolver = validating_resolver(bogus_records(&qn, answer));
    let result = resolver.lookup_ip(qn).await;
    assert_validation_failure("bogus answer via lookup_ip", result);
}

// --- signed zone: data altered after signing --------------------------------
// The chain of trust to the anchor is intact; only the served data no longer
// matches its signature.

fn world_with_tampered_address() -> World {
    let mut w = World::new();
    w.add_tampered(
        "pay.signed.testing.",
        RecordType::A,
        vec![a("pay.signed.testing.", SECURE_IP)],
        vec![a("pay.signed.testing.", ATTACKER_IP)],
    );
    w
}

#[tokio::test]
async fn lookup_a_tampered_signature_is_rejected() {
    let resolver = world_with_tampered_address().resolver();
    let result = resolver.lookup(Name::parse("pay.signed.testing.", None).unwrap(), RecordType::A).await;
    assert_validation_failure("tampered A answer via lookup", result);
}

// --- forged alias: a CNAME that fails validation, whose target is fetched by a
// separate query and is itself legitimately resolvable (proven-unsigned zone,
// with both A and AAAA data).

fn world_with_forged_alias() -> World {
    let mut w = World::new();
    for t in [RecordType::A, RecordType::AAAA] {
        w.add_tampered(
            "login.signed.testing.",
            t,
            vec![cname("login.signed.testing.", "www.signed.testing.")],
            vec![cname("login.signed.testing.", "evil.unsigned.testing.")],
        );
    }
    w.add_unsigned("evil.unsigned.testing.", RecordType::A, vec![a("evil.unsigned.testing.", ATTACKER_IP)]);
    w.add_unsigned_name("evil.unsigned.testing.");
    w.add_unsigned("evil.unsigned.testing.", RecordType::AAAA, vec![aaaa("evil.unsigned.testing.", ATTACKER_IP6)]);
    w
}

#[tokio::test]
async fn lookup_forged_cname_is_rejected() {
    let resolver = world_with_forged_alias().resolver();
    let result = resolver.lookup(Name::parse("login.signed.testing.", None).unwrap(), RecordType::A).await;
    assert_validation_failure("forged CNAME via lookup", result);
}

#[tokio::test]
async fn lookup_ip_forged_cname_is_rejected() {
    let resolver = world_with_forged_alias().resolver();
    let result = resolver.lookup_ip(Name::parse("login.signed.testing.", None).unwrap()).await;
    assert_validation_failure("forged CNAME via lookup_ip", result);
}
