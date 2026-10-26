// A node must not read an input tensor whose data buffer was never allocated.
// Each case builds a model in which a tensor that a kernel reads has no buffer;
// the interpreter is expected to refuse cleanly instead of dereferencing it.
#include "support/model.h"
#include "support/run_model.h"
#include "support/runner.h"

namespace {

void RunOrRefuse(const std::vector<uint8_t>& bytes) {
  ht::LoadedModel m = ht::Load(bytes);
  // Refusing the model while it is loaded is a clean refusal.
  if (m.model == nullptr || m.interpreter == nullptr) return;
  // Either call may refuse; neither may crash.
  m.interpreter->AllocateTensors();
  m.interpreter->Invoke();
}

}  // namespace

HT_TEST(SecuritySuite, ExpandDims_InputWithoutData) {
  ht::ModelBuilder b;
  int data = b.AddTensor(tflite::TensorType_FLOAT32, {2});
  int axis = b.AddConstVector<int32_t>(tflite::TensorType_INT32, {1}, {0});
  int out = b.AddTensor(tflite::TensorType_FLOAT32, {1, 2});
  b.AddOp(tflite::BuiltinOperator_EXPAND_DIMS, {data, axis}, {out},
          tflite::BuiltinOptions_ExpandDimsOptions, b.ExpandDimsOptions());
  RunOrRefuse(b.Finish({}, {out}));
}

HT_TEST(SecuritySuite, Add_InputWithoutData) {
  ht::ModelBuilder b;
  int data = b.AddTensor(tflite::TensorType_FLOAT32, {2});
  int other = b.AddConstVector<float>(tflite::TensorType_FLOAT32, {2}, {1.f, 1.f});
  int out = b.AddTensor(tflite::TensorType_FLOAT32, {2});
  b.AddOp(tflite::BuiltinOperator_ADD, {data, other}, {out},
          tflite::BuiltinOptions_AddOptions, b.AddOptions());
  RunOrRefuse(b.Finish({}, {out}));
}

HT_TEST(SecuritySuite, Reshape_DataInputWithoutData) {
  ht::ModelBuilder b;
  int data = b.AddTensor(tflite::TensorType_FLOAT32, {2, 2});
  int shape = b.AddConstVector<int32_t>(tflite::TensorType_INT32, {1}, {4});
  int out = b.AddTensor(tflite::TensorType_FLOAT32, {4});
  b.AddOp(tflite::BuiltinOperator_RESHAPE, {data, shape}, {out},
          tflite::BuiltinOptions_ReshapeOptions, b.ReshapeOptions({4}));
  RunOrRefuse(b.Finish({}, {out}));
}

HT_TEST(SecuritySuite, Reshape_ShapeTensorWithoutData) {
  ht::ModelBuilder b;
  int data = b.AddConstVector<float>(tflite::TensorType_FLOAT32, {2, 2},
                                     {1.f, 2.f, 3.f, 4.f});
  // Rank-1 int32 shape tensor that nothing ever writes: the reshape kernel
  // reads its elements to compute the output shape.
  int shape = b.AddTensor(tflite::TensorType_INT32, {2});
  int out = b.AddTensor(tflite::TensorType_FLOAT32, {4});
  b.AddOp(tflite::BuiltinOperator_RESHAPE, {data, shape}, {out},
          tflite::BuiltinOptions_ReshapeOptions, b.ReshapeOptions({2, 2}));
  RunOrRefuse(b.Finish({}, {out}));
}

HT_TEST(SecuritySuite, Reshape_OmittedShapeInput) {
  ht::ModelBuilder b;
  int data = b.AddConstVector<float>(tflite::TensorType_FLOAT32, {2, 2},
                                     {1.f, 2.f, 3.f, 4.f});
  int out = b.AddTensor(tflite::TensorType_FLOAT32, {4});
  // The second input of the node is marked absent.
  b.AddOp(tflite::BuiltinOperator_RESHAPE, {data, -1}, {out},
          tflite::BuiltinOptions_ReshapeOptions, b.ReshapeOptions({4}));
  RunOrRefuse(b.Finish({}, {out}));
}
