use std::net::Ipv4Addr;

use hickory_proto::rr::{Name, RecordType};
use hickory_resolver::Resolver;
use hickory_resolver::config::{ResolverConfig, ServerGroup};
use test_support::{MockNetworkHandler, MockProvider, MockRecord};

fn plain_resolver(records: Vec<MockRecord>, resolver_ip: std::net::IpAddr) -> Resolver<MockProvider> {
    let provider = MockProvider::new(MockNetworkHandler::new(records));
    let server_group = ServerGroup { ips: &[resolver_ip], server_name: "ns.testing", path: "/dns-query" };
    let config = ResolverConfig::udp_and_tcp(&server_group);
    Resolver::builder_with_config(config, provider).build().unwrap()
}

#[tokio::test]
async fn unsigned_lookup_a_succeeds() {
    let ip = Ipv4Addr::new(203, 0, 113, 1).into();
    let qn = Name::parse("www.example.testing.", None).unwrap();
    let recs = vec![MockRecord::a(ip, &qn, Ipv4Addr::new(198, 51, 100, 7).into())];
    let r = plain_resolver(recs, ip);
    let lk = r.lookup(qn, RecordType::A).await.expect("plain A lookup must work");
    assert!(!lk.answers().is_empty(), "expected at least one record");
}

#[tokio::test]
async fn unsigned_lookup_ip_succeeds() {
    let ip = Ipv4Addr::new(203, 0, 113, 1).into();
    let qn = Name::parse("host.example.testing.", None).unwrap();
    let addr = Ipv4Addr::new(198, 51, 100, 9);
    let zone = Name::parse("example.testing.", None).unwrap();
    let mname = Name::parse("ns.testing.", None).unwrap();
    let rname = Name::parse("admin.example.testing.", None).unwrap();
    let recs = vec![
        MockRecord::a(ip, &qn, addr.into()),
        MockRecord::soa(ip, &zone, &mname, &rname).with_query_name(&qn).with_query_type(RecordType::AAAA),
    ];
    let r = plain_resolver(recs, ip);
    let lk = r.lookup_ip(qn).await.expect("plain lookup_ip must work");
    assert!(lk.iter().any(|a| a == std::net::IpAddr::V4(addr)), "expected {addr}");
}

#[tokio::test]
async fn unsigned_lookup_txt_succeeds() {
    let ip = Ipv4Addr::new(203, 0, 113, 1).into();
    let qn = Name::parse("txt.example.testing.", None).unwrap();
    let recs = vec![MockRecord::txt(ip, &qn, vec!["hello".to_string()])];
    let r = plain_resolver(recs, ip);
    let lk = r.lookup(qn, RecordType::TXT).await.expect("plain TXT lookup must work");
    assert!(!lk.answers().is_empty());
}

#[tokio::test]
async fn unsigned_lookup_second_name_succeeds() {
    let ip = Ipv4Addr::new(203, 0, 113, 1).into();
    let qn = Name::parse("other.example.testing.", None).unwrap();
    let recs = vec![MockRecord::a(ip, &qn, Ipv4Addr::new(198, 51, 100, 23).into())];
    let r = plain_resolver(recs, ip);
    let lk = r.lookup(qn, RecordType::A).await.expect("plain A lookup must work");
    assert!(!lk.answers().is_empty());
}

#[tokio::test]
async fn unsigned_nodata_is_negative() {
    let ip = Ipv4Addr::new(203, 0, 113, 1).into();
    let qn = Name::parse("empty.example.testing.", None).unwrap();
    let zone = Name::parse("example.testing.", None).unwrap();
    let mname = Name::parse("ns.testing.", None).unwrap();
    let rname = Name::parse("admin.example.testing.", None).unwrap();
    let recs = vec![
        MockRecord::soa(ip, &zone, &mname, &rname).with_query_name(&qn).with_query_type(RecordType::A),
    ];
    let r = plain_resolver(recs, ip);
    let result = r.lookup(qn, RecordType::A).await;
    assert!(result.is_err(), "nodata must be a negative answer, got {result:?}");
}
