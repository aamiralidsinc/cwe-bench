package org.apache.camel.htests;

import org.apache.camel.CamelContext;
import org.apache.camel.builder.RouteBuilder;
import org.eclipse.californium.core.CoapClient;
import org.eclipse.californium.core.CoapResponse;
import org.eclipse.californium.elements.config.Configuration;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/** Request parameters without Camel's prefix keep binding to message headers. */
public class FuncCoapQueryMappingTest {

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
                            String id = exchange.getMessage().getHeader("id", String.class);
                            exchange.getMessage().setBody("Hello " + id);
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
    public void ordinaryRequestParameterKeepsBinding() throws Exception {
        CoapClient client = new CoapClient("coap://127.0.0.1:" + port + "/params?id=Ducky");
        client.setTimeout(30000L);
        try {
            CoapResponse response = client.get();
            if (response == null) {
                throw new AssertionError("coap: no response");
            }
            if (!"Hello Ducky".equals(response.getResponseText())) {
                throw new AssertionError("coap: ordinary parameter binding changed: " + response.getResponseText());
            }
        } finally {
            client.shutdown();
        }
    }
}
