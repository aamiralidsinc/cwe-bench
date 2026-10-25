package wsbench.functional;

import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.http.HttpComponentsMessageSender;

import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class AnonymousReplyTest {

	@Test
	void anonymousReplyIsReturnedInBand() throws Exception {
		try (ServerFixture server = ServerFixture.start(new HttpComponentsMessageSender())) {
			SoapClient.Reply reply = SoapClient.reply(server.url(), WsaTestEndpoint.REPLY_ACTION,
					SoapClient.ANONYMOUS, SoapClient.ANONYMOUS);
			assertThat(reply.status()).isBetween(200, 299);
			assertThat(reply.body()).contains("Pong");
		}
	}

}
