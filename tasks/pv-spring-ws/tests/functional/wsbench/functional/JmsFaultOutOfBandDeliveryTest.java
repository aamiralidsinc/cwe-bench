package wsbench.functional;

import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.jms.JmsMessageSender;

import wsbench.support.JmsFake;
import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class JmsFaultOutOfBandDeliveryTest {

	@Test
	void ordinaryFaultDestinationReceivesTheFault() throws Exception {
		JmsFake jms = JmsFake.create();
		JmsMessageSender sender = new JmsMessageSender();
		sender.setConnectionFactory(jms.connectionFactory());
		try (ServerFixture server = ServerFixture.start(sender)) {
			SoapClient.reply(server.url(), WsaTestEndpoint.FAULT_ACTION, SoapClient.ANONYMOUS, "jms:auditQueue");
			assertThat(jms.sends.get()).as("messages sent to the ordinary fault destination").isEqualTo(1);
			assertThat(jms.destinations).contains("auditQueue");
		}
	}

}
