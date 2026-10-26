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
 * The same transport, the form of an option that carries no value: the name alone must not become a
 * message header either.
 */
public class SecCoapValuelessQueryTest {

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
                            String value = exchange.getMessage().getHeader("CamelBeanMethodName", String.class);
                            exchange.getMessage().setBody(value == null ? "clean" : Support.MARKER);
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
    public void valuelessCamelNamedOptionDoesNotBecomeAMessageHeader() throws Exception {
        CoapClient client = new CoapClient("coap://127.0.0.1:" + port + "/params?CamelBeanMethodName");
        client.setTimeout(30000L);
        try {
            CoapResponse response = client.get();
            if (response == null) {
                throw new AssertionError("coap: no response");
            }
            Support.assertNotInjected("coap", response.getResponseText());
        } finally {
            client.shutdown();
        }
    }
}
