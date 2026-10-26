//! Hidden security tests for the compiled-rules restore path.
//!
//! Each test builds a rule set with the real compiler, changes one piece of
//! the compiled structure so that it is no longer something the compiler can
//! produce, serializes it, and requires the restore operation to refuse the
//! resulting bytes with an error.  The tests never run the damaged rules, so a
//! memory-safety failure cannot abort the test process; the refusal is the
//! observable.

use crate::compiler::rules::SubPatternAtom;
use crate::compiler::{Atom, MetaValue, SubPattern, SubPatternId};
use crate::re::{BckCodeLoc, FwdCodeLoc, RegexpAtom};
use crate::Rules;

fn yt_compiled(source: &str) -> Rules {
    crate::compile(source).expect("the test fixture must compile")
}

fn yt_blob(rules: &Rules) -> Vec<u8> {
    rules.serialize().expect("the test fixture must serialize")
}

fn yt_accepts(rules: &Rules) -> bool {
    Rules::deserialize(yt_blob(rules)).is_ok()
}

fn yt_refuses(rules: &Rules) -> bool {
    Rules::deserialize(yt_blob(rules)).is_err()
}

#[test]
fn atom_sub_pattern_id_equal_to_count_is_refused() {
    let mut rules = yt_compiled(r#"rule t { strings: $a = "foobar" condition: $a }"#);
    assert!(yt_accepts(&rules), "the unmodified fixture must be accepted");

    // The largest valid id is count - 1; `count` itself is already outside
    // the array.
    let count = rules.sub_patterns.len() as u32;
    rules.atoms[0] = SubPatternAtom::from_atom(
        SubPatternId(count),
        Atom::from(&b"foobar"[..]),
    );

    assert!(
        yt_refuses(&rules),
        "an atom whose sub-pattern id equals the sub-pattern count must be refused"
    );
}

#[test]
fn atom_sub_pattern_id_beyond_count_is_refused() {
    let mut rules = yt_compiled(r#"rule t { strings: $a = "foobar" condition: $a }"#);
    assert!(yt_accepts(&rules), "the unmodified fixture must be accepted");

    let count = rules.sub_patterns.len() as u32;
    rules.atoms[0] = SubPatternAtom::from_atom(
        SubPatternId(count + 100),
        Atom::from(&b"foobar"[..]),
    );

    assert!(
        yt_refuses(&rules),
        "an atom whose sub-pattern id is outside the sub-pattern array must be refused"
    );
}

#[test]
fn anchored_sub_pattern_id_outside_array_is_refused() {
    let mut rules = yt_compiled(
        r#"rule t { strings: $a = "foobar" condition: $a at 0 }"#,
    );
    assert!(yt_accepts(&rules), "the unmodified fixture must be accepted");
    assert!(
        !rules.anchored_sub_patterns.is_empty(),
        "the fixture must have an anchored sub-pattern"
    );

    let count = rules.sub_patterns.len() as u32;
    rules.anchored_sub_patterns[0] = SubPatternId(count + 3);

    assert!(
        yt_refuses(&rules),
        "an anchored sub-pattern id outside the sub-pattern array must be refused"
    );
}

#[test]
fn chain_tail_chained_to_outside_array_is_refused() {
    let mut rules = yt_compiled(
        r#"rule t { strings: $a = { 41 42 43 44 [0-1000] 45 46 47 48 } condition: $a }"#,
    );
    assert!(yt_accepts(&rules), "the unmodified fixture must be accepted");

    let count = rules.sub_patterns.len() as u32;
    let mut changed = 0;
    for (_, sub_pattern) in rules.sub_patterns.iter_mut() {
        match sub_pattern {
            SubPattern::LiteralChainTail { chained_to, .. }
            | SubPattern::RegexpChainTail { chained_to, .. } => {
                *chained_to = SubPatternId(count + 5);
                changed += 1;
            }
            _ => {}
        }
    }
    assert!(changed > 0, "the fixture must have a chained sub-pattern");

    assert!(
        yt_refuses(&rules),
        "a chain id outside the sub-pattern array must be refused"
    );
}

#[test]
fn string_metadata_that_is_not_utf8_is_refused() {
    let mut rules = yt_compiled(
        r#"rule t { meta: s = "hello" condition: true }"#,
    );
    assert!(yt_accepts(&rules), "the unmodified fixture must be accepted");

    let not_text = rules.lit_pool.get_or_intern(&[0x80u8, 0x81][..]);
    let mut changed = 0;
    for (_, value) in rules.rules[0].metadata.iter_mut() {
        if matches!(value, MetaValue::String(_)) {
            *value = MetaValue::String(not_text);
            changed += 1;
        }
    }
    assert!(changed > 0, "the fixture must have a text metadata value");

    assert!(
        yt_refuses(&rules),
        "text metadata backed by bytes that are not UTF-8 must be refused"
    );
}

#[test]
fn regex_forward_code_outside_the_code_is_refused() {
    let mut rules = yt_compiled(
        r#"rule t { strings: $a = /ab+c/ condition: $a }"#,
    );
    assert!(yt_accepts(&rules), "the unmodified fixture must be accepted");

    let far = rules.re_code.len() + 512;
    let mut changed = false;
    for index in 0..rules.atoms.len() {
        if rules.atoms[index].fwd_code().is_some() {
            let sub_pattern_id = rules.atoms[index].sub_pattern_id();
            let bck_code = rules.atoms[index].bck_code();
            rules.atoms[index] = SubPatternAtom::from_regexp_atom(
                sub_pattern_id,
                RegexpAtom {
                    atom: Atom::from(&b"abbbc"[..]),
                    fwd_code: Some(FwdCodeLoc::from(far)),
                    bck_code,
                },
            );
            changed = true;
            break;
        }
    }
    assert!(changed, "the fixture must have an atom with forward code");

    assert!(
        yt_refuses(&rules),
        "a forward code location outside the regex code must be refused"
    );
}

#[test]
fn regex_backward_code_outside_the_code_is_refused() {
    let mut rules = yt_compiled(
        r#"rule t { strings: $a = /ab+c/ condition: $a }"#,
    );
    assert!(yt_accepts(&rules), "the unmodified fixture must be accepted");

    let far = rules.re_code.len() + 512;
    let mut changed = false;
    for index in 0..rules.atoms.len() {
        if rules.atoms[index].bck_code().is_some() {
            let sub_pattern_id = rules.atoms[index].sub_pattern_id();
            let fwd_code = rules.atoms[index].fwd_code();
            rules.atoms[index] = SubPatternAtom::from_regexp_atom(
                sub_pattern_id,
                RegexpAtom {
                    atom: Atom::from(&b"abbbc"[..]),
                    fwd_code,
                    bck_code: Some(BckCodeLoc::from(far)),
                },
            );
            changed = true;
            break;
        }
    }
    assert!(changed, "the fixture must have an atom with backward code");

    assert!(
        yt_refuses(&rules),
        "a backward code location outside the regex code must be refused"
    );
}

#[test]
fn per_pattern_scan_table_that_does_not_cover_patterns_is_refused() {
    let mut rules = yt_compiled(
        r#"rule t { strings: $a = "foobar" condition: $a }"#,
    );
    assert!(yt_accepts(&rules), "the unmodified fixture must be accepted");
    assert!(rules.num_patterns > 0);

    rules.fast_scan_patterns.truncate(0);

    assert!(
        yt_refuses(&rules),
        "a per-pattern scan table shorter than the pattern count must be refused"
    );
}

#[test]
fn per_pattern_bounds_table_that_does_not_cover_patterns_is_refused() {
    let mut rules = yt_compiled(
        r#"rule t { strings: $a = "foobar" condition: filesize < 10 and $a }"#,
    );
    assert!(yt_accepts(&rules), "the unmodified fixture must be accepted");
    assert!(rules.num_patterns > 0);
    assert_eq!(rules.filesize_bounds.len(), rules.num_patterns);

    rules.filesize_bounds.truncate(0);

    assert!(
        yt_refuses(&rules),
        "a per-pattern bounds table shorter than the pattern count must be refused"
    );
}
