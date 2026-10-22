/*
 * Functional: legitimate file-system templates, including nested ones under the base directory,
 * must keep loading.
 */
package com.github.jknack.handlebars.springmvc;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import java.io.File;
import java.nio.file.Files;

import org.junit.jupiter.api.Test;

import com.github.jknack.handlebars.io.FileTemplateLoader;
import com.github.jknack.handlebars.io.TemplateSource;

public class FunctionalFileLoaderTest {

  @Test
  public void nestedTemplateLoads() throws Exception {
    File base = TestSupport.tempDir("hb-base-ok");
    File sub = new File(base, "home");
    sub.mkdirs();
    Files.write(new File(sub, "index.hbs").toPath(), TestSupport.IN_BOUNDS.getBytes(UTF_8));

    FileTemplateLoader loader = new FileTemplateLoader(base);
    TemplateSource source = loader.sourceAt("home/index");

    assertNotNull(source);
    assertEquals(TestSupport.IN_BOUNDS, source.content(UTF_8));
  }
}
