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
 * A value the application itself sets under one of Camel's own header names keeps its documented
 * effect on the reply.
 */
public class FuncCoapResponseControlTest {

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
                            exchange.getMessage().setHeader("CamelCoapMaxAge", 42L);
                            exchange.getMessage().setHeader("CamelCoapETag", new byte[] { 1, 2, 3, 4 });
                            exchange.getMessage().setBody("ok");
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
    public void applicationSetResponseControlKeepsWorking() throws Exception {
        CoapClient client = new CoapClient("coap://127.0.0.1:" + port + "/params");
        client.setTimeout(30000L);
        try {
            CoapResponse response = client.get();
            if (response == null) {
                throw new AssertionError("coap: no response");
            }
            if (!"ok".equals(response.getResponseText())) {
                throw new AssertionError("coap: body changed: " + response.getResponseText());
            }
            Long maxAge = response.getOptions().getMaxAge();
            if (maxAge == null || maxAge != 42L) {
                throw new AssertionError("coap: the application's max-age no longer drives the reply: " + maxAge);
            }
            java.util.List<byte[]> etags = response.getOptions().getETags();
            if (etags == null || etags.isEmpty() || etags.get(0).length != 4) {
                throw new AssertionError("coap: the application's etag no longer drives the reply");
            }
        } finally {
            client.shutdown();
        }
    }
}
