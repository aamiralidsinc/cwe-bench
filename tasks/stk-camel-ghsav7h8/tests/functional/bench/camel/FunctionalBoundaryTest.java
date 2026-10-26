package bench.camel;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

import org.apache.camel.CamelContext;
import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.component.undertow.DefaultUndertowHttpBinding;
import org.apache.camel.component.undertow.UndertowComponent;
import org.apache.camel.impl.DefaultCamelContext;

/**
 * Legitimate use of the component, including the values that sit next to each hidden route.
 */
public class FunctionalBoundaryTest {

    private static Map<String, Object> await(BlockingQueue<Map<String, Object>> queue) throws InterruptedException {
        Map<String, Object> headers = queue.poll(Harness.WAIT_SECONDS, TimeUnit.SECONDS);
        if (headers == null) {
            throw new AssertionError("the route did not run");
        }
        return headers;
    }

    private static CamelContext newContext() {
        return new DefaultCamelContext();
    }

    public void testOrdinaryRequestHeadersAndQueryStillMap() throws Exception {
        Harness.run(60, () -> {
            int port = Harness.freePort();
            BlockingQueue<Map<String, Object>> seen = new LinkedBlockingQueue<>();
            CamelContext context = newContext();
            context.addRoutes(new RouteBuilder() {
                @Override
                public void configure() {
                    from("undertow:http://127.0.0.1:" + port + "/probe")
                            .process(exchange -> seen.add(new HashMap<>(exchange.getMessage().getHeaders())))
                            .transform().constant("ok");
                }
            });
            context.start();
            try {
                Harness.Response response = Harness.get(port, "/probe?q=kept",
                        Harness.headers("X-Custom", "kept"));
                if (!response.ok()) {
                    throw new AssertionError("the request was not served normally: status " + response.status());
                }
                Map<String, Object> headers = await(seen);
                if (Harness.header(headers, "X-Custom") == null) {
                    throw new AssertionError("an ordinary request header was dropped");
                }
                if (Harness.header(headers, "q") == null) {
                    throw new AssertionError("an ordinary query parameter was dropped");
                }
                if (Harness.header(headers, "CamelHttpMethod") == null) {
                    throw new AssertionError("the transport's own request metadata was dropped");
                }
            } finally {
                context.stop();
            }
        });
    }

    public void testOrdinaryResponseHeaderStillMaps() throws Exception {
        Harness.run(60, () -> {
            try (Harness.Recorder recorder = new Harness.Recorder(
                    Harness.headers("X-Custom", "from-remote"))) {
                BlockingQueue<Map<String, Object>> seen = new LinkedBlockingQueue<>();
                CamelContext context = newContext();
                context.addRoutes(new RouteBuilder() {
                    @Override
                    public void configure() {
                        from("direct:start")
                                .to("undertow:http://127.0.0.1:" + recorder.port() + "/dest")
                                .process(exchange -> seen.add(new HashMap<>(exchange.getMessage().getHeaders())));
                    }
                });
                context.start();
                try {
                    context.createProducerTemplate().sendBody("direct:start", null);
                    if (recorder.awaitRequest() == null) {
                        throw new AssertionError("the downstream request never arrived");
                    }
                    Map<String, Object> headers = await(seen);
                    if (Harness.header(headers, "X-Custom") == null) {
                        throw new AssertionError("an ordinary response header was dropped");
                    }
                } finally {
                    context.stop();
                }
            }
        });
    }

    public void testSuppliedBindingKeepsItsOwnFiltering() throws Exception {
        Harness.run(60, () -> {
            int port = Harness.freePort();
            BlockingQueue<Map<String, Object>> seen = new LinkedBlockingQueue<>();
            CamelContext context = newContext();
            UndertowComponent component = new UndertowComponent();
            DefaultUndertowHttpBinding binding = new DefaultUndertowHttpBinding();
            binding.setHeaderFilterStrategy(new Harness.DenyStrategy().deny("x-owned"));
            component.setUndertowHttpBinding(binding);
            context.addComponent("undertow", component);
            context.addRoutes(new RouteBuilder() {
                @Override
                public void configure() {
                    from("undertow:http://127.0.0.1:" + port + "/probe")
                            .process(exchange -> seen.add(new HashMap<>(exchange.getMessage().getHeaders())))
                            .transform().constant("ok");
                }
            });
            context.start();
            try {
                Harness.Response response = Harness.get(port, "/probe",
                        Harness.headers("x-owned", "kept-filtered", "X-Custom", "kept"));
                if (!response.ok()) {
                    throw new AssertionError("the request was not served normally: status " + response.status());
                }
                Map<String, Object> headers = await(seen);
                if (Harness.header(headers, "x-owned") != null) {
                    throw new AssertionError("the binding's own filtering was overridden");
                }
                if (Harness.header(headers, "X-Custom") == null) {
                    throw new AssertionError("an ordinary header was dropped");
                }
            } finally {
                context.stop();
            }
        });
    }

