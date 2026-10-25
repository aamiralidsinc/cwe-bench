package wsbench.functional;

import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.jms.JmsMessageSender;

import wsbench.support.JmsFake;
import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class JmsOutOfBandDeliveryTest {

	@Test
	void ordinaryDestinationReceivesTheReply() throws Exception {
		JmsFake jms = JmsFake.create();
		JmsMessageSender sender = new JmsMessageSender();
		sender.setConnectionFactory(jms.connectionFactory());
		try (ServerFixture server = ServerFixture.start(sender)) {
			SoapClient.reply(server.url(), WsaTestEndpoint.REPLY_ACTION, "jms:benchQueue", SoapClient.ANONYMOUS);
			assertThat(jms.sends.get()).as("messages sent to the ordinary destination").isEqualTo(1);
			assertThat(jms.destinations).contains("benchQueue");
		}
	}

}
