package verifier.functional;

import freemarker.cache.ClassTemplateLoader;
import freemarker.template.Configuration;

import java.io.IOException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** A temporary template tree used by the functional checks. */
final class FunctionalSandbox {

    final Path base;
    final Path tpl;
    final URLClassLoader classPath;

    FunctionalSandbox() throws IOException {
        base = Files.createTempDirectory("fm-func-");
        tpl = base.resolve("tpl");
        Files.createDirectories(tpl);

        write(tpl.resolve("t.ftl"), "BASE");
        write(tpl.resolve("t_en.ftl"), "EN");
        write(tpl.resolve("t_en_US.ftl"), "EN-US");
        write(tpl.resolve("t_en_US_VAR.ftl"), "EN-US-VAR");
        write(tpl.resolve("t_en_US_#Latn.ftl"), "EN-US-LATN");
        write(tpl.resolve("en/t.ftl"), "DIR-EN");
        write(tpl.resolve("en_US/t.ftl"), "DIR-EN-US");
        write(tpl.resolve("dark/t.ftl"), "DARK");
        write(tpl.resolve("dark/i.ftl"), "DARK-I");
        write(tpl.resolve("i.ftl"), "I");
        write(tpl.resolve("main.ftl"), "<#include \"i.ftl\">");
        write(base.resolve("ok.ftl"), "ROOT-OK");

        classPath = new URLClassLoader(new URL[] { base.toUri().toURL() }, FunctionalSandbox.class.getClassLoader());
    }

    Configuration config(String basePackagePath) {
        Configuration cfg = new Configuration(Configuration.VERSION_2_3_32);
        cfg.setTemplateLoader(new ClassTemplateLoader((ClassLoader) classPath, basePackagePath));
        cfg.setDefaultEncoding("UTF-8");
        cfg.setLocalizedLookup(true);
        cfg.setLocale(java.util.Locale.US);
        return cfg;
    }

    static void write(Path path, String content) throws IOException {
        Path parent = path.getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        Files.write(path, content.getBytes(StandardCharsets.UTF_8));
    }

}
