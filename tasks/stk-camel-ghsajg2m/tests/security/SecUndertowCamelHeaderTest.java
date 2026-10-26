package org.apache.camel.htests;

import java.net.http.HttpResponse;

import org.apache.camel.CamelContext;
import org.apache.camel.builder.RouteBuilder;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/**
 * A request header that carries one of Camel's own names, spelled exactly as Camel spells it, must
 * not reach the route on a plain HTTP consumer.
 */
public class SecUndertowCamelHeaderTest {

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
    public void camelHeaderFromTheRequestDoesNotBecomeAMessageHeader() throws Exception {
        HttpResponse<String> response = Support.get(port, "/hello", "CamelHttpResponseCode", "503");
        Support.assertProcessedNormally("http", response);
    }
}
