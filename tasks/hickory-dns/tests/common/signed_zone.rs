//! A small, correctly signed DNS tree served by an in-process scripted upstream.
//!
//! Chain of trust:  `.` (trust anchor key) --DS--> `testing.` (zone key)
//!
//! * `signed.testing.` names live inside the signed `testing.` zone, so their answers are
//!   validly signed and validate as Secure.
//! * `unsigned.testing.` is a delegation that the signed parent proves has no DS record (a
//!   signed NSEC at the cut), so answers from it are legitimately Insecure (proven unsigned).
//!
//! Every record and signature is produced here, in the test, from keys generated per run.
#![allow(dead_code)]

use std::collections::HashMap;
use std::net::{IpAddr, Ipv4Addr, Ipv6Addr};
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

use hickory_proto::dnssec::crypto::Ed25519SigningKey;
use hickory_proto::dnssec::rdata::{DNSKEY, DNSSECRData, DS, NSEC, RRSIG, SigInput};
use hickory_proto::dnssec::{Algorithm, DigestType, PublicKeyBuf, SigningKey, TBS, TrustAnchors};
use hickory_proto::op::{Message, OpCode, Query, ResponseCode};
use hickory_proto::rr::rdata::{A, AAAA, CNAME, NS, SOA, TXT};
use hickory_proto::rr::{DNSClass, Name, RData, Record, RecordType, SerialNumber};
use hickory_resolver::Resolver;
use hickory_resolver::config::{ResolverConfig, ServerGroup};
use hickory_resolver::net::NetError;
use hickory_resolver::net::xfer::Protocol;
use test_support::{MockHandler, MockProvider};

pub const UPSTREAM_IP: IpAddr = IpAddr::V4(Ipv4Addr::new(203, 0, 113, 53));

pub fn n(s: &str) -> Name {
    Name::parse(s, None).unwrap()
}

pub struct ZoneKey {
    pub zone: Name,
    key: Ed25519SigningKey,
    pub public: PublicKeyBuf,
    pub dnskey: DNSKEY,
}

impl ZoneKey {
    pub fn generate(zone: &str) -> Self {
        let key =
            Ed25519SigningKey::from_pkcs8(&Ed25519SigningKey::generate_pkcs8().unwrap()).unwrap();
        let public = key.to_public_key().unwrap();
        let dnskey = DNSKEY::from_key(&public);
        Self { zone: n(zone), key, public, dnskey }
    }

    /// RRSIG over `rrset` (all records share name, type and TTL).
    pub fn sign(&self, rrset: &[Record]) -> Record {
        let first = &rrset[0];
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as u32;
        let input = SigInput {
            type_covered: first.record_type(),
            algorithm: Algorithm::ED25519,
            num_labels: first.name.num_labels(),
            original_ttl: first.ttl,
            sig_expiration: SerialNumber::new(now + 30 * 24 * 3600),
            sig_inception: SerialNumber::new(now - 3600),
            key_tag: self.dnskey.calculate_key_tag().unwrap(),
            signer_name: self.zone.clone(),
        };
        let tbs = TBS::from_input(&first.name, DNSClass::IN, &input, rrset.iter()).unwrap();
        let sig = self.key.sign(&tbs).unwrap();
        Record::from_rdata(
            first.name.clone(),
            first.ttl,
            RData::DNSSEC(DNSSECRData::RRSIG(RRSIG::from_sig(input, sig))),
        )
    }

    pub fn dnskey_record(&self) -> Record {
        Record::from_rdata(self.zone.clone(), 3600, RData::DNSSEC(DNSSECRData::DNSKEY(self.dnskey.clone())))
    }

    pub fn ds_record(&self) -> Record {
        let ds = DS::from_key(&self.public, &self.zone, DigestType::SHA256).unwrap();
        Record::from_rdata(self.zone.clone(), 3600, RData::DNSSEC(DNSSECRData::DS(ds)))
    }
}

pub fn a(name: &str, ip: Ipv4Addr) -> Record {
    Record::from_rdata(n(name), 300, RData::A(A(ip)))
}

pub fn aaaa(name: &str, ip: Ipv6Addr) -> Record {
    Record::from_rdata(n(name), 300, RData::AAAA(AAAA(ip)))
}

pub fn cname(name: &str, target: &str) -> Record {
    Record::from_rdata(n(name), 300, RData::CNAME(CNAME(n(target))))
}

pub fn txt(name: &str, text: &str) -> Record {
    Record::from_rdata(n(name), 300, RData::TXT(TXT::new(vec![text.to_string()])))
}

