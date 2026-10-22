/*
 * Functional: a legitimate, nested controller view name must still compile unchanged.
 */
package com.github.jknack.handlebars.springmvc;

import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;

import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Template;

public class FunctionalViewResolverTest {

  @Test
  public void nestedViewNameCompiles() throws Exception {
    Handlebars hb = mock(Handlebars.class);
    Template tpl = mock(Template.class);
    when(hb.compile("home/index")).thenReturn(tpl);

    HandlebarsViewResolver vr = new HandlebarsViewResolver(hb);
    vr.setPrefix("/WEB-INF/views/");
    vr.setSuffix(".hbs");

    vr.buildView("home/index");

    verify(hb, times(1)).compile(eq("home/index"));
  }
}
