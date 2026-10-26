package bench.bcj;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.security.Security;
import java.util.ArrayList;
import java.util.List;

import org.bouncycastle.jce.provider.BouncyCastleProvider;

/**
 * Runs the project's own name-constraint tests and writes their results as JUnit XML.
 * The two classes use different bases (the project's SimpleTest and JUnit's TestCase), so both
 * shapes are driven directly instead of through a test framework.
 */
public final class ProjectSuite
{
    public static void main(String[] args)
        throws Exception
    {
        if (Security.getProvider("BC") == null)
        {
            Security.addProvider(new BouncyCastleProvider());
        }
        StringBuilder cases = new StringBuilder();
        int tests = 0;
        int failures = 0;

        String simple = "org.bouncycastle.jce.provider.test.PKIXNameConstraintsTest";
        tests++;
        try
        {
            Class<?> type = Class.forName(simple);
            Object instance = type.getDeclaredConstructor().newInstance();
            type.getMethod("performTest").invoke(instance);
            cases.append(pass(simple, "performTest"));
        }
        catch (InvocationTargetException e)
        {
            failures++;
            cases.append(fail(simple, "performTest", e.getCause() == null ? e : e.getCause()));
        }
        catch (Throwable t)
        {
            failures++;
            cases.append(fail(simple, "performTest", t));
        }

        String junit = "org.bouncycastle.jce.provider.MultiValuedRDNEmailTest";
        try
        {
            Class<?> type = Class.forName(junit);
            List<Method> ordered = new ArrayList<Method>();
            for (Method method : type.getMethods())
            {
                if (method.getName().startsWith("test") && method.getParameterCount() == 0)
                {
                    ordered.add(method);
                }
            }
            ordered.sort((a, b) -> a.getName().compareTo(b.getName()));
            for (Method method : ordered)
            {
                tests++;
                try
                {
                    Object instance = type.getDeclaredConstructor().newInstance();
                    type.getMethod("setUp").invoke(instance);
                    method.invoke(instance);
                    cases.append(pass(junit, method.getName()));
                }
                catch (InvocationTargetException e)
                {
                    failures++;
                    cases.append(fail(junit, method.getName(), e.getCause() == null ? e : e.getCause()));
                }
                catch (Throwable t)
                {
                    failures++;
                    cases.append(fail(junit, method.getName(), t));
                }
            }
        }
        catch (Throwable t)
        {
            tests++;
            failures++;
            cases.append(fail(junit, "<load>", t));
        }

        StringBuilder xml = new StringBuilder();
        xml.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        xml.append("<testsuite name=\"project\" tests=\"").append(tests).append("\" failures=\"").append(failures)
            .append("\" errors=\"0\" skipped=\"0\">\n");
        xml.append(cases);
        xml.append("</testsuite>\n");
        try (Writer writer = new OutputStreamWriter(new FileOutputStream(new File(args[0])), StandardCharsets.UTF_8))
        {
            writer.write(xml.toString());
        }
        System.out.println("ran " + tests + " project tests, failures: " + failures);
        if (failures != 0)
        {
            System.out.println(xml);
        }
    }

    private static String pass(String className, String name)
    {
        return " <testcase classname=\"" + escape(className) + "\" name=\"" + escape(name) + "\"/>\n";
    }

    private static String fail(String className, String name, Throwable t)
    {
        String message = t.getClass().getName() + ": " + t.getMessage();
        return " <testcase classname=\"" + escape(className) + "\" name=\"" + escape(name) + "\">\n"
            + "  <failure message=\"" + escape(message) + "\">" + escape(String.valueOf(t)) + "</failure>\n"
            + " </testcase>\n";
    }

    private static String escape(String value)
    {
        return String.valueOf(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("\"", "&quot;");
    }
}
