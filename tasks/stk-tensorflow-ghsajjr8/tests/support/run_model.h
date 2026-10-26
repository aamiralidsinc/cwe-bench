// Loading and execution helpers for the behavioural tests.
#ifndef HT_RUN_MODEL_H_
#define HT_RUN_MODEL_H_

#include <stdint.h>

#include <memory>
#include <vector>

#include "tensorflow/lite/interpreter.h"
#include "tensorflow/lite/kernels/register.h"
#include "tensorflow/lite/model.h"

namespace ht {

struct LoadedModel {
  std::unique_ptr<tflite::FlatBufferModel> model;
  std::unique_ptr<tflite::Interpreter> interpreter;
};

// Loads a serialized model through the public API and builds an interpreter.
// Dies with a check failure if the model cannot be built at all.
inline LoadedModel Load(const std::vector<uint8_t>& bytes) {
  LoadedModel out;
  out.model = tflite::FlatBufferModel::BuildFromBuffer(
      reinterpret_cast<const char*>(bytes.data()), bytes.size());
  if (!out.model) return out;
  tflite::ops::builtin::BuiltinOpResolver resolver;
  tflite::InterpreterBuilder builder(*out.model, resolver);
  builder(&out.interpreter);
  return out;
}

}  // namespace ht

#endif  // HT_RUN_MODEL_H_
