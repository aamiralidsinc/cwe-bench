#include <TestSupport.h>
#include <tut/tut_reporter.h>
#include <iostream>
namespace tut { test_runner_singleton runner; }
int main(int argc, char **argv) {
    tut::reporter reporter;
    tut::runner.get().set_callback(&reporter);
    try {
        if (argc > 1) tut::runner.get().run_tests(std::string(argv[1]));
        else tut::runner.get().run_tests();
    } catch (const std::exception &e) {
        std::cerr << "FATAL: " << e.what() << std::endl;
        return 2;
    }
    return reporter.all_ok() ? 0 : 1;
}
