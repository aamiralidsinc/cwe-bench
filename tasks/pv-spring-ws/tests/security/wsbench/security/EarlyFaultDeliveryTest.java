package wsbench.security;

import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.http.HttpComponentsMessageSender;

import wsbench.support.HttpVictim;
import wsbench.support.Refusal;
import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class EarlyFaultDeliveryTest {

	@Test
	void loopbackFaultDestinationOfARejectedRequestIsNotDelivered() throws Exception {
		try (HttpVictim victim = HttpVictim.startLoopback();
				ServerFixture server = ServerFixture.start(new HttpComponentsMessageSender())) {
			SoapClient.Reply reply = SoapClient.replyWithoutMessageId(server.url(), WsaTestEndpoint.REPLY_ACTION,
					SoapClient.ANONYMOUS, victim.uri());
			assertThat(victim.hits.get()).as("deliveries to the requested destination").isZero();
			Refusal.assertRefusedInBand(reply);
		}
	}

}
