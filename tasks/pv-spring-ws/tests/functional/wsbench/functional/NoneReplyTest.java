package wsbench.functional;

import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.http.HttpComponentsMessageSender;

import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class NoneReplyTest {

	@Test
	void noneReplyIsDiscarded() throws Exception {
		try (ServerFixture server = ServerFixture.start(new HttpComponentsMessageSender())) {
			SoapClient.Reply reply = SoapClient.noneReply(server.url(), WsaTestEndpoint.REPLY_ACTION);
			assertThat(reply.status()).as("status %s", reply.status()).isBetween(200, 299);
			assertThat(reply.body()).doesNotContain("Pong");
		}
	}

}
