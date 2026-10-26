package org.apache.camel.htests;

import java.util.Map;

import org.apache.camel.CamelContext;
import org.apache.camel.Exchange;
import org.apache.camel.component.sjms.SjmsHeaderFilterStrategy;
import org.apache.camel.component.sjms.jms.DefaultJmsKeyFormatStrategy;
import org.apache.camel.support.DefaultExchange;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/**
 * A message from a broker that carries one of Camel's own header names must not deliver that header.
 */
public class SecSjmsCamelPropertyTest {

    private CamelContext context;

    @Before
    public void setUp() {
        context = Support.newContext();
    }

    @After
    public void tearDown() {
        Support.close(context);
    }

    private Map<String, Object> extract(FakeJmsMessage message) throws Exception {
        org.apache.camel.component.sjms.jms.JmsBinding binding = new org.apache.camel.component.sjms.jms.JmsBinding(
                true, true, new SjmsHeaderFilterStrategy(), new DefaultJmsKeyFormatStrategy(), null);
        Exchange exchange = new DefaultExchange(context);
        return binding.extractHeadersFromJms(message, exchange);
    }

    @Test
    public void camelPropertyDoesNotBecomeAMessageHeader() throws Exception {
        Map<String, Object> headers = extract(new FakeJmsMessage().put("CamelBeanMethodName", "evil"));
        for (String name : headers.keySet()) {
            if (name.equalsIgnoreCase("CamelBeanMethodName")) {
                throw new AssertionError("broker: a client-supplied name became one of Camel's own message headers: "
                        + name + "=" + headers.get(name));
            }
        }
    }
}
