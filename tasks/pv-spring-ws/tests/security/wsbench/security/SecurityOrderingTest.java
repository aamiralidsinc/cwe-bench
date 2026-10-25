package wsbench.security;

import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.jms.JmsMessageSender;

import wsbench.support.FirewallSecurityInterceptor;
import wsbench.support.JmsFake;
import wsbench.support.Refusal;
import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class SecurityOrderingTest {

	@Test
	void rejectedRequestCausesNoOutOfBandDelivery() throws Exception {
		JmsFake jms = JmsFake.create();
		JmsMessageSender sender = new JmsMessageSender();
		sender.setConnectionFactory(jms.connectionFactory());
		try (ServerFixture server = ServerFixture.start(sender, new FirewallSecurityInterceptor())) {
			SoapClient.Reply reply = SoapClient.reply(server.url(), WsaTestEndpoint.REPLY_ACTION,
					SoapClient.ANONYMOUS, "jms:auditQueue");
			assertThat(jms.sends.get()).as("messages sent for a rejected request").isZero();
			Refusal.assertRefusedInBand(reply);
		}
	}

}
