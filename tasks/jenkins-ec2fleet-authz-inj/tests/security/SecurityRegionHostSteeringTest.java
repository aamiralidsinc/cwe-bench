package com.amazon.jenkins.ec2fleet;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.CopyOnWriteArrayList;

import com.cloudbees.jenkins.plugins.awscredentials.AWSCredentialsImpl;
import com.cloudbees.plugins.credentials.CredentialsScope;
import com.cloudbees.plugins.credentials.SystemCredentialsProvider;
import hudson.ProxyConfiguration;
import jenkins.model.Jenkins;
import org.htmlunit.HttpMethod;
import org.htmlunit.WebRequest;
import org.junit.jupiter.api.Test;
import org.jvnet.hudson.test.JenkinsRule;
import org.jvnet.hudson.test.MockAuthorizationStrategy;
import org.jvnet.hudson.test.junit.jupiter.WithJenkins;

import static org.junit.jupiter.api.Assertions.assertFalse;

/**
 * A caller-supplied region is turned into a service host. Whatever region string an
 * administrator's form submission carries, Jenkins must never send a credential-bearing
 * request to a host outside AWS. Outbound requests are observed through the proxy.
 */
@WithJenkins
class SecurityRegionHostSteeringTest {

    private static final String ATTACKER_MARK = "evil";
    private static final String[] BAD_REGIONS = {
        "evil.com/", "evil.example/path", "evil:9000/", "evil.com?x", "evil.com#", "x@evil.com/"};

    @Test
    void malformedRegionCannotSteerFleetListing(JenkinsRule j) throws Exception {
        try (RecordingProxy proxy = setUp(j)) {
            for (final String region : BAD_REGIONS) {
                post(j, "descriptorByName/com.amazon.jenkins.ec2fleet.EC2FleetCloud/fillFleetItems?awsCredentialsId=cred&endpoint=&fleet=&showAllFleets=true&region=" + q(region));
                assertNeverSteered(proxy, region);
            }
        }
    }

    @Test
    void malformedRegionCannotSteerInstanceTypePreview(JenkinsRule j) throws Exception {
        try (RecordingProxy proxy = setUp(j)) {
            for (final String region : BAD_REGIONS) {
                post(j, "descriptorByName/com.amazon.jenkins.ec2fleet.EC2FleetCloud$NodeHardwareScaler/fillInstanceTypeItems?awsCredentialsId=cred&endpoint=&region=" + q(region));
                assertNeverSteered(proxy, region);
            }
        }
    }

    @Test
    void malformedRegionCannotSteerLabelKeyPairListing(JenkinsRule j) throws Exception {
        try (RecordingProxy proxy = setUp(j)) {
            for (final String region : BAD_REGIONS) {
                post(j, "descriptorByName/com.amazon.jenkins.ec2fleet.EC2FleetLabelCloud/fillEc2KeyPairNameItems?awsCredentialsId=cred&endpoint=&region=" + q(region));
                assertNeverSteered(proxy, region);
            }
        }
    }

    /** Fails if any outbound request was addressed to an attacker-chosen host. */
    private static void assertNeverSteered(final RecordingProxy proxy, final String input) {
        for (final String line : proxy.requestLines) {
            assertFalse(line.toLowerCase(Locale.ENGLISH).contains(ATTACKER_MARK),
                    "input '" + input + "' made Jenkins contact a non-AWS host with a stored credential: " + line);
        }
    }

    /**
     * Stands in for Jenkins' configured HTTP proxy. Every outbound AWS SDK request goes
     * through it, so the first line of each request (e.g. {@code CONNECT host:443}) shows
     * exactly which host Jenkins tried to reach. It refuses to tunnel anything.
     */
    static final class RecordingProxy implements AutoCloseable {
        final List<String> requestLines = new CopyOnWriteArrayList<>();
        private final ServerSocket server;

        RecordingProxy() throws IOException {
            server = new ServerSocket(0, 50, InetAddress.getLoopbackAddress());
            final Thread t = new Thread(this::serve, "recording-proxy");
            t.setDaemon(true);
            t.start();
        }

        int port() {
            return server.getLocalPort();
        }

        private void serve() {
            while (!server.isClosed()) {
                try (Socket s = server.accept()) {
                    s.setSoTimeout(5000);
                    final BufferedReader in = new BufferedReader(
                            new InputStreamReader(s.getInputStream(), StandardCharsets.ISO_8859_1));
                    final String line = in.readLine();
                    if (line != null) {
                        requestLines.add(line);
                    }
                    final OutputStream out = s.getOutputStream();
                    out.write("HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
                            .getBytes(StandardCharsets.ISO_8859_1));
                    out.flush();
                } catch (final IOException e) {
                    // keep serving
                }
            }
        }

        @Override
        public void close() throws IOException {
            server.close();
        }
    }

    /** Admin-only Jenkins with a stored AWS credential "cred", all outbound traffic routed through the proxy. */
    private static RecordingProxy setUp(final JenkinsRule j) throws IOException {
        j.jenkins.setSecurityRealm(j.createDummySecurityRealm());
        final MockAuthorizationStrategy auth = new MockAuthorizationStrategy();
        auth.grant(Jenkins.ADMINISTER).everywhere().to("admin");
        j.jenkins.setAuthorizationStrategy(auth);
        j.jenkins.setCrumbIssuer(null);
        SystemCredentialsProvider.getInstance().getCredentials().add(new AWSCredentialsImpl(
                CredentialsScope.GLOBAL, "cred", "AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "test"));
        final RecordingProxy proxy = new RecordingProxy();
        j.jenkins.setProxy(new ProxyConfiguration("127.0.0.1", proxy.port()));
        return proxy;
    }

    private static String q(final String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }

    /** Admin POST (a genuine form submission); any response status is acceptable here. */
    private static void post(final JenkinsRule j, final String path) throws Exception {
        final JenkinsRule.WebClient wc = j.createWebClient();
        wc.setThrowExceptionOnFailingStatusCode(false);
        wc.login("admin");
        wc.getPage(new WebRequest(new URL(j.getURL(), path), HttpMethod.POST));
    }
}