pub fn soa(zone: &str) -> Record {
    Record::from_rdata(
        n(zone),
        300,
        RData::SOA(SOA::new(n("ns.testing."), n("admin.testing."), 1, 3600, 600, 86400, 300)),
    )
}

pub fn ns(zone: &str, host: &str) -> Record {
    Record::from_rdata(n(zone), 3600, RData::NS(NS(n(host))))
}

pub fn nsec(owner: &str, next: &str, types: &[RecordType]) -> Record {
    Record::from_rdata(
        n(owner),
        300,
        RData::DNSSEC(DNSSECRData::NSEC(NSEC::new(n(next), types.iter().copied()))),
    )
}

/// Scripted authoritative upstream: one canned response per (name, type).
#[derive(Default)]
pub struct Upstream {
    responses: HashMap<(Name, RecordType), Message>,
}

impl Upstream {
    pub fn answer(&mut self, name: &str, qtype: RecordType, answers: Vec<Record>) {
        self.put(name, qtype, ResponseCode::NoError, answers, vec![]);
    }

    pub fn nodata(&mut self, name: &str, qtype: RecordType, authorities: Vec<Record>) {
        self.put(name, qtype, ResponseCode::NoError, vec![], authorities);
    }

    fn put(&mut self, name: &str, qtype: RecordType, rcode: ResponseCode, answers: Vec<Record>, authorities: Vec<Record>) {
        let mut m = Message::response(0, OpCode::Query);
        m.add_query(Query::query(n(name), qtype));
        m.metadata.authoritative = true;
        m.metadata.response_code = rcode;
        for r in answers {
            m.add_answer(r);
        }
        for r in authorities {
            m.add_authority(r);
        }
        self.responses.insert((n(name), qtype), m);
    }
}

impl MockHandler for Upstream {
    fn handle(&self, _destination: IpAddr, _protocol: Protocol, request: Message) -> Message {
        let query = request.queries[0].clone();
        let Some(found) = self.responses.get(&(query.name().clone(), query.query_type())) else {
            eprintln!("scripted upstream: no response for {query}");
            let mut msg = request.into_response();
            msg.metadata.response_code = ResponseCode::ServFail;
            return msg;
        };
        let mut response = found.clone();
        response.metadata.id = request.metadata.id;
        response.queries.clear();
        response.add_query(query);
        response
    }
}

pub struct World {
    pub root: ZoneKey,
    pub testing: ZoneKey,
    pub upstream: Upstream,
}

pub const SECURE_IP: Ipv4Addr = Ipv4Addr::new(192, 0, 2, 10);
pub const INSECURE_IP: Ipv4Addr = Ipv4Addr::new(192, 0, 2, 20);
pub const ATTACKER_IP: Ipv4Addr = Ipv4Addr::new(198, 18, 0, 66);
pub const ATTACKER_IP6: Ipv6Addr = Ipv6Addr::new(0x2001, 0xdb8, 0, 0, 0, 0, 0, 0x66);

impl World {
    /// The signed tree with its legitimate content:
    /// * `www.signed.testing.` A SECURE_IP (signed), AAAA proven absent (signed NSEC)
    /// * `txt.signed.testing.` TXT (signed)
    /// * `alias.signed.testing.` CNAME `www.signed.testing.` (signed; target fetched separately)
    /// * `www.unsigned.testing.` A INSECURE_IP inside the proven-unsigned delegation
    pub fn new() -> Self {
        let root = ZoneKey::generate(".");
        let testing = ZoneKey::generate("testing.");
        let mut w = Self { root, testing, upstream: Upstream::default() };

        // Root zone: self-signed key, signed DS for testing.
        let dnskey = vec![w.root.dnskey_record()];
        let sig = w.root.sign(&dnskey);
        w.upstream.answer(".", RecordType::DNSKEY, vec![dnskey[0].clone(), sig]);
        let ds = vec![w.testing.ds_record()];
        let sig = w.root.sign(&ds);
        w.upstream.answer("testing.", RecordType::DS, vec![ds[0].clone(), sig]);
        w.upstream.answer("testing.", RecordType::NS, vec![ns("testing.", "ns.testing.")]);

        // testing. zone apex.
        let dnskey = vec![w.testing.dnskey_record()];
        let sig = w.testing.sign(&dnskey);
        w.upstream.answer("testing.", RecordType::DNSKEY, vec![dnskey[0].clone(), sig]);

        // Secure positive answers.
        w.add_signed("www.signed.testing.", RecordType::A, vec![a("www.signed.testing.", SECURE_IP)]);
        w.add_signed("txt.signed.testing.", RecordType::TXT, vec![txt("txt.signed.testing.", "v=legit")]);
        w.add_signed("alias.signed.testing.", RecordType::A, vec![cname("alias.signed.testing.", "www.signed.testing.")]);
        w.add_signed("alias.signed.testing.", RecordType::AAAA, vec![cname("alias.signed.testing.", "www.signed.testing.")]);
        w.add_signed_nodata("www.signed.testing.", RecordType::AAAA, "zzz.signed.testing.", &[RecordType::A]);

        // Insecure delegation unsigned.testing.: NS exists, signed NSEC proves there is no DS.
        w.upstream.answer("unsigned.testing.", RecordType::NS, vec![ns("unsigned.testing.", "ns.unsigned.testing.")]);
        w.add_signed_nodata("unsigned.testing.", RecordType::DS, "testing.", &[RecordType::NS]);
        w.add_unsigned("www.unsigned.testing.", RecordType::A, vec![a("www.unsigned.testing.", INSECURE_IP)]);
        w.add_unsigned_name("www.unsigned.testing.");
        w
    }

