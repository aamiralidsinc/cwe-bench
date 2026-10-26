package org.apache.camel.htests;

import java.net.http.HttpResponse;

import org.apache.camel.CamelContext;
import org.apache.camel.builder.RouteBuilder;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/** Ordinary headers and parameters keep binding, and Camel's own headers keep being hidden outward. */
public class FuncHttpLegitTest {

    private CamelContext context;
    private int port;

    @Before
    public void setUp() throws Exception {
        port = Support.freePort();
        context = Support.newContext();
        context.addRoutes(new RouteBuilder() {
            @Override
            public void configure() {
                from("netty-http:http://127.0.0.1:" + port + "/hello")
                        .process(exchange -> {
                            String trace = exchange.getMessage().getHeader("X-Trace", String.class);
                            String lang = exchange.getMessage().getHeader("lang", String.class);
                            exchange.getMessage().setHeader("CamelBeanMethodName", "internal-value");
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
            throw new AssertionError("http: expected 200, got " + response.statusCode() + " / " + response.body());
        }
        if (!"trace=t-1;lang=en".equals(response.body())) {
            throw new AssertionError("http: ordinary header/parameter binding changed: " + response.body());
        }
    }

    @Test
    public void camelHeadersTheApplicationSetsDoNotLeakToTheResponse() throws Exception {
        HttpResponse<String> response = Support.get(port, "/hello?lang=en", "X-Trace", "t-1");
        if (response.headers().firstValue("CamelBeanMethodName").isPresent()) {
            throw new AssertionError("http: an internal header the route set leaked to the response");
        }
    }
}
