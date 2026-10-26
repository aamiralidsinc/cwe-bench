package bench.bcj;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/**
 * Minimal reflection runner: every public no-argument method whose name starts with "test" is a
 * test case. Results are written as JUnit XML so the task's scorer can read them. No external
 * test framework is needed, and a test class that cannot be loaded is reported as a failure.
 */
public final class XmlRunner
{
    public static void main(String[] args)
        throws Exception
    {
        File out = new File(args[0]);
        StringBuilder xml = new StringBuilder();
        xml.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        xml.append("<testsuite name=\"bench\" tests=\"0\" failures=\"0\" errors=\"0\" skipped=\"0\">\n");
        int tests = 0;
        int failures = 0;
        for (int i = 1; i < args.length; i++)
        {
            String className = args[i];
            Class<?> type;
            try
            {
                type = Class.forName(className);
            }
            catch (Throwable t)
            {
                xml.append(caseXml(className, "<init>", t));
                tests++;
                failures++;
                continue;
            }
            List<Method> methods = new ArrayList<Method>();
            for (Method method : type.getMethods())
            {
                if (method.getName().startsWith("test") && method.getParameterCount() == 0)
                {
                    methods.add(method);
                }
            }
            methods.sort((a, b) -> a.getName().compareTo(b.getName()));
            if (methods.isEmpty())
            {
                xml.append(caseXml(className, "<init>", new AssertionError("no test methods found")));
                tests++;
                failures++;
            }
            for (Method method : methods)
            {
                tests++;
                try
                {
                    Object instance = type.getDeclaredConstructor().newInstance();
                    method.invoke(instance);
                    xml.append(" <testcase classname=\"").append(escape(className)).append("\" name=\"")
                        .append(escape(method.getName())).append("\"/>\n");
                }
                catch (InvocationTargetException e)
                {
                    failures++;
                    xml.append(caseXml(className, method.getName(), e.getCause() == null ? e : e.getCause()));
                }
                catch (Throwable t)
                {
                    failures++;
                    xml.append(caseXml(className, method.getName(), t));
                }
            }
        }
        xml.append("</testsuite>\n");
        String text = xml.toString().replace("tests=\"0\"", "tests=\"" + tests + "\"")
            .replace("failures=\"0\"", "failures=\"" + failures + "\"");
        try (Writer writer = new OutputStreamWriter(new FileOutputStream(out), StandardCharsets.UTF_8))
        {
            writer.write(text);
        }
        System.out.println("ran " + tests + " tests, failures: " + failures);
        if (failures != 0)
        {
            System.out.println(text);
        }
    }

    private static String caseXml(String className, String name, Throwable t)
    {
        String message = t.getClass().getName() + ": " + t.getMessage();
        return " <testcase classname=\"" + escape(className) + "\" name=\"" + escape(name) + "\">\n"
            + "  <failure message=\"" + escape(message) + "\">" + escape(stack(t)) + "</failure>\n"
            + " </testcase>\n";
    }

    private static String stack(Throwable t)
    {
        StringBuilder sb = new StringBuilder(String.valueOf(t));
        StackTraceElement[] trace = t.getStackTrace();
        for (int i = 0; i < trace.length && i < 12; i++)
        {
            sb.append("\n  at ").append(trace[i]);
        }
        return sb.toString();
    }

    private static String escape(String value)
    {
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;");
    }
}
