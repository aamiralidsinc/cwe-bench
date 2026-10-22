/*
 * Functional: the project's own template-loader behaviour for the affected area. A real Spring
 * resource loader resolves an existing classpath template; a missing name fails as before.
 */
package com.github.jknack.handlebars.springmvc;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;

import org.junit.jupiter.api.Test;
import org.springframework.core.io.DefaultResourceLoader;

import com.github.jknack.handlebars.io.TemplateSource;

public class FunctionalProjectSpringTest {

  @Test
  public void sourceAt() throws IOException {
    SpringTemplateLoader loader = new SpringTemplateLoader(new DefaultResourceLoader());

    TemplateSource source = loader.sourceAt("template");

    assertNotNull(source);
  }

  @Test
  public void fileNotFound() {
    assertThrows(
        IOException.class,
        () -> new SpringTemplateLoader(new DefaultResourceLoader()).sourceAt("missingFile"));
  }
}
