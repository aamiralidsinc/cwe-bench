package wsbench.security;

import jakarta.mail.Session;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.mail.MailMessageSender;

import wsbench.support.MailFake;
import wsbench.support.Refusal;
import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class MailReplyToLocalhostTest {

	@BeforeEach
	void reset() {
		MailFake.reset();
	}

	@Test
	void localMailboxDestinationIsNotDelivered() throws Exception {
		Session session = MailFake.session();
		MailMessageSender sender = new MailMessageSender();
		sender.setSession(session);
		sender.setTransportUri("bench://localhost");
		sender.setStoreUri("bench://localhost/INBOX");
		sender.afterPropertiesSet();
		try (ServerFixture server = ServerFixture.start(sender)) {
			SoapClient.Reply reply = SoapClient.reply(server.url(), WsaTestEndpoint.REPLY_ACTION,
					"mailto:root@localhost", SoapClient.ANONYMOUS);
			assertThat(MailFake.sends.get()).as("messages delivered").isZero();
			assertThat(MailFake.deliveredTo("root@localhost")).as("mailbox reached").isFalse();
			Refusal.assertRefusedInBand(reply);
		}
	}

}
