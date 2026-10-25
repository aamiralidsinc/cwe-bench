package wsbench.security;

import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.jms.JmsMessageSender;

import wsbench.support.JmsFake;
import wsbench.support.Refusal;
import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class JmsReplyToIndirectionTest {

	@Test
	void indirectionInRequestedDestinationIsNotResolvedOrDelivered() throws Exception {
		JmsFake jms = JmsFake.create();
		JmsMessageSender sender = new JmsMessageSender();
		sender.setConnectionFactory(jms.connectionFactory());
		try (ServerFixture server = ServerFixture.start(sender)) {
			String destination = "jms:benchQueue?replyToName=ldap://127.0.0.1:1389/bench";
			SoapClient.Reply reply = SoapClient.reply(server.url(), WsaTestEndpoint.REPLY_ACTION, destination,
					SoapClient.ANONYMOUS);
			assertThat(jms.sends.get()).as("messages sent to the requested destination").isZero();
			assertThat(jms.usedDestinationContaining("ldap:")).as("indirection names resolved").isFalse();
			Refusal.assertRefusedInBand(reply);
		}
	}

}
