//! Security suite: a model whose declared tensor dimensions overflow the size arithmetic used to
//! allocate or to shape that tensor must be refused with an error. Nothing here runs the malformed
//! tensor; the assertion is only that reading the model does not succeed.
mod common;

use common::*;

/// Plain f32: the element count fits a usize but the byte count does not.
#[test]
fn sec_dat_plain_byte_size_overflow_is_refused() {
    let file = dat(&[1 << 31, 1 << 31], 0, 32, 0, 0, &[]);
    assert!(
        tract_nnef::tensors::read_tensor(&file[..]).is_err(),
        "a tensor file whose dimensions overflow its byte count must be refused"
    );
}

/// Plain f64: a different element width reaches the same sink.
#[test]
fn sec_dat_wide_element_overflow_is_refused() {
    let file = dat(&[1 << 31, 1 << 31], 0, 64, 0, 0, &[]);
    assert!(
        tract_nnef::tensors::read_tensor(&file[..]).is_err(),
        "a tensor file whose dimensions overflow its byte count must be refused"
    );
}

/// Plain u8: the element count itself does not fit a usize.
#[test]
fn sec_dat_element_count_overflow_is_refused() {
    let file = dat(&[1 << 31, 1 << 31, 1 << 31], 0, 8, 1, 0, &[]);
    assert!(
        tract_nnef::tensors::read_tensor(&file[..]).is_err(),
        "a tensor file whose element count overflows must be refused"
    );
}

/// The same file reaching the loader through a model directory.
#[test]
fn sec_nnef_model_dat_overflow_is_refused() {
    let graph = "version 1.0;\n\nextension tract_registry tract_core;\n\n\
                 graph net() -> (output_0)\n{\n    \
                 output_0 = variable(label = 'w', shape = [2147483648, 2147483648]);\n}\n";
    let dir = nnef_model(
        "sec-model-overflow",
        graph,
        &[("w.dat", dat(&[1 << 31, 1 << 31], 0, 32, 0, 0, &[]))],
    );
    match load_nnef(&dir) {
        Ok(Err(_)) => {}
        Ok(Ok(_)) => panic!("a model with an overflowing tensor dimension was loaded"),
        Err(()) => panic!("the loader crashed instead of refusing the model"),
    }
}
