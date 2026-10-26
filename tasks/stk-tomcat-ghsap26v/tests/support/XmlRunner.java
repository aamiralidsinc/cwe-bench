package htests;

import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.ArrayList;
import java.util.List;

import org.junit.runner.Description;
import org.junit.runner.JUnitCore;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;
import org.junit.runner.notification.RunListener;

/** Run JUnit classes and write one JUnit XML file; used for both hidden groups. */
public class XmlRunner {

    private static String esc(String s) {
        if (s == null) return "";
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '&': b.append("&amp;"); break;
                case '<': b.append("&lt;"); break;
                case '>': b.append("&gt;"); break;
                case '"': b.append("&quot;"); break;
                case '\'': b.append("&apos;"); break;
                default:
                    if (c < 0x20 && c != '\n' && c != '\r' && c != '\t') b.append(' ');
                    else b.append(c);
            }
        }
        return b.toString();
    }

    private static final class Case {
        String name;
        String trace;
        boolean failed;
        boolean skipped;
    }

    private static final class Recorder extends RunListener {
        final List<Case> cases = new ArrayList<Case>();
        final List<Failure> current = new ArrayList<Failure>();

        @Override
        public void testStarted(Description d) {
            Case c = new Case();
            c.name = d.getMethodName() == null ? d.getDisplayName() : d.getMethodName();
            cases.add(c);
            current.clear();
        }

        @Override
        public void testFailure(Failure f) {
            current.add(f);
        }

        @Override
        public void testAssumptionFailure(Failure f) {
            if (!cases.isEmpty()) cases.get(cases.size() - 1).skipped = true;
        }

        @Override
        public void testIgnored(Description d) {
            Case c = new Case();
            c.name = d.getMethodName() == null ? d.getDisplayName() : d.getMethodName();
            c.skipped = true;
            cases.add(c);
        }

        @Override
        public void testFinished(Description d) {
            if (cases.isEmpty()) return;
            Case c = cases.get(cases.size() - 1);
            if (!current.isEmpty()) {
                c.failed = true;
                Failure f = current.get(0);
                StringWriter sw = new StringWriter();
                f.getException().printStackTrace(new PrintWriter(sw));
                c.trace = (f.getMessage() == null ? "" : f.getMessage()) + "\n" + sw.toString();
            }
        }
    }

    private static void appendSuite(StringBuilder sb, String name, List<Case> cases) {
        int failures = 0;
        int skipped = 0;
        for (Case c : cases) {
            if (c.failed) failures++;
            else if (c.skipped) skipped++;
        }
        sb.append("  <testsuite name=\"").append(esc(name)).append("\" tests=\"").append(cases.size())
          .append("\" failures=\"").append(failures).append("\" errors=\"0\" skipped=\"").append(skipped).append("\">\n");
        for (Case c : cases) {
            sb.append("    <testcase classname=\"").append(esc(name)).append("\" name=\"").append(esc(c.name)).append("\"");
            if (c.failed) {
                String trace = c.trace == null ? "" : c.trace;
                String first = trace.split("\n", 2)[0];
                sb.append(">\n      <failure message=\"").append(esc(first)).append("\">")
                  .append(esc(trace)).append("</failure>\n    </testcase>\n");
            } else if (c.skipped) {
                sb.append(">\n      <skipped/>\n    </testcase>\n");
            } else {
                sb.append("/>\n");
            }
        }
        sb.append("  </testsuite>\n");
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("usage: XmlRunner <out.xml> <class>...");
            System.exit(2);
        }
        StringBuilder sb = new StringBuilder();
        sb.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<testsuites>\n");
        for (int i = 1; i < args.length; i++) {
            String cn = args[i];
            List<Case> cases = new ArrayList<Case>();
            try {
                Class<?> c = Class.forName(cn);
                Recorder rec = new Recorder();
                JUnitCore core = new JUnitCore();
                core.addListener(rec);
                Result r = core.run(c);
                cases.addAll(rec.cases);
                if (cases.isEmpty()) {
                    for (Failure f : r.getFailures()) {
                        Case k = new Case();
                        k.name = f.getDescription() == null ? "initializationError" : f.getDescription().getDisplayName();
                        k.failed = true;
                        StringWriter sw = new StringWriter();
                        f.getException().printStackTrace(new PrintWriter(sw));
                        k.trace = f.getMessage() + "\n" + sw.toString();
                        cases.add(k);
                    }
                    if (cases.isEmpty()) {
                        Case k = new Case();
                        k.name = "noTests";
                        k.failed = true;
                        k.trace = "no tests were run";
                        cases.add(k);
                    }
                }
            } catch (Throwable t) {
                Case k = new Case();
                k.name = "initializationError";
                k.failed = true;
                StringWriter sw = new StringWriter();
                t.printStackTrace(new PrintWriter(sw));
                k.trace = String.valueOf(t) + "\n" + sw.toString();
                cases.add(k);
            }
            appendSuite(sb, cn, cases);
        }
        sb.append("</testsuites>\n");
        PrintWriter w = new PrintWriter(new OutputStreamWriter(new FileOutputStream(args[0]), "UTF-8"));
        w.print(sb.toString());
        w.close();
        int failed = 0;
        for (int i = 0; i < sb.length(); i++) if (sb.charAt(i) == '<') failed += 0; // no-op
        System.out.println("wrote " + args[0]);
        System.exit(0);
    }
}
