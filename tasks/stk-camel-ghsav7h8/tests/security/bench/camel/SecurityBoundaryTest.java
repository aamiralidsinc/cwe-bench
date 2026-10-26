package bench.camel;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

import org.apache.camel.CamelContext;
import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.component.undertow.DefaultUndertowHttpBinding;
import org.apache.camel.component.undertow.UndertowComponent;
import org.apache.camel.impl.DefaultCamelContext;

/**
 * The caller must never be able to place a value on the message as one of the transport's own
 * control headers, and a route's configured filtering must be the filtering its traffic gets.
 */
public class SecurityBoundaryTest {

    private static Map<String, Object> await(BlockingQueue<Map<String, Object>> queue) throws InterruptedException {
        Map<String, Object> headers = queue.poll(Harness.WAIT_SECONDS, java.util.concurrent.TimeUnit.SECONDS);
        if (headers == null) {
            throw new AssertionError("the route did not run");
        }
        return headers;
    }

    private static void assertAbsent(Map<String, Object> headers, String name) {
        Object value = Harness.header(headers, name);
        if (value != null) {
            throw new AssertionError("caller-supplied value crossed the boundary as " + name + "=" + value);
        }
    }

    private static void assertPresent(Map<String, Object> headers, String name) {
        if (Harness.header(headers, name) == null) {
            throw new AssertionError("a legitimate value was dropped: " + name);
        }
    }

    private static CamelContext newContext() {
        return new DefaultCamelContext();
    }

    private static UndertowComponent componentWithDefaultBinding() {
        UndertowComponent component = new UndertowComponent();
        component.setUndertowHttpBinding(new DefaultUndertowHttpBinding());
        return component;
    }

    // ---- the reported route and the same sink in both directions -------------------------

    public void testRequestControlHeaderIsNotMapped() throws Exception {
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
                Harness.Response response = Harness.get(port, "/probe",
                        Harness.headers("CamelControlValue", "injected", "X-Custom", "kept"));
                if (!response.ok()) {
                    throw new AssertionError("the request was not served normally: status " + response.status());
                }
                Map<String, Object> headers = await(seen);
                assertAbsent(headers, "CamelControlValue");
                assertPresent(headers, "X-Custom");
            } finally {
                context.stop();
            }
        });
    }

    public void testRequestControlValueInQueryIsNotMapped() throws Exception {
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
                Harness.Response response = Harness.get(port, "/probe?CamelControlValue=injected&q=kept", null);
                if (!response.ok()) {
                    throw new AssertionError("the request was not served normally: status " + response.status());
                }
                Map<String, Object> headers = await(seen);
                assertAbsent(headers, "CamelControlValue");
                assertPresent(headers, "q");
            } finally {
                context.stop();
            }
        });
    }

    public void testDispatchHeaderFromRequestIsNotMapped() throws Exception {
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
                Harness.Response response = Harness.get(port, "/probe",
                        Harness.headers("websocket.connectionKey", "chosen-by-caller", "X-Custom", "kept"));
                if (!response.ok()) {
                    throw new AssertionError("the request was not served normally: status " + response.status());
                }
                Map<String, Object> headers = await(seen);
                assertAbsent(headers, "websocket.connectionKey");
                assertPresent(headers, "X-Custom");
            } finally {
                context.stop();
            }
        });
    }

    // ---- the outbound side of the same boundary ------------------------------------------

    public void testDispatchHeaderOnMessageIsNotSent() throws Exception {
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
                    out.put("websocket.connectionKey", "chosen-by-caller");
                    out.put("X-Custom", "kept");
                    context.createProducerTemplate().sendBodyAndHeaders("direct:start", null, out);
                    Map<String, String> received = recorder.awaitRequest();
                    if (received == null) {
                        throw new AssertionError("the downstream request never arrived");
                    }
                    if (received.get("websocket.connectionKey") != null) {
                        throw new AssertionError("a message value crossed the boundary as a dispatch header");
                    }
                    if (received.get("X-Custom") == null) {
                        throw new AssertionError("a legitimate header was dropped");
                    }
                } finally {
                    context.stop();
                }
            }
        });
    }

    public void testControlHeaderFromRemoteResponseIsNotMapped() throws Exception {
        Harness.run(60, () -> {
            try (Harness.Recorder recorder = new Harness.Recorder(
                    Harness.headers("CamelControlValue", "from-remote", "X-Custom", "from-remote"))) {
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
                    assertAbsent(headers, "CamelControlValue");
                    assertPresent(headers, "X-Custom");
                } finally {
                    context.stop();
                }
            }
        });
    }

    // ---- the filtering configured for a route must be the one in force -------------------

    public void testConfiguredStrategyAppliesAlongsideSuppliedBinding() throws Exception {
        Harness.run(60, () -> {
            int port = Harness.freePort();
            BlockingQueue<Map<String, Object>> seen = new LinkedBlockingQueue<>();
            CamelContext context = newContext();
            context.getRegistry().bind("routeFilter", new Harness.DenyStrategy().deny("x-denied"));
            context.addComponent("undertow", componentWithDefaultBinding());
            context.addRoutes(new RouteBuilder() {
                @Override
                public void configure() {
                    from("undertow:http://127.0.0.1:" + port + "/probe?headerFilterStrategy=#routeFilter")
                            .process(exchange -> seen.add(new HashMap<>(exchange.getMessage().getHeaders())))
                            .transform().constant("ok");
                }
            });
            context.start();
            try {
                Harness.Response response = Harness.get(port, "/probe",
                        Harness.headers("x-denied", "leaked", "X-Custom", "kept"));
                if (!response.ok()) {
                    throw new AssertionError("the request was not served normally: status " + response.status());
                }
                Map<String, Object> headers = await(seen);
                assertAbsent(headers, "x-denied");
                assertPresent(headers, "X-Custom");
            } finally {
                context.stop();
            }
        });
    }

    public void testConfiguredStrategyAppliesOnRestConsumer() throws Exception {
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
                    rest("/items").get("{id}/probe").to("direct:restProbe");
                    from("direct:restProbe")
                            .process(exchange -> seen.add(new HashMap<>(exchange.getMessage().getHeaders())))
                            .transform().constant("ok");
                }
            });
            context.start();
            try {
                Harness.Response response = Harness.get(port, "/items/42/probe",
                        Harness.headers("x-denied", "leaked", "X-Custom", "kept"));
                if (!response.ok()) {
                    throw new AssertionError("the request was not served normally: status " + response.status());
                }
                Map<String, Object> headers = await(seen);
                assertAbsent(headers, "x-denied");
                assertPresent(headers, "id");
                assertPresent(headers, "X-Custom");
            } finally {
                context.stop();
            }
        });
    }

    public void testConfiguredStrategyAppliesOnRestProducer() throws Exception {
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
                    out.put("x-denied", "leaked");
                    out.put("X-Custom", "kept");
                    context.createProducerTemplate().sendBodyAndHeaders("direct:start", null, out);
                    Map<String, String> received = recorder.awaitRequest();
                    if (received == null) {
                        throw new AssertionError("the downstream request never arrived");
                    }
                    if (received.get("x-denied") != null) {
                        throw new AssertionError("a value denied by the configured filtering crossed the boundary");
                    }
                    if (received.get("X-Custom") == null) {
                        throw new AssertionError("a legitimate header was dropped");
                    }
                    if (!"/items/123?q=abc".equals(received.get(":path"))) {
                        throw new AssertionError("rest uri mapping changed: " + received.get(":path"));
                    }
                } finally {
                    context.stop();
                }
            }
        });
    }
}
