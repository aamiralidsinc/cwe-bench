package io.quarkus.vertx.http.security;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.net.URI;
import java.net.URL;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Base64;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;

import org.jboss.shrinkwrap.api.ShrinkWrap;
import org.jboss.shrinkwrap.api.asset.StringAsset;
import org.jboss.shrinkwrap.api.spec.JavaArchive;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.RegisterExtension;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import io.quarkus.security.test.utils.TestIdentityController;
import io.quarkus.security.test.utils.TestIdentityProvider;
import io.quarkus.test.QuarkusExtensionTest;
import io.quarkus.test.common.http.TestHTTPResource;
import io.vertx.ext.web.Router;

public class HiddenStaticPathAuthzTest {

    static final String ADMIN_MARKER = "ADMIN-STATIC-MARKER-7f3a";
    static final String SECRET_MARKER = "SECRET-STATIC-MARKER-9c2b";
    static final String PUBLIC_MARKER = "PUBLIC-STATIC-MARKER-4d8e";
    static final String INTERNAL_MARKER = "INTERNAL-STATIC-MARKER-1a6f";
    static final String ROUTE_MARKER = "SECURE-ROUTE-MARKER-5b0c";

    private static final String PROPS = """
            quarkus.http.auth.permission.admin.paths=/api/admin/*
            quarkus.http.auth.permission.admin.policy=admin-policy
            quarkus.http.auth.policy.admin-policy.roles-allowed=admin
            quarkus.http.auth.permission.secret.paths=/api/secret/*
            quarkus.http.auth.permission.secret.policy=authenticated
            quarkus.http.auth.permission.public.paths=/api/public/*
            quarkus.http.auth.permission.public.policy=permit
            quarkus.http.auth.permission.secure.paths=/api/secure/*
            quarkus.http.auth.permission.secure.policy=admin-policy
            quarkus.http.auth.permission.open.paths=/api/open/*
            quarkus.http.auth.permission.open.policy=permit
            quarkus.http.static-resources.excluded-paths=/api/internal
            """;

    private static final HttpClient CLIENT = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .followRedirects(HttpClient.Redirect.NEVER)
            .build();

    record Resp(int status, String body) {
        boolean clientError() {
            return status >= 400 && status < 500;
        }
    }

    static JavaArchive archive() {
        return ShrinkWrap.create(JavaArchive.class)
                .addClasses(TestIdentityController.class, TestIdentityProvider.class, Routes.class)
                .addAsResource(new StringAsset(ADMIN_MARKER), "META-INF/resources/api/admin/admin.html")
                .addAsResource(new StringAsset(SECRET_MARKER), "META-INF/resources/api/secret/secret.html")
                .addAsResource(new StringAsset(PUBLIC_MARKER), "META-INF/resources/api/public/pub.html")
                .addAsResource(new StringAsset(PUBLIC_MARKER), "META-INF/resources/api/public/nested/pub.html")
                .addAsResource(new StringAsset(INTERNAL_MARKER), "META-INF/resources/api/internal/internal.html")
                .addAsResource(new StringAsset(PROPS), "application.properties");
    }

    static void resetIdentities() {
        TestIdentityController.resetRoles().add("admin", "admin", "admin").add("user", "user", "user");
    }

    static Resp get(URL base, String path) {
        return get(base, path, null);
    }

    static Resp get(URL base, String path, String user) {
        try {
            HttpRequest.Builder builder = HttpRequest.newBuilder()
                    .uri(URI.create("http://" + base.getHost() + ":" + base.getPort() + path))
                    .timeout(Duration.ofSeconds(20))
                    .GET();
            if (user != null) {
                String token = Base64.getEncoder()
                        .encodeToString((user + ":" + user).getBytes(StandardCharsets.UTF_8));
                builder.header("Authorization", "Basic " + token);
            }
            HttpResponse<String> response = CLIENT.send(builder.build(), HttpResponse.BodyHandlers.ofString());
            return new Resp(response.statusCode(), response.body() == null ? "" : response.body());
        } catch (Exception e) {
            throw new RuntimeException("request to " + path + " failed", e);
        }
    }

    @ApplicationScoped
    public static class Routes {
        public void setup(@Observes Router router) {
            router.route("/api/secure/*").order(-1)
                    .handler(rc -> rc.response().end(ROUTE_MARKER));
        }
    }
    @RegisterExtension
    static QuarkusExtensionTest test = new QuarkusExtensionTest().setArchiveProducer(HiddenStaticPathAuthzTest::archive);

    @TestHTTPResource
    URL url;

    @BeforeAll
    public static void setup() {
        HiddenStaticPathAuthzTest.resetIdentities();
    }

    @ParameterizedTest
    @ValueSource(strings = {
            "/api%2Fadmin%2Fadmin.html",
            "/api/admin%2Fadmin.html",
            "/api%2Fsecret%2Fsecret.html",
            "/api/secret%2Fsecret.html",
            "/api%2fadmin%2fadmin.html",
    })
    public void protectedStaticContentIsNotServedToAnonymousCaller(String path) {
        Resp response = get(url, path);
        assertTrue(response.clientError(),
                "request '" + path + "' was not refused, status " + response.status());
        assertFalse(response.body().contains(ADMIN_MARKER),
                "admin static content was served for '" + path + "'");
        assertFalse(response.body().contains(SECRET_MARKER),
                "secret static content was served for '" + path + "'");
    }
}
