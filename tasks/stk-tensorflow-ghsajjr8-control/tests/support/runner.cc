#include "runner.h"

#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/time.h>

#include <algorithm>
#include <fstream>
#include <sstream>

namespace ht {
namespace {

constexpr int kCaseTimeoutSec = 120;

std::string XmlEscape(const std::string& in) {
  std::string out;
  out.reserve(in.size());
  for (char c : in) {
    switch (c) {
      case '&': out += "&amp;"; break;
      case '<': out += "&lt;"; break;
      case '>': out += "&gt;"; break;
      case '"': out += "&quot;"; break;
      case '\'': out += "&apos;"; break;
      default:
        if (static_cast<unsigned char>(c) >= 0x20 || c == '\n' || c == '\t') {
          out += c;
        }
    }
  }
  return out;
}

std::string ReadFile(const std::string& path) {
  std::ifstream f(path.c_str(), std::ios::binary);
  std::stringstream ss;
  ss << f.rdbuf();
  return ss.str();
}

}  // namespace

std::vector<TestCase>* Registry() {
  static std::vector<TestCase> r;
  return &r;
}

int RunAll(const std::string& suite, const std::string& xml_path,
           const std::string& filter) {
  std::vector<TestCase> tests;
  for (const auto& t : *Registry()) {
    if (filter.empty() || t.name.find(filter) != std::string::npos) tests.push_back(t);
  }
  std::ofstream xml(xml_path.c_str());
  if (!xml) {
    fprintf(stderr, "cannot write %s\n", xml_path.c_str());
    return 1;
  }
  std::ostringstream body;
  int failures = 0;
  for (const auto& t : tests) {
    char errpath[] = "/tmp/ht-case-XXXXXX";
    int fd = mkstemp(errpath);
    if (fd < 0) {
      fprintf(stderr, "mkstemp failed: %s\n", strerror(errno));
      return 1;
    }
    fflush(nullptr);
    pid_t pid = fork();
    if (pid == 0) {
      dup2(fd, STDERR_FILENO);
      close(fd);
      t.fn();
      _exit(0);
    }
    std::string failure;
    if (pid < 0) {
      failure = "could not fork";
    } else {
      time_t deadline = time(nullptr) + kCaseTimeoutSec;
      int status = 0;
      bool done = false, timed_out = false;
      while (true) {
        pid_t w = waitpid(pid, &status, WNOHANG);
        if (w == pid) {
          done = true;
          break;
        }
        if (w < 0 && errno != EINTR) {
          failure = std::string("waitpid failed: ") + strerror(errno);
          done = true;
          break;
        }
        if (time(nullptr) > deadline) {
          kill(pid, SIGKILL);
          waitpid(pid, &status, 0);
          timed_out = true;
          done = true;
          break;
        }
        usleep(2000);
      }
      (void)done;
      if (timed_out) {
        failure = "timed out";
      } else if (WIFSIGNALED(status)) {
        failure = std::string("process crashed: signal ") +
                  std::to_string(WTERMSIG(status));
      } else if (WIFEXITED(status) && WEXITSTATUS(status) != 0) {
        failure = "check failed";
      }
    }
    close(fd);
    std::string err = ReadFile(errpath);
    unlink(errpath);
    if (!failure.empty()) {
      ++failures;
      if (!err.empty()) {
        if (failure == "check failed") failure = err;
        else failure += "\n" + err;
      }
    }
    body << "  <testcase classname=\"" << XmlEscape(suite) << "\" name=\""
         << XmlEscape(t.name) << "\">\n";
    if (!failure.empty()) {
      body << "    <failure message=\"" << XmlEscape(failure.substr(0, 4000))
           << "\">" << XmlEscape(failure.substr(0, 20000)) << "</failure>\n";
    }
    body << "  </testcase>\n";
  }
  xml << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<testsuites>\n";
  xml << " <testsuite name=\"" << XmlEscape(suite) << "\" tests=\""
      << tests.size() << "\" failures=\"" << failures << "\" errors=\"0\">\n";
  xml << body.str();
  xml << " </testsuite>\n</testsuites>\n";
  xml.close();
  return failures;
}

}  // namespace ht

int main(int argc, char** argv) {
  if (argc < 2) {
    fprintf(stderr, "usage: %s <junit.xml> [filter]\n", argv[0]);
    return 2;
  }
  const std::string suite = argc > 3 ? argv[3] : "tests";
  return ht::RunAll(suite, argv[1], argc > 2 ? argv[2] : "") == 0 ? 0 : 1;
}
