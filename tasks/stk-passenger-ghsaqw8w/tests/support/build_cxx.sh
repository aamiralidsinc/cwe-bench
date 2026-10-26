#!/bin/bash
# Compile the product's public server-instance-directory API, the neutral driver, and the
# project's own ServerInstanceDir test. Runs offline as the verifier user.
set -eu
WS=$(readlink -f "$1"); HID=$(readlink -f "$2"); OUT=$(readlink -f "$3")
INC="-I$WS/ext -I$WS/ext/common -I$WS/ext/oxt -I$WS/ext/libev -I$WS/test -I$WS/test/cxx -I$WS/test/support"
CXX="g++ -std=c++11 -w -pthread -ffunction-sections -fdata-sections $INC"
mkdir -p "$OUT/obj" "$OUT/bin"
cd "$OUT"
compile() { $CXX -c "$1" -o "$2"; }
PRODUCT=""
for spec in \
  "$WS/ext/oxt/implementation.cpp:oxt_implementation" \
  "$WS/ext/oxt/system_calls.cpp:oxt_system_calls" \
  "$WS/ext/boost/libs/system/src/error_code.cpp:boost_error_code" \
  "$WS/ext/boost/libs/thread/src/pthread/thread.cpp:boost_thread" \
  "$WS/ext/boost/libs/thread/src/pthread/once.cpp:boost_once" \
  "$WS/ext/boost/libs/thread/src/future.cpp:boost_future" \
  "$WS/ext/common/Logging.cpp:logging" \
  "$WS/ext/common/Utils.cpp:utils" \
  "$WS/ext/common/Utils/StrIntUtils.cpp:strintutils" \
  "$WS/ext/common/Utils/IOUtils.cpp:ioutils" \
  "$WS/ext/common/Utils/SystemTime.cpp:systemtime" \
  "$WS/ext/common/Utils/jsoncpp.cpp:jsoncpp" ; do
  f=${spec%:*}; o=${spec##*:}; compile "$f" "obj/$o.o"; PRODUCT="$PRODUCT obj/$o.o"
done
compile "$HID/support/harness.cpp" obj/harness.o
g++ -pthread -Wl,--gc-sections $PRODUCT obj/harness.o -o bin/harness -lpthread -ldl
compile "$WS/test/cxx/TestSupport.cpp" obj/testsupport.o
compile "$WS/test/cxx/ServerInstanceDirTest.cpp" obj/sidtest.o
compile "$HID/support/tutmain.cpp" obj/tutmain.o
g++ -pthread -Wl,--gc-sections $PRODUCT obj/testsupport.o obj/sidtest.o obj/tutmain.o -o bin/sidtest -lpthread -ldl
