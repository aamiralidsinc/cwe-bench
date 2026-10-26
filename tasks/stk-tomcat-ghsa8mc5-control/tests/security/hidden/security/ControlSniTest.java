package hidden.security;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

import hidden.support.Server;
import hidden.support.Server.HttpResult;

/**
 * Control security suite: only the advisory's own route. A TLS connection negotiated for one
 * virtual host must not serve a request that names another virtual host with a different TLS
 * configuration.
 */
public class ControlSniTest {

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
        HttpResult result = server.get(server.nioPort(), Server.WEAK, Server.STRICT, false);
        assertTrue("a client error was expected: " + result, result.clientError());
        assertEquals("the application must not run: " + result, 0, result.hits);
    }
}
