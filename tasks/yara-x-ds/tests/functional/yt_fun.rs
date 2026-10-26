//! Hidden functional tests for the compiled-rules restore path.
//!
//! Everything here is ordinary, legitimate use: compile, serialize, restore,
//! scan and read metadata.  A fix that refuses too much (or that changes what
//! a restored rule set does) must fail one of these.

use crate::{compile, MetaValue, Rules, Scanner};

const CORPUS: &str = r#"
    rule text_rule { strings: $a = "alpha" condition: $a }
    rule regexp_rule { strings: $a = /beta[0-9]+/ condition: $a }
    rule hex_rule { strings: $a = { 47 41 4d 4d 41 } condition: $a }
    rule combo_rule {
        strings: $a = "delta" $b = /omega/i
        condition: $a and $b
    }
"#;

const CORPUS_DATA: &[u8] = b"alpha beta42 GAMMA delta OMeGa";

fn restored(rules: &Rules) -> Rules {
    let bytes = rules.serialize().expect("a compiled rule set must serialize");
    Rules::deserialize(&bytes)
        .expect("a blob produced by the library must be accepted")
}

fn matching_identifiers(rules: &Rules, data: &[u8]) -> Vec<String> {
    let mut scanner = Scanner::new(rules);
    let mut identifiers: Vec<String> = scanner
        .scan(data)
        .expect("scanning must succeed")
        .matching_rules()
        .map(|rule| rule.identifier().to_string())
        .collect();
    identifiers.sort();
    identifiers
}

#[test]
fn round_trip_preserves_scan_results() {
    let rules = compile(CORPUS).expect("the corpus must compile");
    let before = matching_identifiers(&rules, CORPUS_DATA);
    assert_eq!(
        before,
        vec!["combo_rule", "hex_rule", "regexp_rule", "text_rule"],
        "the corpus must match on the pinned library"
    );

    let after = matching_identifiers(&restored(&rules), CORPUS_DATA);
    assert_eq!(before, after);
}

#[test]
fn rule_sets_without_patterns_round_trip() {
    let rules = compile(
        r#"
        rule always { condition: true }
        rule never { condition: false }
        "#,
    )
    .expect("pattern-free rules must compile");
    assert!(rules.iter().count() > 0);

    let after = restored(&rules);
    assert_eq!(matching_identifiers(&after, b""), vec!["always"]);
    assert_eq!(matching_identifiers(&after, b"anything"), vec!["always"]);
}

#[test]
fn anchored_patterns_round_trip() {
    let rules = compile(
        r#"
        rule anchored { strings: $a = "hello" condition: $a at 0 }
        rule ranged { strings: $b = "world" condition: $b in (0..8) }
        "#,
    )
    .expect("anchored rules must compile");

    let data = b"hello world";
    assert_eq!(
        matching_identifiers(&rules, data),
        vec!["anchored", "ranged"]
    );
    assert_eq!(
        matching_identifiers(&restored(&rules), data),
        vec!["anchored", "ranged"]
    );
}

#[test]
fn chained_patterns_round_trip() {
    let rules = compile(
        r#"rule chained { strings: $a = { 41 42 43 44 [0-1000] 45 46 47 48 } condition: $a }"#,
    )
    .expect("a chained pattern must compile");

    let mut data = b"ABCD".to_vec();
    data.extend(std::iter::repeat(b'.').take(500));
    data.extend_from_slice(b"EFGH");

    assert_eq!(matching_identifiers(&rules, &data), vec!["chained"]);
    assert_eq!(matching_identifiers(&restored(&rules), &data), vec!["chained"]);
}

#[test]
fn every_metadata_kind_round_trips() {
    let rules = compile(
        r#"
        rule meta_rule {
            meta:
                text = "café"
                raw = "\xff\xfe\x80"
                number = -7
                real = 1.5
                flag = true
            condition: true
        }
        "#,
    )
    .expect("metadata must compile");

    let after = restored(&rules);
    let rule = after.iter().next().expect("one rule");
    let mut text = None;
    let mut raw = None;
    let mut number = None;
    let mut real = None;
    let mut flag = None;
    for (name, value) in rule.metadata() {
        match (name, value) {
            ("text", MetaValue::String(s)) => text = Some(s.to_string()),
            ("raw", MetaValue::Bytes(b)) => raw = Some(b.to_vec()),
            ("number", MetaValue::Integer(i)) => number = Some(i),
            ("real", MetaValue::Float(f)) => real = Some(f),
            ("flag", MetaValue::Bool(b)) => flag = Some(b),
            _ => panic!("unexpected metadata kind for {name}"),
        }
    }
    assert_eq!(text.as_deref(), Some("café"));
    assert_eq!(raw.as_deref(), Some(&[0xff, 0xfe, 0x80][..]));
    assert_eq!(number, Some(-7));
    assert_eq!(real, Some(1.5));
    assert_eq!(flag, Some(true));
}

#[test]
fn fast_scan_mode_round_trips() {
    let rules = compile(
        r#"
        rule fast {
            strings: $a = "foo" $b = "bar"
            condition: $a and $b
        }
        "#,
    )
    .expect("the rule must compile");

    let mut scanner = Scanner::new(&rules);
    scanner.fast_scan(true);
    let before: Vec<String> = scanner
        .scan(b"foobar")
        .expect("scanning must succeed")
        .matching_rules()
        .map(|rule| rule.identifier().to_string())
        .collect();
    assert_eq!(before, vec!["fast"]);

    let after_rules = restored(&rules);
    let mut scanner = Scanner::new(&after_rules);
    scanner.fast_scan(true);
    let after: Vec<String> = scanner
        .scan(b"foobar")
        .expect("scanning must succeed")
        .matching_rules()
        .map(|rule| rule.identifier().to_string())
        .collect();
    assert_eq!(after, vec!["fast"]);
}

#[test]
fn file_size_bounds_round_trip() {
    let rules = compile(
        r#"rule small { strings: $a = "needle" condition: filesize < 10 and $a }"#,
    )
    .expect("the rule must compile");

    assert_eq!(matching_identifiers(&rules, b"needle"), vec!["small"]);

    let after = restored(&rules);
    assert_eq!(matching_identifiers(&after, b"needle"), vec!["small"]);
    assert!(
        matching_identifiers(&after, &[b'x'; 64]).is_empty(),
        "the restored rule must still honour its file size bound"
    );
}
