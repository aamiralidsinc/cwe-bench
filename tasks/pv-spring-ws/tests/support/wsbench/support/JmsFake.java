package wsbench.support;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import jakarta.jms.BytesMessage;
import jakarta.jms.Connection;
import jakarta.jms.ConnectionFactory;
import jakarta.jms.Destination;
import jakarta.jms.JMSException;
import jakarta.jms.Message;
import jakarta.jms.MessageProducer;
import jakarta.jms.Queue;
import jakarta.jms.Session;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyBoolean;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * A recording stand-in for a JMS broker. It answers per destination and records every
 * destination name resolved and every message actually sent.
 */
public final class JmsFake {

	public final List<String> destinations = Collections.synchronizedList(new ArrayList<>());

	public final AtomicInteger sends = new AtomicInteger();

	private final ConnectionFactory connectionFactory;

	private JmsFake(ConnectionFactory connectionFactory) {
		this.connectionFactory = connectionFactory;
	}

	public static JmsFake create() throws JMSException {
		ConnectionFactory connectionFactory = mock(ConnectionFactory.class);
		Connection connection = mock(Connection.class);
		Session session = mock(Session.class);
		MessageProducer producer = mock(MessageProducer.class);
		JmsFake fake = new JmsFake(connectionFactory);
		when(connectionFactory.createConnection()).thenReturn(connection);
		when(connection.createSession(anyBoolean(), anyInt())).thenReturn(session);
		when(session.createQueue(anyString())).thenAnswer((invocation) -> {
			fake.destinations.add(invocation.getArgument(0));
			return mock(Queue.class);
		});
		when(session.createTemporaryQueue()).thenReturn(mock(jakarta.jms.TemporaryQueue.class));
		when(session.createBytesMessage()).thenReturn(mock(BytesMessage.class));
		when(session.createTextMessage()).thenReturn(mock(jakarta.jms.TextMessage.class));
		when(session.getTransacted()).thenReturn(false);
		when(session.createProducer(any(Destination.class))).thenReturn(producer);
		doAnswer((invocation) -> {
			fake.sends.incrementAndGet();
			return null;
		}).when(producer).send(any(Message.class));
		return fake;
	}

	public ConnectionFactory connectionFactory() {
		return this.connectionFactory;
	}

	public boolean usedDestinationContaining(String token) {
		synchronized (this.destinations) {
			return this.destinations.stream().anyMatch((name) -> name != null && name.contains(token));
		}
	}

}
