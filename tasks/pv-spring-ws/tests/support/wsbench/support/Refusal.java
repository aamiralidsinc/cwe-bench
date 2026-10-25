package wsbench.support;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * The product's refusal form: the client sees an in-band SOAP fault or an HTTP client
 * error, and the out-of-band destination received nothing.
 */
public final class Refusal {

	private Refusal() {
	}

	public static void assertRefusedInBand(SoapClient.Reply reply) {
		boolean clientError = reply.status() >= 400 && reply.status() < 500;
		boolean soapFault = reply.body() != null && reply.body().contains("Fault");
		assertThat(clientError || soapFault)
			.as("request was refused in band (status %s, body %s)", reply.status(), reply.body())
			.isTrue();
	}

	public static void assertAcceptedInBand(SoapClient.Reply reply) {
		assertThat(reply.status()).as("in-band response status").isBetween(200, 299);
	}

}
