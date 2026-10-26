// The project's own kernel tests for the operators touched here, built from
// the pristine test sources against the tree under test.
#include <stdlib.h>

#include <cstdio>

#include "support/runner.h"

namespace {

int RunProjectBinary() {
  const char* bin = getenv("HT_PROJECT_KERNEL_TESTS");
  if (bin == nullptr || bin[0] == '\0') {
    fprintf(stderr, "HT_PROJECT_KERNEL_TESTS is not set\n");
    return -1;
  }
  int status = system(bin);
  if (status != 0) {
    fprintf(stderr, "project kernel tests failed (status %d)\n", status);
    return status;
  }
  return 0;
}

}  // namespace

HT_TEST(FunctionalSuite, ProjectKernelTests) {
  int rc = RunProjectBinary();
  if (rc != 0) _exit(1);
}
