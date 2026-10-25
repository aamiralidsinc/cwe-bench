package wsbench.functional;

import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.xmpp.XmppMessageSender;

import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;
import wsbench.support.XmppFake;

import static org.assertj.core.api.Assertions.assertThat;

class XmppOutOfBandDeliveryTest {

	@Test
	void destinationOnTheServiceDomainReceivesTheReply() throws Exception {
		XmppFake xmpp = XmppFake.create("safe.example");
		XmppMessageSender sender = new XmppMessageSender();
		sender.setConnection(xmpp.connection());
		sender.afterPropertiesSet();
		try (ServerFixture server = ServerFixture.start(sender)) {
			SoapClient.reply(server.url(), WsaTestEndpoint.REPLY_ACTION, "xmpp:user@safe.example/resource",
					SoapClient.ANONYMOUS);
			assertThat(xmpp.sends.get()).as("stanzas sent").isEqualTo(1);
			assertThat(xmpp.sentTo).anyMatch((jid) -> jid.startsWith("user@safe.example"));
		}
	}

}
