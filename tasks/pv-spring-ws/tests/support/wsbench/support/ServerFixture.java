package wsbench.support;

import org.eclipse.jetty.ee10.servlet.ServletContextHandler;
import org.eclipse.jetty.ee10.servlet.ServletHolder;
import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.server.ServerConnector;
import org.junit.jupiter.api.Assertions;

import org.springframework.web.context.support.GenericWebApplicationContext;
import org.springframework.ws.server.EndpointInterceptor;
import org.springframework.ws.soap.addressing.server.AnnotationActionEndpointMapping;
import org.springframework.ws.transport.WebServiceMessageSender;
import org.springframework.ws.transport.http.MessageDispatcherServlet;

/**
 * A real SOAP server: a servlet container running the framework's dispatcher, with a
 * WS-Addressing endpoint mapping and one out-of-band message sender.
 */
public final class ServerFixture implements AutoCloseable {

	private final Server server;

	private final ServerConnector connector;

	private final GenericWebApplicationContext context;

	private final String url;

	private ServerFixture(Server server, ServerConnector connector, GenericWebApplicationContext context) {
		this.server = server;
		this.connector = connector;
		this.context = context;
		this.url = "http://localhost:" + connector.getLocalPort() + "/";
	}

	public static ServerFixture start(WebServiceMessageSender sender, EndpointInterceptor... postInterceptors)
			throws Exception {
		return start(new WebServiceMessageSender[] { sender }, postInterceptors);
	}

	public static ServerFixture start(WebServiceMessageSender[] senders, EndpointInterceptor... postInterceptors)
			throws Exception {
		GenericWebApplicationContext context = new GenericWebApplicationContext();
		context.registerBean("benchEndpoint", WsaTestEndpoint.class);
		context.registerBean("benchMapping", AnnotationActionEndpointMapping.class, () -> {
			AnnotationActionEndpointMapping mapping = new AnnotationActionEndpointMapping();
			mapping.setMessageSenders(senders);
			if (postInterceptors.length > 0) {
				mapping.setPostInterceptors(postInterceptors);
			}
			return mapping;
		});
		context.refresh();

		Server server = new Server();
		ServerConnector connector = new ServerConnector(server);
		connector.setPort(0);
		server.addConnector(connector);
		ServletContextHandler handler = new ServletContextHandler();
		handler.setContextPath("/");
		handler.addServlet(new ServletHolder(new MessageDispatcherServlet(context)), "/*");
		server.setHandler(handler);
		server.start();
		Assertions.assertTrue(connector.getLocalPort() > 0, "server did not bind a port");
		return new ServerFixture(server, connector, context);
	}

	public String url() {
		return this.url;
	}

	public int port() {
		return this.connector.getLocalPort();
	}

	@Override
	public void close() {
		try {
			if (this.server.isRunning()) {
				this.server.stop();
			}
		}
		catch (Exception ex) {
			// ignore shutdown errors
		}
		this.context.close();
	}

}
