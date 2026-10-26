package org.apache.camel.htests;

import org.apache.camel.CamelContext;
import org.apache.camel.builder.RouteBuilder;
import org.eclipse.californium.core.CoapClient;
import org.eclipse.californium.core.CoapResponse;
import org.eclipse.californium.elements.config.Configuration;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/**
 * A client-supplied name that Camel's own response handling reads must not change the reply the
 * client gets.
 */
public class SecCoapMaxAgeTest {

    private CamelContext context;
    private int port;

    @Before
    public void setUp() throws Exception {
        Configuration.createStandardWithoutFile();
        port = Support.freePort();
        context = Support.newContext();
        context.addRoutes(new RouteBuilder() {
            @Override
            public void configure() {
                from("coap://127.0.0.1:" + port + "/params")
                        .process(exchange -> {
                            String injected = exchange.getMessage().getHeader("CamelCoapMaxAge", String.class);
                            exchange.getMessage().setBody(injected == null ? "clean" : Support.MARKER);
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
    public void clientSuppliedCachingValueDoesNotDriveTheReply() throws Exception {
        CoapClient client = new CoapClient("coap://127.0.0.1:" + port + "/params?CamelCoapMaxAge=99");
        client.setTimeout(30000L);
        try {
            CoapResponse response = client.get();
            if (response == null) {
                throw new AssertionError("coap: no response");
            }
            Support.assertNotInjected("coap", response.getResponseText());
            Long maxAge = response.getOptions().getMaxAge();
            if (maxAge != null && maxAge == 99L) {
                throw new AssertionError("coap: the client's query option drove the reply's max-age: " + maxAge);
            }
        } finally {
            client.shutdown();
        }
    }
}
