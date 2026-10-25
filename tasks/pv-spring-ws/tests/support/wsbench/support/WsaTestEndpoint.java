package wsbench.support;

import java.io.StringReader;
import java.util.Locale;

import javax.xml.transform.TransformerFactory;
import javax.xml.transform.stream.StreamSource;

import org.springframework.ws.context.MessageContext;
import org.springframework.ws.server.endpoint.annotation.Endpoint;
import org.springframework.ws.soap.SoapMessage;
import org.springframework.ws.soap.addressing.server.annotation.Action;

/**
 * Endpoint used by the behaviour tests. Two actions: one writes an ordinary reply
 * payload, the other produces a server-side fault.
 */
@Endpoint
public class WsaTestEndpoint {

	public static final String REPLY_ACTION = "urn:bench:reply";

	public static final String FAULT_ACTION = "urn:bench:fault";

	@Action(REPLY_ACTION)
	public void reply(MessageContext messageContext) throws Exception {
		SoapMessage response = (SoapMessage) messageContext.getResponse();
		StreamSource source = new StreamSource(new StringReader("<Pong xmlns=\"urn:bench\">ok</Pong>"));
		TransformerFactory.newInstance().newTransformer().transform(source, response.getSoapBody().getPayloadResult());
	}

	@Action(FAULT_ACTION)
	public void fault(MessageContext messageContext) {
		SoapMessage response = (SoapMessage) messageContext.getResponse();
		response.getSoapBody().addServerOrReceiverFault("bench failure", Locale.ENGLISH);
	}

}
