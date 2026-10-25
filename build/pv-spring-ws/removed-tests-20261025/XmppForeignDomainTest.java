package wsbench.security;

import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.xmpp.XmppMessageSender;

import wsbench.support.Refusal;
import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;
import wsbench.support.XmppFake;

import static org.assertj.core.api.Assertions.assertThat;

class XmppForeignDomainTest {

	@Test
	void foreignDomainDestinationIsNotDelivered() throws Exception {
		XmppFake xmpp = XmppFake.create("safe.example");
		XmppMessageSender sender = new XmppMessageSender();
		sender.setConnection(xmpp.connection());
		sender.afterPropertiesSet();
		try (ServerFixture server = ServerFixture.start(sender)) {
			SoapClient.Reply reply = SoapClient.reply(server.url(), WsaTestEndpoint.REPLY_ACTION,
					"xmpp:user@evil.example/resource", SoapClient.ANONYMOUS);
			assertThat(xmpp.sends.get()).as("stanzas sent to the requested destination").isZero();
			Refusal.assertRefusedInBand(reply);
		}
	}

}
