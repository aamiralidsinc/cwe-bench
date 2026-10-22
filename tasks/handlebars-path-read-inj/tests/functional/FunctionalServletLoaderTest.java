/*
 * Functional: a legitimate, nested servlet-context template must keep loading.
 */
package com.github.jknack.handlebars.springmvc;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.io.File;

import org.junit.jupiter.api.Test;

import com.github.jknack.handlebars.io.ServletContextTemplateLoader;
import com.github.jknack.handlebars.io.TemplateSource;

import jakarta.servlet.ServletContext;

public class FunctionalServletLoaderTest {

  @Test
  public void nestedTemplateLoads() throws Exception {
    File ok = TestSupport.tempFile(".dat", TestSupport.IN_BOUNDS);
    ServletContext ctx = mock(ServletContext.class);
    when(ctx.getResource("/WEB-INF/views/home/index.hbs")).thenReturn(ok.toURI().toURL());

    ServletContextTemplateLoader loader =
        new ServletContextTemplateLoader(ctx, "/WEB-INF/views/", ".hbs");
    TemplateSource source = loader.sourceAt("home/index");

    assertNotNull(source);
    assertEquals(TestSupport.IN_BOUNDS, source.content(UTF_8));
  }
}
