package wsbench.functional;

import java.net.URI;

import javax.xml.transform.stream.StreamSource;

import org.junit.jupiter.api.Test;

import org.springframework.ws.client.core.WebServiceTemplate;
import org.springframework.ws.soap.addressing.client.ActionCallback;
import org.springframework.ws.transport.http.HttpComponentsMessageSender;
import org.springframework.xml.transform.StringResult;

import wsbench.support.ServerFixture;
import wsbench.support.WsaTestEndpoint;

import static org.assertj.core.api.Assertions.assertThat;

class ClientDestinationTest {

	@Test
	void clientReachesLoopbackHostName() throws Exception {
		String result = call("http://localhost:");
		assertThat(result).contains("Pong");
	}

	@Test
	void clientReachesLoopbackIpLiteral() throws Exception {
		String result = call("http://127.0.0.1:");
		assertThat(result).contains("Pong");
	}

	private String call(String hostPrefix) throws Exception {
		try (ServerFixture server = ServerFixture.start(new HttpComponentsMessageSender())) {
			WebServiceTemplate template = new WebServiceTemplate();
			template.setMessageSender(new HttpComponentsMessageSender());
			template.afterPropertiesSet();
			StringResult result = new StringResult();
			URI uri = new URI(hostPrefix + server.port() + "/");
			template.sendSourceAndReceiveToResult(uri.toString(), new StreamSource(
					new java.io.StringReader("<Ping xmlns=\"urn:bench\"/>")),
					new ActionCallback(new URI(WsaTestEndpoint.REPLY_ACTION)), result);
			return result.toString();
		}
	}

}
