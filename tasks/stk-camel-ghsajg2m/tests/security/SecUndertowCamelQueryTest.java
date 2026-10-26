package org.apache.camel.htests;

import java.net.http.HttpResponse;

import org.apache.camel.CamelContext;
import org.apache.camel.builder.RouteBuilder;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/**
 * A request parameter whose name carries one of Camel's own names must not reach the route as a
 * message header on a plain HTTP consumer.
 */
public class SecUndertowCamelQueryTest {

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
                            String value = exchange.getMessage().getHeader("CamelBeanMethodName", String.class);
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
    public void camelNamedParameterFromTheRequestDoesNotBecomeAMessageHeader() throws Exception {
        HttpResponse<String> response = Support.get(port, "/hello?CamelBeanMethodName=evil");
        Support.assertProcessedNormally("http", response);
    }
}
