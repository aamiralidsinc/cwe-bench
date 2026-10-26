/*
 * Minimal JUnit 4 runner that writes one JUnit XML file for the test classes named on the
 * command line. Usage: JUnitXmlRunner <output.xml> <class> [<class> ...]
 */
package hidden.support;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.junit.runner.Description;
import org.junit.runner.JUnitCore;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;
import org.junit.runner.notification.RunListener;

public final class JUnitXmlRunner {

    private JUnitXmlRunner() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("usage: JUnitXmlRunner <output.xml> <class> [<class> ...]");
            System.exit(2);
        }
        String output = args[0];
        List<Class<?>> classes = new ArrayList<>();
        for (int i = 1; i < args.length; i++) {
            classes.add(Class.forName(args[i]));
        }

        Collector collector = new Collector();
        JUnitCore core = new JUnitCore();
        core.addListener(collector);
        for (Class<?> testClass : classes) {
            Result result = core.run(testClass);
            if (result.getFailureCount() > 0) {
                for (Failure failure : result.getFailures()) {
                    if (failure.getDescription().getMethodName() == null) {
                        collector.recordClassFailure(testClass.getName(), failure);
                    }
                }
            }
        }
        collector.write(output);
    }

    private static final class Collector extends RunListener {
        private final Map<String, Case> cases = new LinkedHashMap<>();
        private final Map<String, String> classFailures = new LinkedHashMap<>();

        @Override
        public void testStarted(Description description) {
            cases.computeIfAbsent(key(description), k -> new Case(description));
        }

        @Override
        public void testFinished(Description description) {
            cases.computeIfAbsent(key(description), k -> new Case(description));
        }

        @Override
        public void testFailure(Failure failure) {
            Description description = failure.getDescription();
            Case testCase = cases.computeIfAbsent(key(description), k -> new Case(description));
            boolean assertion = failure.getException() instanceof AssertionError;
            if (testCase.status == null || "pass".equals(testCase.status)) {
                testCase.status = assertion ? "fail" : "error";
                testCase.message = failure.getMessage();
                testCase.trace = failure.getTrace();
            }
        }

        @Override
        public void testAssumptionFailure(Failure failure) {
            Description description = failure.getDescription();
            Case testCase = cases.computeIfAbsent(key(description), k -> new Case(description));
            testCase.status = "skipped";
            testCase.message = failure.getMessage();
        }

        @Override
        public void testIgnored(Description description) {
            Case testCase = cases.computeIfAbsent(key(description), k -> new Case(description));
            testCase.status = "skipped";
        }

        void recordClassFailure(String className, Failure failure) {
            classFailures.put(className, failure.getTrace());
        }

        private static String key(Description description) {
            return description.getClassName() + "#" + description.getMethodName();
        }

        void write(String path) throws IOException {
            int tests = cases.size() + classFailures.size();
            int failures = 0;
            int errors = 0;
            int skipped = 0;
            for (Case testCase : cases.values()) {
                if ("fail".equals(testCase.status)) {
                    failures++;
                } else if ("error".equals(testCase.status)) {
                    errors++;
                } else if ("skipped".equals(testCase.status)) {
                    skipped++;
                }
            }
            errors += classFailures.size();
            try (PrintWriter out = new PrintWriter(new FileWriter(path))) {
                out.println("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
                out.println("<testsuite name=\"hidden\" tests=\"" + tests + "\" failures=\"" + failures
                        + "\" errors=\"" + errors + "\" skipped=\"" + skipped + "\">");
                for (Case testCase : cases.values()) {
                    out.print("  <testcase classname=\"" + escape(testCase.className) + "\" name=\""
                            + escape(testCase.name) + "\"");
                    if (testCase.status == null || "pass".equals(testCase.status)) {
                        out.println("/>");
                        continue;
                    }
                    out.println(">");
                    String element = "skipped".equals(testCase.status) ? "skipped"
                            : ("fail".equals(testCase.status) ? "failure" : "error");
                    out.print("    <" + element);
                    if (testCase.message != null) {
                        out.print(" message=\"" + escape(testCase.message) + "\"");
                    }
                    out.println(">");
                    if (testCase.trace != null) {
                        out.print(escape(testCase.trace));
                    }
                    out.println("    </" + element + ">");
                    out.println("  </testcase>");
                }
                for (Map.Entry<String, String> entry : classFailures.entrySet()) {
                    out.println("  <testcase classname=\"" + escape(entry.getKey()) + "\" name=\"classLoad\">");
                    out.println("    <error message=\"test class could not run\">" + escape(entry.getValue())
                            + "</error>");
                    out.println("  </testcase>");
                }
                out.println("</testsuite>");
            }
        }

        private static String escape(String value) {
            StringBuilder out = new StringBuilder();
            for (int i = 0; i < value.length(); i++) {
                char c = value.charAt(i);
                switch (c) {
                    case '&':
                        out.append("&amp;");
                        break;
                    case '<':
                        out.append("&lt;");
                        break;
                    case '>':
                        out.append("&gt;");
                        break;
                    case '"':
                        out.append("&quot;");
                        break;
                    default:
                        out.append(c);
                }
            }
            return out.toString();
        }
    }

    private static final class Case {
        final String className;
        final String name;
        String status;
        String message;
        String trace;

        Case(Description description) {
            className = description.getClassName();
            name = description.getMethodName() == null ? "class" : description.getMethodName();
        }
    }
}
