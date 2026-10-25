package io.quarkus.undertow.test;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.io.IOException;
import java.net.URI;
import java.net.URL;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Base64;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

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

public class HiddenServletPathAuthzFunctionalTest {

    static final String MARKER = "SERVLET-MARKER-3e7d";

    private static final String WEB_XML = """
            <?xml version="1.0" encoding="UTF-8"?>
            <web-app version="3.0" xmlns="http://java.sun.com/xml/ns/javaee"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://java.sun.com/xml/ns/javaee http://java.sun.com/xml/ns/javaee/web-app_3_0.xsd"
              metadata-complete="false">
              <security-constraint>
                <web-resource-collection>
                  <web-resource-name>admin</web-resource-name>
                  <url-pattern>/secure/admin/*</url-pattern>
                  <http-method>GET</http-method>
                </web-resource-collection>
                <auth-constraint><role-name>admin</role-name></auth-constraint>
              </security-constraint>
            </web-app>
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
                .addClasses(WildServlet.class, TestIdentityProvider.class, TestIdentityController.class)
                .addAsManifestResource(new StringAsset(WEB_XML), "web.xml");
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

    @WebServlet(urlPatterns = "/secure/*")
    public static class WildServlet extends HttpServlet {
        @Override
        protected void service(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
            resp.getWriter().write(MARKER);
        }
    }
    @RegisterExtension
    static QuarkusExtensionTest test = new QuarkusExtensionTest().setArchiveProducer(HiddenServletPathAuthzFunctionalTest::archive);

    @TestHTTPResource
    URL url;

    @BeforeAll
    public static void setup() {
        HiddenServletPathAuthzFunctionalTest.resetIdentities();
    }

    @Test
    public void administratorReachesConstrainedServlet() {
        Resp response = get(url, "/secure/admin/x", "admin");
        assertEquals(200, response.status());
        assertEquals(MARKER, response.body());
    }

    @Test
    public void anonymousCallerIsRefusedOnConstrainedServlet() {
        Resp response = get(url, "/secure/admin/x");
        assertEquals(401, response.status());
    }

    @Test
    public void unconstrainedServletSubtreeStaysAccessible() {
        Resp response = get(url, "/secure/public/x");
        assertEquals(200, response.status());
        assertEquals(MARKER, response.body());
    }
}
