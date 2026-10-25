package wsbench.support;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Properties;
import java.util.concurrent.atomic.AtomicInteger;

import jakarta.mail.Address;
import jakarta.mail.Message;
import jakarta.mail.MessagingException;
import jakarta.mail.Provider;
import jakarta.mail.Session;
import jakarta.mail.Transport;
import jakarta.mail.URLName;
import jakarta.mail.internet.InternetAddress;

/**
 * A JavaMail session backed by a recording transport provider. Recipients are recorded
 * per message; no mail leaves the machine.
 */
public final class MailFake {

	public static final List<String> recipients = Collections.synchronizedList(new ArrayList<>());

	public static final AtomicInteger sends = new AtomicInteger();

	private MailFake() {
	}

	public static void reset() {
		recipients.clear();
		sends.set(0);
	}

	public static Session session() {
		Session session = Session.getInstance(new Properties());
		session.addProvider(new Provider(Provider.Type.TRANSPORT, "bench", RecordingTransport.class.getName(),
				"bench", "1.0"));
		return session;
	}

	public static boolean deliveredTo(String address) {
		synchronized (recipients) {
			return recipients.contains(address);
		}
	}

	/**
	 * Transport provider used by {@link #session()}.
	 */
	public static final class RecordingTransport extends Transport {

		public RecordingTransport(Session session, URLName urlName) {
			super(session, urlName);
		}

		@Override
		protected boolean protocolConnect(String host, int port, String user, String password) {
			return true;
		}

		@Override
		public synchronized void sendMessage(Message message, Address[] addresses) throws MessagingException {
			MailFake.sends.incrementAndGet();
			if (addresses != null) {
				for (Address address : addresses) {
					String value = (address instanceof InternetAddress internetAddress) ? internetAddress.getAddress()
							: String.valueOf(address);
					MailFake.recipients.add(value);
				}
			}
		}

	}

}
