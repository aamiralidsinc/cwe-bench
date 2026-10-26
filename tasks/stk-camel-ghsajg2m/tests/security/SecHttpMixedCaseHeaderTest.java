package org.apache.camel.htests;

import java.net.http.HttpResponse;

import org.apache.camel.CamelContext;
import org.apache.camel.builder.RouteBuilder;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/**
 * A client that spells one of Camel's own header names with different capitalization must not get
 * that header into the route.
 */
public class SecHttpMixedCaseHeaderTest {

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
                            String value = exchange.getMessage().getHeader("CamelHttpResponseCode", String.class);
                            exchange.getMessage().setBody(value == null ? "clean" : Support.MARKER + value);
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
    public void caseVariantOfACamelHeaderDoesNotBecomeAMessageHeader() throws Exception {
        HttpResponse<String> response = Support.get(port, "/hello", "caMElHttpResponseCode", "503");
        Support.assertProcessedNormally("http", response);
    }

    @Test
    public void upperCaseVariantOfACamelHeaderDoesNotBecomeAMessageHeader() throws Exception {
        HttpResponse<String> response = Support.get(port, "/hello", "CAMELHTTPRESPONSECODE", "503");
        Support.assertProcessedNormally("http", response);
    }
}
