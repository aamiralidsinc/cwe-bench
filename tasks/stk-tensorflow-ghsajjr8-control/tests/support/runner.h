// Forking test runner: every case runs in its own child process, so a crash in the
// code under test is recorded as a failing case instead of losing the whole report.
#ifndef HT_RUNNER_H_
#define HT_RUNNER_H_

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include <string>
#include <vector>

namespace ht {

struct TestCase {
  std::string name;
  void (*fn)();
};

std::vector<TestCase>* Registry();

struct Registrar {
  Registrar(const char* name, void (*fn)()) { Registry()->push_back({name, fn}); }
};

// Runs every registered case (optionally only those whose name contains
// `filter`), writes JUnit XML to `xml_path`, returns the number of failures.
int RunAll(const std::string& suite, const std::string& xml_path,
           const std::string& filter);

}  // namespace ht

#define HT_TEST_I(suite, name, id)                                    \
  static void ht_test_##id();                                         \
  static ::ht::Registrar ht_reg_##id(#suite "." #name, ht_test_##id); \
  static void ht_test_##id()
#define HT_TEST_II(suite, name, id) HT_TEST_I(suite, name, id)
#define HT_TEST(suite, name) HT_TEST_II(suite, name, __COUNTER__)

#define HT_CHECK(cond)                                                     \
  do {                                                                     \
    if (!(cond)) {                                                         \
      fprintf(stderr, "CHECK failed at %s:%d: %s\n", __FILE__, __LINE__,   \
              #cond);                                                      \
      _exit(1);                                                            \
    }                                                                      \
  } while (0)

#endif  // HT_RUNNER_H_