    /// Positive answer in the signed zone, signed by the zone key.
    pub fn add_signed(&mut self, name: &str, qtype: RecordType, rrset: Vec<Record>) {
        let sig = self.testing.sign(&rrset);
        let mut answers = rrset;
        answers.push(sig);
        self.upstream.answer(name, qtype, answers);
    }

    /// Positive answer whose signature does not match the data (the data was altered after
    /// signing): `signed_rrset` is what the zone signed, `served_rrset` is what is returned.
    pub fn add_tampered(&mut self, name: &str, qtype: RecordType, signed_rrset: Vec<Record>, served_rrset: Vec<Record>) {
        let sig = self.testing.sign(&signed_rrset);
        let mut answers = served_rrset;
        answers.push(sig);
        self.upstream.answer(name, qtype, answers);
    }

    /// Signed NODATA for (name, qtype): signed SOA plus a signed NSEC at `name`.
    pub fn add_signed_nodata(&mut self, name: &str, qtype: RecordType, next: &str, present: &[RecordType]) {
        let soa_rr = vec![soa("testing.")];
        let soa_sig = self.testing.sign(&soa_rr);
        let mut types = present.to_vec();
        types.extend([RecordType::RRSIG, RecordType::NSEC]);
        let nsec_rr = vec![nsec(name, next, &types)];
        let nsec_sig = self.testing.sign(&nsec_rr);
        self.upstream.nodata(name, qtype, vec![soa_rr[0].clone(), soa_sig, nsec_rr[0].clone(), nsec_sig]);
    }

    /// Answer from inside the unsigned delegation (no signatures at all).
    pub fn add_unsigned(&mut self, name: &str, qtype: RecordType, rrset: Vec<Record>) {
        self.upstream.answer(name, qtype, rrset);
    }

    /// Unsigned NODATA for the NS / AAAA queries a resolver makes for a name in unsigned.testing.
    pub fn add_unsigned_name(&mut self, name: &str) {
        for t in [RecordType::NS, RecordType::AAAA] {
            self.upstream.nodata(name, t, vec![soa("unsigned.testing.")]);
        }
    }

    /// A validating resolver (root trust anchor = this world's root key) over the scripted upstream.
    pub fn resolver(self) -> Resolver<MockProvider> {
        let mut anchors = TrustAnchors::empty();
        anchors.insert(&self.root.public);
        let provider = MockProvider::new(self.upstream);
        let group = ServerGroup { ips: &[UPSTREAM_IP], server_name: "ns.testing", path: "/dns-query" };
        let config = ResolverConfig::udp_and_tcp(&group);
        Resolver::builder_with_config(config, provider)
            .with_trust_anchor(Arc::new(anchors))
            .build()
            .unwrap()
    }
}

/// The lookup must fail, and fail as a validation failure: not as an ordinary negative answer
/// ("no such name / no such record") and not as a transport failure.
pub fn assert_validation_failure<T: std::fmt::Debug>(what: &str, result: Result<T, NetError>) {
    let err = match result {
        Ok(v) => panic!("{what}: untrustworthy answer was returned as a success: {v:?}"),
        Err(e) => e,
    };
    assert!(
        !err.is_no_records_found() && !err.is_nx_domain(),
        "{what}: failure was reported as an ordinary negative answer (name/record does not exist), \
         not as a validation failure: {err:?}"
    );
    assert!(
        !matches!(err, NetError::Timeout | NetError::NoConnections | NetError::Busy | NetError::Io(_)),
        "{what}: failure was reported as a transport failure, not as a validation failure: {err:?}"
    );
}
