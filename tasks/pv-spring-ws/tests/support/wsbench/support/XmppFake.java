package wsbench.support;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import org.jivesoftware.smack.XMPPConnection;
import org.jivesoftware.smack.packet.Stanza;
import org.jxmpp.jid.impl.JidCreate;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * A recording stand-in for an XMPP connection. It answers for its own service domain and
 * records every stanza actually sent.
 */
public final class XmppFake {

	public final List<String> sentTo = Collections.synchronizedList(new ArrayList<>());

	public final AtomicInteger sends = new AtomicInteger();

	private final XMPPConnection connection;

	private XmppFake(XMPPConnection connection) {
		this.connection = connection;
	}

	public static XmppFake create(String serviceDomain) throws Exception {
		XMPPConnection connection = mock(XMPPConnection.class);
		XmppFake fake = new XmppFake(connection);
		when(connection.getUser()).thenReturn(JidCreate.entityFullFrom("server@" + serviceDomain + "/bench"));
		when(connection.getXMPPServiceDomain()).thenReturn(JidCreate.domainBareFrom(serviceDomain));
		doAnswer((invocation) -> {
			Stanza stanza = invocation.getArgument(0);
			fake.sends.incrementAndGet();
			fake.sentTo.add(stanza.getTo().toString());
			return null;
		}).when(connection).sendStanza(any(Stanza.class));
		return fake;
	}

	public XMPPConnection connection() {
		return this.connection;
	}

}
