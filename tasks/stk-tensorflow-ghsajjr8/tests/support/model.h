// Minimal in-memory builder for TFLite flatbuffer models, used by the task's
// behavioural tests.  A tensor that is added with no data buffer and is not a
// graph input or a node output is exactly the shape a hand-crafted model can
// declare: it exists, it has a size, and nothing ever allocates memory for it.
#ifndef HT_MODEL_H_
#define HT_MODEL_H_

#include <stdint.h>
#include <string.h>

#include <string>
#include <vector>

#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"

namespace ht {

class ModelBuilder {
 public:
  ModelBuilder() { buffers_.push_back(tflite::CreateBuffer(builder_)); }

  // A tensor with no data buffer (buffer index 0).
  int AddTensor(tflite::TensorType type, const std::vector<int>& shape) {
    int id = static_cast<int>(tensors_.size());
    tensors_.push_back(tflite::CreateTensor(
        builder_, builder_.CreateVector<int32_t>(Vec(shape)), type,
        /*buffer=*/0, /*name=*/0, /*quantization=*/0, /*is_variable=*/false));
    return id;
  }

  // A tensor backed by constant data.
  int AddConstTensor(tflite::TensorType type, const std::vector<int>& shape,
                     const void* data, size_t bytes) {
    int id = static_cast<int>(tensors_.size());
    uint32_t buffer_id = 0;
    if (bytes > 0 && data != nullptr) {
      buffer_id = static_cast<uint32_t>(buffers_.size());
      buffers_.push_back(tflite::CreateBuffer(
          builder_,
          builder_.CreateVector(reinterpret_cast<const uint8_t*>(data), bytes)));
    }
    tensors_.push_back(tflite::CreateTensor(
        builder_, builder_.CreateVector<int32_t>(Vec(shape)), type, buffer_id,
        /*name=*/0, /*quantization=*/0, /*is_variable=*/false));
    return id;
  }

  template <typename T>
  int AddConstVector(tflite::TensorType type, const std::vector<int>& shape,
                     const std::vector<T>& data) {
    return AddConstTensor(type, shape, data.data(), data.size() * sizeof(T));
  }

  void AddOp(tflite::BuiltinOperator op, const std::vector<int>& inputs,
             const std::vector<int>& outputs,
             tflite::BuiltinOptions options_type = tflite::BuiltinOptions_NONE,
             flatbuffers::Offset<void> options = 0) {
    uint32_t opcode_index = static_cast<uint32_t>(opcodes_.size());
    opcodes_.push_back(tflite::CreateOperatorCode(builder_, op, 0, 1));
    operators_.push_back(tflite::CreateOperator(
        builder_, opcode_index, builder_.CreateVector<int32_t>(Vec(inputs)),
        builder_.CreateVector<int32_t>(Vec(outputs)), options_type, options));
  }

  flatbuffers::Offset<void> ReshapeOptions(const std::vector<int>& shape) {
    return tflite::CreateReshapeOptions(
               builder_, builder_.CreateVector<int32_t>(Vec(shape)))
        .Union();
  }

  flatbuffers::Offset<void> ExpandDimsOptions() {
    return tflite::CreateExpandDimsOptions(builder_).Union();
  }

  flatbuffers::Offset<void> AddOptions() {
    return tflite::CreateAddOptions(builder_,
                                    tflite::ActivationFunctionType_NONE, true)
        .Union();
  }

  std::vector<uint8_t> Finish(const std::vector<int>& inputs,
                              const std::vector<int>& outputs) {
    auto subgraph = tflite::CreateSubGraph(
        builder_, builder_.CreateVector(tensors_),
        builder_.CreateVector<int32_t>(Vec(inputs)),
        builder_.CreateVector<int32_t>(Vec(outputs)),
        builder_.CreateVector(operators_));
    std::vector<flatbuffers::Offset<tflite::SubGraph>> subgraphs{subgraph};
    auto model = tflite::CreateModel(
        builder_, TFLITE_SCHEMA_VERSION, builder_.CreateVector(opcodes_),
        builder_.CreateVector(subgraphs), builder_.CreateString("harness"),
        builder_.CreateVector(buffers_));
    builder_.Finish(model, "TFL3");
    return std::vector<uint8_t>(builder_.GetBufferPointer(),
                                builder_.GetBufferPointer() + builder_.GetSize());
  }

 private:
  static std::vector<int32_t> Vec(const std::vector<int>& v) {
    return std::vector<int32_t>(v.begin(), v.end());
  }

  flatbuffers::FlatBufferBuilder builder_;
  std::vector<flatbuffers::Offset<tflite::Tensor>> tensors_;
  std::vector<flatbuffers::Offset<tflite::Operator>> operators_;
  std::vector<flatbuffers::Offset<tflite::OperatorCode>> opcodes_;
  std::vector<flatbuffers::Offset<tflite::Buffer>> buffers_;
};

}  // namespace ht

#endif  // HT_MODEL_H_
