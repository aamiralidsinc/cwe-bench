#!/bin/bash
# Build and run one hidden group. $1 = group, $2 = JUnit XML path.
set -u
G=$1
OUT=$2
D=/workspace/.htests
B=/opt/tflite-build
CXX=/usr/bin/g++
INC="-I$D -I/workspace -I/workspace/tensorflow/lite/schema -I$B/eigen -I$B/neon2sse -I$B/abseil-cpp -I$B/farmhash/src -I$B/flatbuffers/include -I$B/gemmlowp/public -I$B/gemmlowp -I$B/ruy"
EXTRAS="/workspace/tensorflow/lite/profiling/platform_profiler.cc /workspace/tensorflow/lite/profiling/memory_info.cc /workspace/tensorflow/lite/profiling/time.cc /workspace/tensorflow/lite/tools/optimize/sparsity/format_converter.cc"
DEPS=$(find "$B/_deps" -name '*.a' 2>/dev/null)
LIBS="-Wl,--start-group $B/libtensorflowlite.a $DEPS -Wl,--end-group -lpthread -ldl -lrt"
COMMON="$D/support/runner.cc"
FLAGS="-std=c++14 -O1 -g0 -w"

if [ "$G" = security ]; then
  $CXX $FLAGS $INC "$COMMON" "$D"/security/*.cc $EXTRAS -o /tmp/ht-security $LIBS || exit 1
  exec /tmp/ht-security "$OUT" "" SecuritySuite
fi

$CXX $FLAGS $INC "$COMMON" "$D"/functional/*.cc $EXTRAS -o /tmp/ht-functional $LIBS || exit 1

# The project's own tests for the affected operators, compiled from the pristine
# copies shipped in this image against the tree under test.
P=/opt/project-tests
GT="-I/opt/gtest/include"
$CXX $FLAGS $INC $GT -I/opt/generated \
  "$P/reshape_test.cc" "$P/expand_dims_test.cc" "$P/test_util.cc" \
  "$P/acceleration_test_util.cc" "$D/support/nnapi_acceleration_stub.cc" \
  $EXTRAS \
  /workspace/tensorflow/lite/tools/tool_params.cc \
  /workspace/tensorflow/lite/tools/command_line_flags.cc \
  /workspace/tensorflow/lite/tools/versioning/op_version.cc \
  /workspace/tensorflow/core/platform/default/logging.cc \
  /workspace/tensorflow/core/platform/default/env_time.cc \
  -Wl,--start-group $B/libtensorflowlite.a $DEPS -Wl,--end-group \
  /opt/gtest/lib/libgmock.a /opt/gtest/lib/libgtest.a /opt/gtest/lib/libgtest_main.a \
  -lpthread -ldl -lrt -o /tmp/ht-project-kernel-tests || exit 1

export HT_PROJECT_KERNEL_TESTS=/tmp/ht-project-kernel-tests
exec /tmp/ht-functional "$OUT" "" FunctionalSuite