    public void testRestConsumerPathVariablesStillBind() throws Exception {
        Harness.run(60, () -> {
            int port = Harness.freePort();
            BlockingQueue<Map<String, Object>> seen = new LinkedBlockingQueue<>();
            CamelContext context = newContext();
            context.getRegistry().bind("routeFilter", new Harness.DenyStrategy().deny("x-denied"));
            context.addRoutes(new RouteBuilder() {
                @Override
                public void configure() {
                    restConfiguration().component("undertow").host("127.0.0.1").port(port)
                            .endpointProperty("headerFilterStrategy", "#routeFilter");
                    rest("/items").get("/{id}/probe").to("direct:restProbe");
                    from("direct:restProbe")
                            .process(exchange -> seen.add(new HashMap<>(exchange.getMessage().getHeaders())))
                            .setBody(constant("ok"));
                }
            });
            context.start();
            try {
                Harness.Response response = Harness.get(port, "/items/42/probe", null);
                if (!response.ok()) {
                    throw new AssertionError("the request was not served normally: status " + response.status());
                }
                Map<String, Object> headers = await(seen);
                Object id = Harness.header(headers, "id");
                if (id == null || !"42".equals(String.valueOf(id))) {
                    throw new AssertionError("the rest path variable was not bound: " + id);
                }
            } finally {
                context.stop();
            }
        });
    }

    public void testRestProducerTemplateAndQueryStillMap() throws Exception {
        Harness.run(60, () -> {
            try (Harness.Recorder recorder = new Harness.Recorder(null)) {
                CamelContext context = newContext();
                context.getRegistry().bind("routeFilter", new Harness.DenyStrategy().deny("x-denied"));
                context.addRoutes(new RouteBuilder() {
                    @Override
                    public void configure() {
                        restConfiguration().component("undertow").host("127.0.0.1").port(recorder.port())
                                .endpointProperty("headerFilterStrategy", "#routeFilter");
                        from("direct:start").to("rest:get:items/{id}?q={q}");
                    }
                });
                context.start();
                try {
                    Map<String, Object> out = new HashMap<>();
                    out.put("id", "123");
                    out.put("q", "abc");
                    context.createProducerTemplate().sendBodyAndHeaders("direct:start", null, out);
                    Map<String, String> received = recorder.awaitRequest();
                    if (received == null) {
                        throw new AssertionError("the downstream request never arrived");
                    }
                    if (!"/items/123?q=abc".equals(received.get(":path"))) {
                        throw new AssertionError("rest uri mapping changed: " + received.get(":path"));
                    }
                    if (received.get("id") != null || received.get("q") != null) {
                        throw new AssertionError("a mapped template value was also sent as a header");
                    }
                } finally {
                    context.stop();
                }
            }
        });
    }

    public void testPlainProducerStillSendsOrdinaryHeaders() throws Exception {
        Harness.run(60, () -> {
            try (Harness.Recorder recorder = new Harness.Recorder(null)) {
                CamelContext context = newContext();
                context.addRoutes(new RouteBuilder() {
                    @Override
                    public void configure() {
                        from("direct:start").to("undertow:http://127.0.0.1:" + recorder.port() + "/dest");
                    }
                });
                context.start();
                try {
                    Map<String, Object> out = new HashMap<>();
                    out.put("X-Custom", "kept");
                    context.createProducerTemplate().sendBodyAndHeaders("direct:start", null, out);
                    Map<String, String> received = recorder.awaitRequest();
                    if (received == null) {
                        throw new AssertionError("the downstream request never arrived");
                    }
                    if (received.get("X-Custom") == null) {
                        throw new AssertionError("an ordinary header was dropped");
                    }
                } finally {
                    context.stop();
                }
            }
        });
    }

    public void testDefaultRestRouteStillRoundTrips() throws Exception {
        Harness.run(60, () -> {
            int port = Harness.freePort();
            CamelContext context = newContext();
            context.addRoutes(new RouteBuilder() {
                @Override
                public void configure() {
                    restConfiguration().component("undertow").host("127.0.0.1").port(port);
                    rest("/items").get("/{id}/name").to("direct:name");
                    from("direct:name")
                            .setBody(exchange -> exchange.getMessage().getHeader("id", String.class) + ";ok");
                }
            });
            context.start();
            try {
                Harness.Response response = Harness.get(port, "/items/7/name", null);
                if (!response.ok()) {
                    throw new AssertionError("the request was not served normally: status " + response.status());
                }
            } finally {
                context.stop();
            }
        });
    }
}
