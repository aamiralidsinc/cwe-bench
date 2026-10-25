package wsbench.security;

import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.http.HttpComponentsMessageSender;

import wsbench.support.HttpVictim;
import wsbench.support.Refusal;
import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class HttpFaultToSsrfTest {

	@Test
	void loopbackFaultDestinationIsNotDelivered() throws Exception {
		try (HttpVictim victim = HttpVictim.startLoopback();
				ServerFixture server = ServerFixture.start(new HttpComponentsMessageSender())) {
			SoapClient.Reply reply = SoapClient.reply(server.url(), WsaTestEndpoint.FAULT_ACTION,
					SoapClient.ANONYMOUS, victim.uri());
			assertThat(victim.hits.get()).as("deliveries to the requested destination").isZero();
			Refusal.assertRefusedInBand(reply);
		}
	}

}
