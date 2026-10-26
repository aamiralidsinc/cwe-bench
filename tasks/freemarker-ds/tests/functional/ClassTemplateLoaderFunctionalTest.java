package verifier.functional;

import freemarker.cache.ClassTemplateLoader;
import freemarker.template.Configuration;
import freemarker.template.Template;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.StringWriter;
import java.util.HashMap;

import static org.junit.Assert.assertEquals;

/** Ordinary schemeless class-path template names keep loading, including with a root base package. */
public class ClassTemplateLoaderFunctionalTest {

    private static FunctionalSandbox sandbox;

    @BeforeClass
    public static void setUp() throws Exception {
        sandbox = new FunctionalSandbox();
    }

    @AfterClass
    public static void tearDown() throws Exception {
        if (sandbox != null) {
            sandbox.classPath.close();
        }
    }

    @Test
    public void emptyBasePackageLoadsFromTheClassLoaderRoot() throws Exception {
        assertResolved(new ClassTemplateLoader((ClassLoader) sandbox.classPath, ""), "ok.ftl", "ROOT-OK");
    }

    @Test
    public void slashBasePackageLoadsFromTheClassLoaderRoot() throws Exception {
        assertResolved(new ClassTemplateLoader((ClassLoader) sandbox.classPath, "/"), "ok.ftl", "ROOT-OK");
    }

    @Test
    public void relativeBasePackageLoadsFromASubdirectory() throws Exception {
        assertResolved(new ClassTemplateLoader((ClassLoader) sandbox.classPath, "/tpl/"), "t.ftl", "BASE");
    }

    @Test
    public void nestedNameLoadsFromTheTemplateRoot() throws Exception {
        assertResolved(new ClassTemplateLoader((ClassLoader) sandbox.classPath, "/tpl/"), "dark/t.ftl", "DARK");
    }

    private static void assertResolved(ClassTemplateLoader loader, String name, String expected) throws Exception {
        Configuration cfg = new Configuration(Configuration.VERSION_2_3_32);
        cfg.setTemplateLoader(loader);
        cfg.setLocalizedLookup(false);
        cfg.setDefaultEncoding("UTF-8");
        Template template = cfg.getTemplate(name);
        StringWriter out = new StringWriter();
        template.process(new HashMap<String, Object>(), out);
        assertEquals(expected, out.toString());
    }

}
