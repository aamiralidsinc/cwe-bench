/*
 * Security: a template name must not load a resource whose real suffix differs from the
 * configured one by smuggling a URL fragment or query past the suffix. Driven through the
 * real public entry point (the loader's sourceAt), with the Spring ResourceLoader stubbed
 * to answer with the concrete URL Spring would hand back.
 */
package com.github.jknack.handlebars.springmvc;

import java.io.File;
import java.net.URL;

import org.junit.jupiter.api.Test;
import org.springframework.core.io.ResourceLoader;

public class SecuritySpringSuffixBypassTest {

  private SpringTemplateLoader loader(final URL resolvedUrl) throws Exception {
    ResourceLoader rl = TestSupport.stubLoader(resolvedUrl);
    SpringTemplateLoader l = new SpringTemplateLoader(rl);
    l.setPrefix("classpath:/templates/");
    l.setSuffix(".hbs");
    return l;
  }

  @Test
  public void fragmentMustNotBypassSuffix() throws Exception {
    File secret = TestSupport.tempFile(".dat", TestSupport.OUT_OF_BOUNDS);
    URL smuggled = new URL("file:" + secret.getAbsolutePath() + "#.hbs");
    SpringTemplateLoader l = loader(smuggled);
    TestSupport.assertBlocked(() -> l.sourceAt("report#"));
  }

  @Test
  public void queryMustNotBypassSuffix() throws Exception {
    File secret = TestSupport.tempFile(".dat", TestSupport.OUT_OF_BOUNDS);
    URL smuggled = new URL("file:" + secret.getAbsolutePath() + "?.hbs");
    SpringTemplateLoader l = loader(smuggled);
    TestSupport.assertBlocked(() -> l.sourceAt("report?"));
  }
}
