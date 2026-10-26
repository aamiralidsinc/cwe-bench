package hidden.functional;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

import hidden.support.Server;
import hidden.support.Server.H2Result;
import hidden.support.Server.HttpResult;

/**
 * Legitimate requests must keep working: a host that resolves to the TLS configuration the
 * connection negotiated is served, including configurations shared by several names.
 */
public class FunctionalSniTest {

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
    public void matchingNameIsServed() throws Exception {
        assertServed(server.get(server.nioPort(), Server.WEAK, Server.WEAK, false), "WEAK");
    }

    @Test
    public void strictHostIsServedWithAClientCertificate() throws Exception {
        assertServed(server.get(server.nioPort(), Server.STRICT, Server.STRICT, true), "STRICT");
    }

    @Test
    public void caseOnlyDifferenceIsServed() throws Exception {
        assertServed(server.get(server.nioPort(), Server.STRICT, Server.STRICT.toUpperCase(), true), "STRICT");
    }

    @Test
    public void connectionWithoutTlsNameReachesTheDefaultHost() throws Exception {
        assertServed(server.get(server.nioPort(), null, Server.WEAK, false), "WEAK");
    }

    @Test
    public void matchingNameIsServedOnSecondIoImplementation() throws Exception {
        assertServed(server.get(server.nio2Port(), Server.WEAK, Server.WEAK, false), "WEAK");
    }

    @Test
    public void strictHostIsServedOnSecondIoImplementation() throws Exception {
        assertServed(server.get(server.nio2Port(), Server.STRICT, Server.STRICT, true), "STRICT");
    }

    @Test
    public void connectorServedNameSharingTheTlsConfigurationIsServed() throws Exception {
        assertServed(server.get(server.proxyInternalPort(), Server.WEAK, Server.WEAK, false), "INTERNAL");
    }

    @Test
    public void connectorServedNameMatchingTheTlsConfigurationIsServed() throws Exception {
        assertServed(server.get(server.proxyStrictPort(), Server.STRICT, Server.STRICT, true), "STRICT");
    }

    @Test
    public void hostsSharingOneConfigurationAreServed() throws Exception {
        assertServed(server.get(server.wildPort(), Server.A, Server.B, false), "B");
    }

    @Test
    public void matchingAuthorityIsServedOverHttp2() throws Exception {
        H2Result result = server.h2(Server.STRICT, Server.STRICT, true);
        assertTrue("h2 was not negotiated: " + result, result.alpn);
        assertEquals("the request must be served: " + result, 1, result.hits);
        assertTrue("the application body was expected: " + result, result.body.contains("STRICT-OK"));
    }

    @Test
    public void hostsSharingOneConfigurationAreServedOverHttp2() throws Exception {
        H2Result result = server.h2(Server.A, Server.B, false);
        assertTrue("h2 was not negotiated: " + result, result.alpn);
        assertEquals("the request must be served: " + result, 1, result.hits);
        assertTrue("the application body was expected: " + result, result.body.contains("B-OK"));
    }

    private static void assertServed(HttpResult result, String tag) {
        assertEquals("the request must be served: " + result, 200, result.status);
        assertEquals("the application must run once: " + result, 1, result.hits);
        assertTrue("the application body was expected: " + result, result.body.contains(tag + "-OK"));
    }
}
