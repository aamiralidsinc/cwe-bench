package hidden.security;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertTrue;

import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

import hidden.support.Server;
import hidden.support.Server.H2Result;
import hidden.support.Server.HttpResult;

/**
 * The protected outcome: a request must not be served by a virtual host whose TLS configuration
 * is not the one the connection negotiated. Each test drives a real TLS connection and asserts a
 * client error with no application invocation.
 */
public class SecuritySniTest {

    private static Server server;

    @BeforeClass
    public static void startServer() throws Exception {
        server = Server.start();
    }

    @AfterClass
    public static void stopServer() {
        if (server != null) {
            server.stop();
        }
    }

    @Before
    public void reset() {
        server.resetHits();
    }

    @Test
    public void requestNameSelectsAnotherVirtualHost() throws Exception {
        assertRefused(server.get(server.nioPort(), Server.WEAK, Server.STRICT, false));
    }

    @Test
    public void requestNameSelectsAnotherVirtualHostOnSecondIoImplementation() throws Exception {
        assertRefused(server.get(server.nio2Port(), Server.WEAK, Server.STRICT, false));
    }

    @Test
    public void requestNameDiffersOnlyInCaseFromTheStrictHost() throws Exception {
        assertRefused(server.get(server.nioPort(), Server.WEAK, Server.STRICT.toUpperCase(), false));
    }

    @Test
    public void connectionSentNoTlsNameAndRequestNamesTheStrictHost() throws Exception {
        assertRefused(server.get(server.nioPort(), null, Server.STRICT, false));
    }

    @Test
    public void connectorServedNameSelectsAnotherVirtualHost() throws Exception {
        assertRefused(server.get(server.proxyStrictPort(), Server.WEAK, Server.WEAK, false));
    }

    @Test
    public void requestAuthoritySelectsAnotherVirtualHost() throws Exception {
        H2Result result = server.h2(Server.WEAK, Server.STRICT, false);
        assertTrue("h2 was not negotiated: " + result, result.alpn);
        assertEquals("the application must not run: " + result, 0, result.hits);
        assertNotEquals("the server failed internally instead of refusing the request: " + result, 2,
                result.errorCode);
        assertTrue("the application body must not be produced: " + result, !result.body.contains("STRICT-OK"));
    }

    private static void assertRefused(HttpResult result) {
        assertTrue("a client error was expected: " + result, result.clientError());
        assertEquals("the application must not run: " + result, 0, result.hits);
    }
}
