#ifndef HT_CHECK_H_
#define HT_CHECK_H_

#include <stdint.h>

#include <string>
#include <vector>

#include "support/run_model.h"
#include "support/runner.h"

namespace ht {

inline std::vector<int> TensorShape(const tflite::Interpreter& interpreter,
                                    int index) {
  const TfLiteIntArray* dims = interpreter.tensor(index)->dims;
  std::vector<int> shape;
  if (dims == nullptr) return shape;
  for (int i = 0; i < dims->size; ++i) shape.push_back(dims->data[i]);
  return shape;
}

inline std::vector<float> FloatValues(const tflite::Interpreter& interpreter,
                                      int index) {
  const TfLiteTensor* t = interpreter.tensor(index);
  std::vector<float> out;
  if (t->data.f == nullptr) return out;
  int64_t n = 1;
  for (int i = 0; i < t->dims->size; ++i) n *= t->dims->data[i];
  for (int64_t i = 0; i < n; ++i) out.push_back(t->data.f[i]);
  return out;
}

inline std::vector<int32_t> IntValues(const tflite::Interpreter& interpreter,
                                      int index) {
  const TfLiteTensor* t = interpreter.tensor(index);
  std::vector<int32_t> out;
  if (t->data.i32 == nullptr) return out;
  int64_t n = 1;
  for (int i = 0; i < t->dims->size; ++i) n *= t->dims->data[i];
  for (int64_t i = 0; i < n; ++i) out.push_back(t->data.i32[i]);
  return out;
}

inline void ExpectSuccess(const LoadedModel& m, TfLiteStatus status,
                          const char* what) {
  if (status != kTfLiteOk) {
    fprintf(stderr, "%s failed with status %d\n", what, static_cast<int>(status));
    _exit(1);
  }
}

inline void ExpectShapeEq(const tflite::Interpreter& interpreter, int index,
                          const std::vector<int>& expected) {
  std::vector<int> got = TensorShape(interpreter, index);
  if (got != expected) {
    fprintf(stderr, "output shape mismatch: expected %s got %s\n",
            [&] { std::string s; for (int v : expected) s += std::to_string(v) + " "; return s.c_str(); }(),
            [&] { std::string s; for (int v : got) s += std::to_string(v) + " "; return s.c_str(); }());
    _exit(1);
  }
}

inline void ExpectFloatEq(const tflite::Interpreter& interpreter, int index,
                          const std::vector<float>& expected) {
  std::vector<float> got = FloatValues(interpreter, index);
  if (got.size() != expected.size()) {
    fprintf(stderr, "output size mismatch: expected %zu got %zu\n",
            expected.size(), got.size());
    _exit(1);
  }
  for (size_t i = 0; i < got.size(); ++i) {
    if (got[i] != expected[i]) {
      fprintf(stderr, "output[%zu]: expected %f got %f\n", i, expected[i], got[i]);
      _exit(1);
    }
  }
}

}  // namespace ht

#endif  // HT_CHECK_H_
