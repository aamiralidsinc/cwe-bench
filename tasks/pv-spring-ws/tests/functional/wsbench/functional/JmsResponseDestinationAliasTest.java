package wsbench.functional;

import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.jms.JmsMessageSender;

import wsbench.support.JmsFake;
import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class JmsResponseDestinationAliasTest {

	@Test
	void ordinaryLegacyResponseDestinationReceivesTheReply() throws Exception {
		JmsFake jms = JmsFake.create();
		JmsMessageSender sender = new JmsMessageSender();
		sender.setConnectionFactory(jms.connectionFactory());
		try (ServerFixture server = ServerFixture.start(sender)) {
			SoapClient.reply(server.url(), WsaTestEndpoint.REPLY_ACTION, "jms:benchQueue?replyTo=auditQueue",
					SoapClient.ANONYMOUS);
			assertThat(jms.sends.get()).as("messages sent").isEqualTo(1);
			assertThat(jms.destinations).contains("auditQueue");
		}
	}

}
