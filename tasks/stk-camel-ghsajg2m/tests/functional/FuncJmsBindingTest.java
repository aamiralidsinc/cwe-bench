package org.apache.camel.htests;

import java.util.Map;

import org.apache.camel.CamelContext;
import org.apache.camel.Exchange;
import org.apache.camel.component.jms.JmsBinding;
import org.apache.camel.support.DefaultExchange;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/** Ordinary broker properties keep binding, and Camel's own names keep being filtered. */
public class FuncJmsBindingTest {

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
        JmsBinding binding = new JmsBinding();
        Exchange exchange = new DefaultExchange(context);
        FakeJmsMessage message = new FakeJmsMessage()
                .put("orderId", "42")
                .put("X-Trace", "t-1");
        Map<String, Object> headers = binding.extractHeadersFromJms(message, exchange);
        if (!"42".equals(String.valueOf(headers.get("orderId")))) {
            throw new AssertionError("broker: ordinary property no longer binds: " + headers.get("orderId"));
        }
        if (!"t-1".equals(String.valueOf(headers.get("X-Trace")))) {
            throw new AssertionError("broker: ordinary property no longer binds: " + headers.get("X-Trace"));
        }
    }

    @Test
    public void exactCamelPropertyIsStillFiltered() throws Exception {
        JmsBinding binding = new JmsBinding();
        Exchange exchange = new DefaultExchange(context);
        FakeJmsMessage message = new FakeJmsMessage().put("CamelBeanMethodName", "evil");
        Map<String, Object> headers = binding.extractHeadersFromJms(message, exchange);
        for (String name : headers.keySet()) {
            if (name.equalsIgnoreCase("CamelBeanMethodName")) {
                throw new AssertionError("broker: the documented filtering of Camel's own names no longer happens");
            }
        }
    }
}
