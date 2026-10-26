package verifier.security;

import freemarker.cache.ClassTemplateLoader;
import freemarker.template.Configuration;
import freemarker.template.Template;

import java.io.IOException;
import java.io.StringWriter;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Locale;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.fail;

/**
 * A temporary template tree whose template root is {@code <base>/tpl}, plus marker files that live outside
 * that root but still inside the class path entry. The markers let a test tell "resolved a template inside the
 * template root" from "read a file from outside it" without touching anything real.
 */
final class Sandbox {

    static final String OUTSIDE_SECRET = "OUTSIDE-SECRET-3f9a1c";
    static final String OUTSIDE_ROOT_T = "OUTSIDE-ROOT-T-77c1b2";

    final Path base;
    final Path tpl;
    final URLClassLoader classPath;

    Sandbox() throws IOException {
        base = Files.createTempDirectory("fm-sandbox-");
        tpl = base.resolve("tpl");
        Files.createDirectories(tpl);

        write(tpl.resolve("t.ftl"), "INSIDE-BASE");
        write(tpl.resolve("t_en.ftl"), "INSIDE-EN");
        write(tpl.resolve("en/t.ftl"), "INSIDE-DIR-EN");
        write(tpl.resolve("en_US/t.ftl"), "INSIDE-DIR-EN-US");
        write(tpl.resolve("dark/t.ftl"), "INSIDE-DARK");
        write(tpl.resolve("main.ftl"), "<#setting locale=\"en_US_sub/../../secret\"><#include \"t.ftl\">");
        write(tpl.resolve("include.ftl"), "<#include \"t.ftl\">");

        write(base.resolve("secret.ftl"), OUTSIDE_SECRET);
        // Locale uppercases the country part, so a country-borne path lands on an upper-case file name.
        write(base.resolve("SECRET.ftl"), OUTSIDE_SECRET);
        write(base.resolve("t.ftl"), OUTSIDE_ROOT_T);

        classPath = new URLClassLoader(new URL[] { base.toUri().toURL() }, Sandbox.class.getClassLoader());
    }

    Configuration config() {
        Configuration cfg = new Configuration(Configuration.VERSION_2_3_32);
        cfg.setTemplateLoader(new ClassTemplateLoader((ClassLoader) classPath, "/tpl/"));
        cfg.setDefaultEncoding("UTF-8");
        cfg.setLocalizedLookup(true);
        cfg.setLocale(Locale.US);
        return cfg;
    }

    /** Performs the lookup and rendering, and fails when anything from outside the template root shows up. */
    void assertBlocked(Configuration cfg, String name, Locale locale, Object condition) {
        Template template;
        try {
            template = condition == null
                    ? cfg.getTemplate(name, locale)
                    : cfg.getTemplate(name, locale, condition, "UTF-8", true, false);
        } catch (IOException e) {
            return; // refusing the request is an acceptable outcome
        }

        StringWriter out = new StringWriter();
        try {
            template.process(new HashMap<String, Object>(), out);
        } catch (Exception e) {
            // A refusal may surface while processing (for example at an inclusion boundary); what
            // matters is that nothing from outside the root made it into the output.
            assertNoOutsideContent(out.toString());
            return;
        }
        assertNoOutsideContent(out.toString());
    }

    /** Renders the template returned for the configured default locale and checks the result. */
    void assertDefaultLocaleBlocked(Configuration cfg, String name) throws Exception {
        Template template;
        try {
            template = cfg.getTemplate(name);
        } catch (IOException e) {
            return;
        }
        StringWriter out = new StringWriter();
        template.process(new HashMap<String, Object>(), out);
        assertNoOutsideContent(out.toString());
    }

    static void assertNoOutsideContent(String rendered) {
        assertFalse("rendered a template from outside the template root: " + rendered,
                rendered.contains(OUTSIDE_SECRET));
        assertFalse("rendered a template from outside the template root: " + rendered,
                rendered.contains(OUTSIDE_ROOT_T));
    }

    static void write(Path path, String content) throws IOException {
        Path parent = path.getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        Files.write(path, content.getBytes(StandardCharsets.UTF_8));
    }

}
