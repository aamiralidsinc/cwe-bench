/*
 * Functional: legitimate Spring template resolution must keep working, including nested view
 * names and protocol-qualified configured prefixes (classpath: / file:). A fix that rejects ':'
 * or '/' anywhere in the resolved location would break these.
 */
package com.github.jknack.handlebars.springmvc;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import java.io.File;

import org.junit.jupiter.api.Test;
import org.springframework.core.io.ResourceLoader;

import com.github.jknack.handlebars.io.TemplateSource;

public class FunctionalSpringResolutionTest {

  private void resolvesNested(final String prefix) throws Exception {
    File ok = TestSupport.tempFile(".hbs", TestSupport.IN_BOUNDS);
    ResourceLoader rl = TestSupport.stubLoader(ok.toURI().toURL());
    SpringTemplateLoader l = new SpringTemplateLoader(rl);
    l.setPrefix(prefix);
    l.setSuffix(".hbs");

    TemplateSource source = l.sourceAt("home/index");
    assertNotNull(source, "a legitimate nested template must resolve for prefix " + prefix);
    assertEquals(TestSupport.IN_BOUNDS, source.content(UTF_8));
  }

  @Test
  public void classpathPrefixResolvesNestedName() throws Exception {
    resolvesNested("classpath:/templates/");
  }

  @Test
  public void filePrefixResolvesNestedName() throws Exception {
    resolvesNested("file:/opt/templates/");
  }
}
