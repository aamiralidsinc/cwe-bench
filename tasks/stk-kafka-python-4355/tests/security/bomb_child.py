"""Resource probe run in a child process with a hard address-space limit.

argv: <mode> <expansion_mb> <memory_limit_mb>

mode "v2"           a compressed record batch whose decompressed size is <expansion_mb>
mode "legacy_bomb"  the same expansion inside a compressed legacy message set
mode "legacy_loop"  a compressed legacy message set whose first declared message length makes
                    the parse revisit the same offset forever

Exit status: 0 the product raised an explicit error (refused), 2 the product returned a result,
3 it ran out of memory, anything else is an unclean end.
"""

import resource
import struct
import sys
import zlib

mode, expansion_mb, limit_mb = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
limit = limit_mb << 20
resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

BATCH_HEADER = struct.Struct(">qiibIhiqqqhii")


def gzip_zeros(total):
    compressor = zlib.compressobj(6, zlib.DEFLATED, 31)
    chunk = b'\0' * (1 << 20)
    parts = [compressor.compress(chunk) for _ in range(total // len(chunk))]
    parts.append(compressor.flush())
    return b''.join(parts)


def v2_bomb(expansion):
    blob = gzip_zeros(expansion)
    length = BATCH_HEADER.size - 12 + len(blob)
    # base_offset, length, leader_epoch, magic=2, crc, attributes=gzip, ...
    return BATCH_HEADER.pack(0, length, 0, 2, 0, 1, 0, 0, 0, -1, -1, -1, 1) + blob


def legacy_outer(value_blob):
    body = (struct.pack(">Ibbq", 0, 1, 1, 0)          # crc, magic=1, attributes=gzip, timestamp
            + struct.pack(">i", -1)                    # null key
            + struct.pack(">i", len(value_blob)) + value_blob)
    return struct.pack(">qi", 0, len(body)) + body


def run_v2():
    from kafka.record.default_records import DefaultRecordBatch
    list(DefaultRecordBatch(v2_bomb(expansion_mb << 20)))


def run_legacy_bomb():
    from kafka.record.legacy_records import LegacyRecordBatch
    list(LegacyRecordBatch(legacy_outer(gzip_zeros(expansion_mb << 20)), 1))


def run_legacy_loop():
    from kafka.record.legacy_records import LegacyRecordBatch
    compressor = zlib.compressobj(6, zlib.DEFLATED, 31)
    inner = struct.pack(">qiIbbq", 0, -12, 0, 1, 0, 0) + b'\0' * 16
    blob = compressor.compress(inner) + compressor.flush()
    list(LegacyRecordBatch(legacy_outer(blob), 1))


try:
    {'v2': run_v2, 'legacy_bomb': run_legacy_bomb, 'legacy_loop': run_legacy_loop}[mode]()
except MemoryError:
    print('MemoryError')
    sys.exit(3)
except Exception as exc:  # noqa: BLE001 - any explicit refusal is what the probe looks for
    print('refused:%s:%s' % (type(exc).__name__, str(exc)[:200]))
    sys.exit(0)
else:
    print('returned')
    sys.exit(2)
