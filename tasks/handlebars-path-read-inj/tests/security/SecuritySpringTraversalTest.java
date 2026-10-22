/*
 * Security: a template name must not escape the configured prefix via relative traversal.
 * The stub resource loader would happily return an out-of-bounds resource; a correct loader
 * refuses the name before ever asking for it.
 */
package com.github.jknack.handlebars.springmvc;

import java.io.File;

import org.junit.jupiter.api.Test;
import org.springframework.core.io.ResourceLoader;

public class SecuritySpringTraversalTest {

  @Test
  public void relativeTraversalMustNotEscapePrefix() throws Exception {
    File secret = TestSupport.tempFile(".dat", TestSupport.OUT_OF_BOUNDS);
    ResourceLoader rl = TestSupport.stubLoader(secret.toURI().toURL());
    SpringTemplateLoader l = new SpringTemplateLoader(rl);
    l.setPrefix("classpath:/templates/");
    l.setSuffix(".hbs");
    TestSupport.assertBlocked(() -> l.sourceAt("../../outside"));
  }
}
