package org.apache.camel.htests;

import java.util.Map;

import org.apache.camel.CamelContext;
import org.apache.camel.Exchange;
import org.apache.camel.component.sjms.jms.DefaultJmsKeyFormatStrategy;
import org.apache.camel.component.sjms.jms.JmsBinding;
import org.apache.camel.support.DefaultExchange;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/** Ordinary broker properties keep binding through the simple consumer. */
public class FuncSjmsBindingTest {

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
    public void ordinaryPropertiesKeepBinding() throws Exception {
        JmsBinding binding = new JmsBinding(true, true,
                new org.apache.camel.component.sjms.SjmsHeaderFilterStrategy(),
                new DefaultJmsKeyFormatStrategy(), null);
        Exchange exchange = new DefaultExchange(context);
        FakeJmsMessage message = new FakeJmsMessage().put("orderId", "42").put("X-Trace", "t-1");
        Map<String, Object> headers = binding.extractHeadersFromJms(message, exchange);
        if (!"42".equals(String.valueOf(headers.get("orderId")))) {
            throw new AssertionError("broker: ordinary property no longer binds: " + headers.get("orderId"));
        }
        if (!"t-1".equals(String.valueOf(headers.get("X-Trace")))) {
            throw new AssertionError("broker: ordinary property no longer binds: " + headers.get("X-Trace"));
        }
    }
}
