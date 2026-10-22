/*
 * Security: a servlet-context template name must not escape the configured prefix. The servlet
 * container is stubbed to resolve whatever path it is handed (containers do not all normalise
 * '..'); a correct loader normalises and bounds the name before consulting the container.
 */
package com.github.jknack.handlebars.springmvc;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.io.File;

import org.junit.jupiter.api.Test;

import com.github.jknack.handlebars.io.ServletContextTemplateLoader;

import jakarta.servlet.ServletContext;

public class SecurityServletLoaderTest {

  @Test
  public void nameMustNotEscapePrefix() throws Exception {
    File secret = TestSupport.tempFile(".dat", TestSupport.OUT_OF_BOUNDS);
    ServletContext ctx = mock(ServletContext.class);
    // A permissive container: it returns the resource for any path it is asked for.
    lenient().when(ctx.getResource(anyString())).thenReturn(secret.toURI().toURL());

    ServletContextTemplateLoader loader =
        new ServletContextTemplateLoader(ctx, "/WEB-INF/views/", ".hbs");
    TestSupport.assertBlocked(() -> loader.sourceAt("../../../outside"));
  }
}
