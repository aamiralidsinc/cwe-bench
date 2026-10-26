package org.apache.camel.htests;

import java.net.http.HttpResponse;

import org.apache.camel.CamelContext;
import org.apache.camel.builder.RouteBuilder;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/** The plain consumer keeps binding ordinary headers and parameters. */
public class FuncUndertowBindingTest {

    private CamelContext context;
    private int port;

    @Before
    public void setUp() throws Exception {
        port = Support.freePort();
        context = Support.newContext();
        context.addRoutes(new RouteBuilder() {
            @Override
            public void configure() {
                from("undertow:http://127.0.0.1:" + port + "/hello")
                        .process(exchange -> {
                            String trace = exchange.getMessage().getHeader("X-Trace", String.class);
                            String lang = exchange.getMessage().getHeader("lang", String.class);
                            exchange.getMessage().setBody("trace=" + trace + ";lang=" + lang);
                        });
            }
        });
        context.start();
        Support.awaitPort(port, 20000);
    }

    @After
    public void tearDown() {
        Support.close(context);
    }

    @Test
    public void ordinaryHeadersAndParametersKeepBinding() throws Exception {
        HttpResponse<String> response = Support.get(port, "/hello?lang=en", "X-Trace", "t-1");
        if (response.statusCode() != 200) {
            throw new AssertionError("undertow: expected 200, got " + response.statusCode() + " / " + response.body());
        }
        if (!"trace=t-1;lang=en".equals(response.body())) {
            throw new AssertionError("undertow: ordinary header/parameter binding changed: " + response.body());
        }
    }
}
