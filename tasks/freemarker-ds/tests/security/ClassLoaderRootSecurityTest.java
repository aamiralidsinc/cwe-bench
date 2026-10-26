package verifier.security;

import freemarker.cache.ClassTemplateLoader;
import freemarker.template.Configuration;
import freemarker.template.Template;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.IOException;
import java.io.StringWriter;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.util.HashMap;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.fail;

/**
 * When the class-path template root is the root of the class loader (the base package is empty), a name written as
 * an absolute URL must not be resolved as one. The class loader below resolves URL-shaped resource names the way the
 * class loader the product guards against does; the guard is meant to keep such a name from reaching it at all.
 */
public class ClassLoaderRootSecurityTest {

    private static Sandbox sandbox;

    @BeforeClass
    public static void setUp() throws Exception {
        sandbox = new Sandbox();
    }

    @AfterClass
    public static void tearDown() throws Exception {
        if (sandbox != null) {
            sandbox.classPath.close();
        }
    }

    @Test
    public void absoluteUrlNameWithEmptyBasePackage() throws Exception {
        assertBlocked("");
    }

    @Test
    public void absoluteUrlNameWithRootBasePackage() throws Exception {
        assertBlocked("/");
    }

    private void assertBlocked(String basePackagePath) throws Exception {
        Configuration cfg = new Configuration(Configuration.VERSION_2_3_32);
        cfg.setTemplateLoader(new ClassTemplateLoader(new SchemeResolvingClassLoader(sandbox.base.toUri().toURL()),
                basePackagePath));
        cfg.setLocalizedLookup(false);
        cfg.setDefaultEncoding("UTF-8");
        cfg.setLocale(java.util.Locale.US);

        String secretName = sandbox.base.resolve("secret.ftl").toUri().toURL().toString();
        Template template;
        try {
            template = cfg.getTemplate(secretName);
        } catch (IOException e) {
            return;
        }

        StringWriter out = new StringWriter();
        try {
            template.process(new HashMap<String, Object>(), out);
        } catch (Exception e) {
            assertFalse("rendered a template addressed by an absolute URL: " + out,
                    out.toString().contains(Sandbox.OUTSIDE_SECRET));
            return;
        }
        assertFalse("rendered a template addressed by an absolute URL: " + out,
                out.toString().contains(Sandbox.OUTSIDE_SECRET));
    }

    /** Resolves URL-shaped names as URLs, like the class loader implementation the product guards against. */
    private static final class SchemeResolvingClassLoader extends ClassLoader {

        private final URLClassLoader delegate;

        SchemeResolvingClassLoader(URL root) {
            super(ClassLoaderRootSecurityTest.class.getClassLoader());
            delegate = new URLClassLoader(new URL[] { root }, getParent());
        }

        @Override
        public URL getResource(String name) {
            if (name.matches("[a-zA-Z][a-zA-Z0-9+.-]*:.*")) {
                try {
                    return new URL(name);
                } catch (IOException e) {
                    return null;
                }
            }
            return delegate.getResource(name);
        }

        @Override
        public java.io.InputStream getResourceAsStream(String name) {
            URL url = getResource(name);
            if (url == null) {
                return null;
            }
            try {
                return url.openStream();
            } catch (IOException e) {
                return null;
            }
        }

    }

}
