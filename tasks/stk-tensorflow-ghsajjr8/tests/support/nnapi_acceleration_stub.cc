// The kernel test harness links the nnapi acceleration-test table, which pulls
// in an external regex engine. No delegate is used by these tests, so the
// lookup always answers "no entry for this test".
#include <string>

#include "absl/types/optional.h"
#include "tensorflow/lite/delegates/nnapi/acceleration_test_util.h"

namespace tflite {

absl::optional<NnapiAccelerationTestParams> GetNnapiAccelerationTestParam(
    std::string) {
  return absl::nullopt;
}

}  // namespace tflite
