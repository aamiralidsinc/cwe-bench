// Legitimate models must keep working: ordinary operators, models whose shape
// comes from an ignored second input, and tensors that are legitimately empty.
#include "support/check.h"
#include "support/model.h"
#include "support/run_model.h"
#include "support/runner.h"

namespace {

ht::LoadedModel BuildAndAllocate(const std::vector<uint8_t>& bytes) {
  ht::LoadedModel m = ht::Load(bytes);
  HT_CHECK(m.model != nullptr);
  HT_CHECK(m.interpreter != nullptr);
  ht::ExpectSuccess(m, m.interpreter->AllocateTensors(), "AllocateTensors");
  return m;
}

}  // namespace

// A second input the reshape never consults (a rank-2 tensor the operator
// ignores in favour of its own options) may legitimately have no data.
HT_TEST(FunctionalSuite, Reshape_IgnoredSecondInputWithoutData) {
  ht::ModelBuilder b;
  int data = b.AddConstVector<float>(tflite::TensorType_FLOAT32, {2, 2},
                                     {1.f, 2.f, 3.f, 4.f});
  int ignored = b.AddTensor(tflite::TensorType_INT32, {2, 1});
  int out = b.AddTensor(tflite::TensorType_FLOAT32, {4});
  b.AddOp(tflite::BuiltinOperator_RESHAPE, {data, ignored}, {out},
          tflite::BuiltinOptions_ReshapeOptions, b.ReshapeOptions({4}));
  ht::LoadedModel m = BuildAndAllocate(b.Finish({}, {out}));
  ht::ExpectSuccess(m, m.interpreter->Invoke(), "Invoke");
  ht::ExpectShapeEq(*m.interpreter, out, {4});
  ht::ExpectFloatEq(*m.interpreter, out, {1.f, 2.f, 3.f, 4.f});
}

// The classic shape-from-tensor form keeps working.
HT_TEST(FunctionalSuite, Reshape_ShapeFromConstantTensor) {
  ht::ModelBuilder b;
  int data = b.AddConstVector<float>(tflite::TensorType_FLOAT32, {2, 2},
                                     {1.f, 2.f, 3.f, 4.f});
  int shape = b.AddConstVector<int32_t>(tflite::TensorType_INT32, {1}, {4});
  int out = b.AddTensor(tflite::TensorType_FLOAT32, {4});
  b.AddOp(tflite::BuiltinOperator_RESHAPE, {data, shape}, {out},
          tflite::BuiltinOptions_ReshapeOptions, b.ReshapeOptions({4}));
  ht::LoadedModel m = BuildAndAllocate(b.Finish({}, {out}));
  ht::ExpectSuccess(m, m.interpreter->Invoke(), "Invoke");
  ht::ExpectShapeEq(*m.interpreter, out, {4});
  ht::ExpectFloatEq(*m.interpreter, out, {1.f, 2.f, 3.f, 4.f});
}

// A reshape with no shape input at all uses its own options.
HT_TEST(FunctionalSuite, Reshape_ShapeFromOptionsOnly) {
  ht::ModelBuilder b;
  int data = b.AddConstVector<float>(tflite::TensorType_FLOAT32, {2, 2},
                                     {1.f, 2.f, 3.f, 4.f});
  int out = b.AddTensor(tflite::TensorType_FLOAT32, {4});
  b.AddOp(tflite::BuiltinOperator_RESHAPE, {data}, {out},
          tflite::BuiltinOptions_ReshapeOptions, b.ReshapeOptions({4}));
  ht::LoadedModel m = BuildAndAllocate(b.Finish({}, {out}));
  ht::ExpectSuccess(m, m.interpreter->Invoke(), "Invoke");
  ht::ExpectShapeEq(*m.interpreter, out, {4});
  ht::ExpectFloatEq(*m.interpreter, out, {1.f, 2.f, 3.f, 4.f});
}

// A tensor that legitimately holds no elements has no buffer either; an
// operation over it must not be refused.
HT_TEST(FunctionalSuite, Reshape_EmptyTensor) {
  ht::ModelBuilder b;
  int data = b.AddConstTensor(tflite::TensorType_FLOAT32, {0, 2}, nullptr, 0);
  int out = b.AddTensor(tflite::TensorType_FLOAT32, {0, 2});
  b.AddOp(tflite::BuiltinOperator_RESHAPE, {data}, {out},
          tflite::BuiltinOptions_ReshapeOptions, b.ReshapeOptions({0, 2}));
  ht::LoadedModel m = BuildAndAllocate(b.Finish({}, {out}));
  ht::ExpectSuccess(m, m.interpreter->Invoke(), "Invoke");
  ht::ExpectShapeEq(*m.interpreter, out, {0, 2});
}

// Ordinary expand-dims on a real input keeps working.
HT_TEST(FunctionalSuite, ExpandDims_Normal) {
  ht::ModelBuilder b;
  int data = b.AddTensor(tflite::TensorType_FLOAT32, {2});
  int axis = b.AddConstVector<int32_t>(tflite::TensorType_INT32, {1}, {0});
  int out = b.AddTensor(tflite::TensorType_FLOAT32, {1, 2});
  b.AddOp(tflite::BuiltinOperator_EXPAND_DIMS, {data, axis}, {out},
          tflite::BuiltinOptions_ExpandDimsOptions, b.ExpandDimsOptions());
  ht::LoadedModel m = BuildAndAllocate(b.Finish({data}, {out}));
  float* input = m.interpreter->typed_tensor<float>(data);
  input[0] = 3.f;
  input[1] = 4.f;
  ht::ExpectSuccess(m, m.interpreter->Invoke(), "Invoke");
  ht::ExpectShapeEq(*m.interpreter, out, {1, 2});
  ht::ExpectFloatEq(*m.interpreter, out, {3.f, 4.f});
}

// Ordinary addition keeps working.
HT_TEST(FunctionalSuite, Add_Normal) {
  ht::ModelBuilder b;
  int a = b.AddConstVector<float>(tflite::TensorType_FLOAT32, {2}, {1.f, 2.f});
  int c = b.AddConstVector<float>(tflite::TensorType_FLOAT32, {2}, {10.f, 20.f});
  int out = b.AddTensor(tflite::TensorType_FLOAT32, {2});
  b.AddOp(tflite::BuiltinOperator_ADD, {a, c}, {out},
          tflite::BuiltinOptions_AddOptions, b.AddOptions());
  ht::LoadedModel m = BuildAndAllocate(b.Finish({}, {out}));
  ht::ExpectSuccess(m, m.interpreter->Invoke(), "Invoke");
  ht::ExpectFloatEq(*m.interpreter, out, {11.f, 22.f});
}
