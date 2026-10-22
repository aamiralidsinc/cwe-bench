/*
 * Shared helpers for the hidden behavioural tests. Not a test class itself
 * (no @Test methods), so it contributes no results; it only builds stub
 * collaborators and expresses the "attack is blocked" oracle.
 */
package com.github.jknack.handlebars.springmvc;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.io.File;
import java.net.URL;
import java.nio.file.Files;

import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;

import com.github.jknack.handlebars.io.TemplateSource;

final class TestSupport {

  private TestSupport() {}

  /** A marker a test writes into a resource that lives OUTSIDE the configured bounds. */
  static final String OUT_OF_BOUNDS = "OUT-OF-BOUNDS-MARKER";

  /** A marker a test writes into a legitimate, in-bounds resource. */
  static final String IN_BOUNDS = "IN-BOUNDS-OK";

  /**
   * Write {@code content} to a fresh temp file with the given extension and return it.
   */
  static File tempFile(final String extension, final String content) throws Exception {
    File f = File.createTempFile("hb-test", extension);
    Files.write(f.toPath(), content.getBytes(UTF_8));
    f.deleteOnExit();
    return f;
  }

  /** A fresh temp directory. */
  static File tempDir(final String name) throws Exception {
    File d = Files.createTempDirectory(name).toFile();
    d.deleteOnExit();
    return d;
  }

  /**
   * A Spring {@link ResourceLoader} that, for any requested location, answers with an existing
   * resource whose URL is {@code url}. Models the Spring infrastructure answering with a concrete
   * (possibly attacker-shaped) URL for whatever location the loader asks for.
   */
  static ResourceLoader stubLoader(final URL url) throws Exception {
    ResourceLoader rl = mock(ResourceLoader.class);
    Resource res = mock(Resource.class);
    when(res.exists()).thenReturn(true);
    when(res.getURL()).thenReturn(url);
    when(rl.getResource(anyString())).thenReturn(res);
    return rl;
  }

  @FunctionalInterface
  interface Load {
    TemplateSource get() throws Exception;
  }

  /**
   * Assert an out-of-bounds load is blocked: it must either be refused with an error, or (if it
   * returns at all) must not have read the out-of-bounds marker. No single status/exception type
   * is required.
   */
  static void assertBlocked(final Load load) {
    TemplateSource source;
    try {
      source = load.get();
    } catch (Throwable refused) {
      return; // refused with a client error -> blocked, no side effect
    }
    if (source == null) {
      return; // nothing resolved -> blocked
    }
    String content;
    try {
      content = source.content(UTF_8);
    } catch (Throwable refused) {
      return; // could not read -> no side effect
    }
    assertFalse(
        content.contains(OUT_OF_BOUNDS),
        "An out-of-bounds resource was read through a template name: " + content);
  }
}
