package wsbench.security;

import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.http.HttpComponentsMessageSender;

import wsbench.support.HttpVictim;
import wsbench.support.Refusal;
import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class HttpAddressShapeTest {

	@Test
	void ipv6LoopbackReplyDestinationIsNotDelivered() throws Exception {
		try (HttpVictim victim = HttpVictim.startIpv6Loopback();
				ServerFixture server = ServerFixture.start(new HttpComponentsMessageSender())) {
			SoapClient.Reply reply = SoapClient.reply(server.url(), WsaTestEndpoint.REPLY_ACTION, victim.uri(),
					SoapClient.ANONYMOUS);
			assertThat(victim.hits.get()).as("deliveries to the requested destination").isZero();
			Refusal.assertRefusedInBand(reply);
		}
	}

	@Test
	void anyLocalReplyDestinationIsNotDelivered() throws Exception {
		try (HttpVictim victim = HttpVictim.startAnyLocal();
				ServerFixture server = ServerFixture.start(new HttpComponentsMessageSender())) {
			SoapClient.Reply reply = SoapClient.reply(server.url(), WsaTestEndpoint.REPLY_ACTION, victim.uri(),
					SoapClient.ANONYMOUS);
			assertThat(victim.hits.get()).as("deliveries to the requested destination").isZero();
			Refusal.assertRefusedInBand(reply);
		}
	}

}
