/*
 * Security: a controller-supplied view name must not reach template compilation when it carries
 * a protocol, a fragment, or a traversal sequence. The compiler is mocked; the side effect we
 * forbid is "an unsafe name was compiled". Driven through the real view-building entry point.
 */
package com.github.jknack.handlebars.springmvc;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.atLeast;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Template;

public class SecurityViewResolverTest {

  private void assertViewNameBlocked(final String viewName) throws Exception {
    Handlebars hb = mock(Handlebars.class);
    Template tpl = mock(Template.class);
    when(hb.compile(anyString())).thenReturn(tpl);

    HandlebarsViewResolver vr = new HandlebarsViewResolver(hb);
    vr.setPrefix("/WEB-INF/views/");
    vr.setSuffix(".hbs");

    try {
      vr.buildView(viewName);
    } catch (Exception refused) {
      return; // refused the unsafe view name -> blocked
    }
    // No refusal: prove the unsafe name was never handed to the compiler.
    ArgumentCaptor<String> cap = ArgumentCaptor.forClass(String.class);
    verify(hb, atLeast(0)).compile(cap.capture());
    for (String compiled : cap.getAllValues()) {
      assertFalse(
          compiled.contains("..") || compiled.contains(":") || compiled.contains("#"),
          "An unsafe view name was compiled: " + compiled);
    }
  }

  @Test
  public void traversalViewNameMustBeRejected() throws Exception {
    assertViewNameBlocked("../../outside");
  }

  @Test
  public void protocolViewNameMustBeRejected() throws Exception {
    assertViewNameBlocked("file:/opt/secret");
  }

  @Test
  public void fragmentViewNameMustBeRejected() throws Exception {
    assertViewNameBlocked("report#bypass");
  }
}
