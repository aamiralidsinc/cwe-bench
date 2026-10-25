package wsbench.support;

import java.util.Iterator;

import org.springframework.ws.context.MessageContext;
import org.springframework.ws.soap.SoapHeaderElement;
import org.springframework.ws.soap.SoapMessage;
import org.springframework.ws.soap.security.AbstractWsSecurityInterceptor;
import org.springframework.ws.soap.security.WsSecurityValidationException;

/**
 * A small authentication interceptor: a request is accepted only when it carries the
 * authentication header. Rejected requests produce a client fault.
 */
public final class FirewallSecurityInterceptor extends AbstractWsSecurityInterceptor {

	public static final String AUTH_NAMESPACE = "urn:bench:auth";

	@Override
	protected void validateMessage(SoapMessage soapMessage, MessageContext messageContext)
			throws WsSecurityValidationException {
		boolean authenticated = false;
		if (soapMessage.getSoapHeader() != null) {
			Iterator<SoapHeaderElement> iterator = soapMessage.getSoapHeader().examineAllHeaderElements();
			while (iterator.hasNext()) {
				SoapHeaderElement element = iterator.next();
				if (AUTH_NAMESPACE.equals(element.getName().getNamespaceURI())) {
					authenticated = true;
				}
			}
		}
		if (!authenticated) {
			throw new NotAuthenticatedException("request is not authenticated");
		}
	}

	@Override
	protected void secureMessage(SoapMessage soapMessage, MessageContext messageContext) {
		// no outbound security in this fixture
	}

	@Override
	protected void cleanUp() {
	}

	/**
	 * Concrete validation exception for the fixture.
	 */
	public static final class NotAuthenticatedException extends WsSecurityValidationException {

		public NotAuthenticatedException(String message) {
			super(message);
		}

	}

}
