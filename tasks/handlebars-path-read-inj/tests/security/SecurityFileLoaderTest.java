/*
 * Security: a file-system template name must not escape the configured base directory. Exercised
 * through the real public entry point (new Handlebars(loader).compile(...) -> loader.sourceAt).
 */
package com.github.jknack.handlebars.springmvc;

import java.io.File;

import org.junit.jupiter.api.Test;

import com.github.jknack.handlebars.io.FileTemplateLoader;

public class SecurityFileLoaderTest {

  @Test
  public void nameMustNotEscapeBaseDirectory() throws Exception {
    File base = TestSupport.tempDir("hb-base");
    File outside = TestSupport.tempDir("hb-outside");
    File secret = new File(outside, "secret.dat");
    java.nio.file.Files.write(secret.toPath(), TestSupport.OUT_OF_BOUNDS.getBytes());

    FileTemplateLoader loader = new FileTemplateLoader(base);
    TestSupport.assertBlocked(() -> loader.sourceAt("file:" + secret.getAbsolutePath() + "#"));
  }
}
