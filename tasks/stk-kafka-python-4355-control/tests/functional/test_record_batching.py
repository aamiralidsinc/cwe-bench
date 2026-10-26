"""Legitimate compressed and uncompressed record batches keep decoding unchanged.

Real batches expand far beyond their compressed size (repeated values, structured payloads),
and a compressed stream may consist of several concatenated frames.  Both must keep working.
"""

import pytest

from kafka.codec import has_zstd, zstd_encode
from kafka.record.default_records import DefaultRecordBatch, DefaultRecordBatchBuilder
from kafka.record.legacy_records import LegacyRecordBatch, LegacyRecordBatchBuilder

LARGE_VALUE = b'A' * (20 * 1024 * 1024)


def _v2_builder(compression_type, batch_size):
    return DefaultRecordBatchBuilder(
        magic=2, compression_type=compression_type, is_transactional=0,
        producer_id=-1, producer_epoch=-1, base_sequence=-1, batch_size=batch_size)


def test_highly_compressible_batch_decodes():
    builder = _v2_builder(DefaultRecordBatch.CODEC_GZIP, 64 * 1024 * 1024)
    builder.append(0, 1000, b'first', LARGE_VALUE, headers=[])
    builder.append(1, 1001, b'second', b'small', headers=[])
    batch = DefaultRecordBatch(bytes(builder.build()))
    records = list(batch)
    assert [(record.key, len(record.value)) for record in records] == [
        (b'first', len(LARGE_VALUE)), (b'second', 5)]
    assert records[0].value == LARGE_VALUE


@pytest.mark.skipif(not has_zstd(), reason='zstandard is not installed')
def test_multi_frame_compressed_batch_decodes():
    builder = _v2_builder(DefaultRecordBatch.CODEC_NONE, 1024 * 1024)
    builder.append(0, 1000, b'a', b'first-value-0123456789', headers=[])
    builder.append(1, 1001, b'b', b'second-value-0123456789', headers=[])
    raw = bytes(builder.build())
    header_size = DefaultRecordBatch.HEADER_STRUCT.size
    records = raw[header_size:]
    half = len(records) // 2
    payload = zstd_encode(records[:half]) + zstd_encode(records[half:])
    header = list(DefaultRecordBatch.HEADER_STRUCT.unpack_from(raw))
    header[1] = len(raw) - 12 - len(records) + len(payload)
    header[5] = DefaultRecordBatch.CODEC_ZSTD
    buffer = DefaultRecordBatch.HEADER_STRUCT.pack(*header) + payload
    decoded = list(DefaultRecordBatch(buffer))
    assert [(record.offset, record.key, record.value) for record in decoded] == [
        (0, b'a', b'first-value-0123456789'),
        (1, b'b', b'second-value-0123456789')]


def test_legacy_compressed_batch_decodes():
    builder = LegacyRecordBatchBuilder(magic=1, compression_type=1, batch_size=9999999)
    for offset in range(10):
        builder.append(offset, timestamp=9999999, key=b'test', value=b'Super')
    records = list(LegacyRecordBatch(bytes(builder.build()), 1))
    assert [record.offset for record in records] == list(range(10))
    assert all(record.key == b'test' and record.value == b'Super' for record in records)


def test_legacy_uncompressed_batch_decodes():
    builder = LegacyRecordBatchBuilder(magic=1, compression_type=0, batch_size=9999999)
    builder.append(0, timestamp=9999999, key=b'key', value=b'value')
    records = list(LegacyRecordBatch(bytes(builder.build()), 1))
    assert len(records) == 1
    assert records[0].key == b'key' and records[0].value == b'value'
