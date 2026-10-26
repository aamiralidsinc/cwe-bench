package org.apache.camel.htests;

import java.net.http.HttpResponse;

import org.apache.camel.CamelContext;
import org.apache.camel.builder.RouteBuilder;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/** A REST route on the same component keeps binding its declared template and query values. */
public class FuncUndertowRestTest {

    private CamelContext context;
    private int port;

    @Before
    public void setUp() throws Exception {
        port = Support.freePort();
        context = Support.newContext();
        context.addRoutes(new RouteBuilder() {
            @Override
            public void configure() {
                restConfiguration().component("undertow").host("127.0.0.1").port(port);
                rest("/api/").get("greet/{name}").to("direct:greet");

                from("direct:greet").process(exchange -> {
                    String name = exchange.getMessage().getHeader("name", String.class);
                    String lang = exchange.getMessage().getHeader("lang", String.class);
                    exchange.getMessage().setBody("hi " + name + " " + lang);
                });
            }
        });
        context.start();
    }

    @After
    public void tearDown() {
        Support.close(context);
    }

    @Test
    public void declaredRestTemplateAndQueryValuesKeepBinding() throws Exception {
        HttpResponse<String> response = Support.get(port, "/api/greet/ducky?lang=en");
        if (response.statusCode() != 200) {
            throw new AssertionError("undertow rest: expected 200, got " + response.statusCode() + " / "
                    + response.body());
        }
        if (!"hi ducky en".equals(response.body())) {
            throw new AssertionError("undertow rest: declared template/query values stopped binding: " + response.body());
        }
    }
}
