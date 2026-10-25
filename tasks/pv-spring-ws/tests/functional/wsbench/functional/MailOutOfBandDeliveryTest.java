package wsbench.functional;

import jakarta.mail.Session;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import org.springframework.ws.transport.mail.MailMessageSender;

import wsbench.support.MailFake;
import wsbench.support.ServerFixture;
import wsbench.support.SoapClient;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class MailOutOfBandDeliveryTest {

	@BeforeEach
	void reset() {
		MailFake.reset();
	}

	@Test
	void ordinaryMailboxReceivesTheReply() throws Exception {
		Session session = MailFake.session();
		MailMessageSender sender = new MailMessageSender();
		sender.setSession(session);
		sender.setTransportUri("bench://localhost");
		sender.setStoreUri("bench://localhost/INBOX");
		sender.afterPropertiesSet();
		try (ServerFixture server = ServerFixture.start(sender)) {
			SoapClient.reply(server.url(), WsaTestEndpoint.REPLY_ACTION, "mailto:ops@example.com",
					SoapClient.ANONYMOUS);
			assertThat(MailFake.sends.get()).as("messages delivered").isEqualTo(1);
			assertThat(MailFake.deliveredTo("ops@example.com")).as("mailbox reached").isTrue();
		}
	}

}
