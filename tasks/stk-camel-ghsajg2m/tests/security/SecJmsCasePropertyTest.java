package org.apache.camel.htests;

import java.util.Map;

import org.apache.camel.CamelContext;
import org.apache.camel.Exchange;
import org.apache.camel.component.jms.JmsBinding;
import org.apache.camel.support.DefaultExchange;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/**
 * A message that arrives from a broker with a property spelled like one of Camel's own header names,
 * in a different capitalization, must not deliver that header.
 */
public class SecJmsCasePropertyTest {

    private CamelContext context;

    @Before
    public void setUp() {
        context = Support.newContext();
    }

    @After
    public void tearDown() {
        Support.close(context);
    }

    @Test
    public void caseVariantOfACamelPropertyDoesNotBecomeAMessageHeader() throws Exception {
        JmsBinding binding = new JmsBinding();
        Exchange exchange = new DefaultExchange(context);
        FakeJmsMessage message = new FakeJmsMessage()
                .put("cAmelHttpResponseCode", "503")
                .put("CamelBeanMethodName", "evil");
        Map<String, Object> headers = binding.extractHeadersFromJms(message, exchange);
        for (String name : headers.keySet()) {
            if (name.equalsIgnoreCase("CamelHttpResponseCode")) {
                fail("broker", name, headers.get(name));
            }
        }
    }

    @Test
    public void upperCaseVariantOfACamelPropertyDoesNotBecomeAMessageHeader() throws Exception {
        JmsBinding binding = new JmsBinding();
        Exchange exchange = new DefaultExchange(context);
        FakeJmsMessage message = new FakeJmsMessage().put("CAMELHTTPPATH", "/evil");
        Map<String, Object> headers = binding.extractHeadersFromJms(message, exchange);
        for (String name : headers.keySet()) {
            if (name.equalsIgnoreCase("CamelHttpPath")) {
                fail("broker", name, headers.get(name));
            }
        }
    }

    private static RuntimeException fail(String surface, String name, Object value) {
        throw new AssertionError(surface + ": a client-supplied name became one of Camel's own message headers: "
                + name + "=" + value);
    }
}
