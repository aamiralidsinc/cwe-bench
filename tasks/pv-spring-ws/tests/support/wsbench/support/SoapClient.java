package wsbench.support;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.UUID;

/**
 * Sends a real HTTP SOAP request to the server, with optional WS-Addressing headers.
 */
public final class SoapClient {

	private static final String WSA = "http://schemas.xmlsoap.org/ws/2004/08/addressing";

	private static final String WSA10 = "http://www.w3.org/2005/08/addressing";

	public static final String ANONYMOUS = WSA + "/role/anonymous";

	public static final String NONE10 = WSA10 + "/none";

	public record Reply(int status, String body) {
	}

	private SoapClient() {
	}

	public static Reply reply(String url, String action, String replyTo, String faultTo) throws Exception {
		return post(url, UUID.randomUUID().toString(), action, replyTo, faultTo);
	}

	public static Reply replyWithoutMessageId(String url, String action, String replyTo, String faultTo)
			throws Exception {
		return post(url, null, action, replyTo, faultTo);
	}

	public static Reply noneReply(String url, String action) throws Exception {
		return post(url, WSA10, UUID.randomUUID().toString(), action, NONE10, NONE10);
	}

	public static Reply post(String url, String messageId, String action, String replyTo, String faultTo)
			throws Exception {
		return post(url, WSA, messageId, action, replyTo, faultTo);
	}

	private static Reply post(String url, String namespace, String messageId, String action, String replyTo,
			String faultTo) throws Exception {
		StringBuilder headers = new StringBuilder();
		if (messageId != null) {
			headers.append("<wsa:MessageID>urn:uuid:").append(messageId).append("</wsa:MessageID>");
		}
		headers.append("<wsa:Action>").append(escape(action)).append("</wsa:Action>");
		headers.append("<wsa:To>").append(escape(url)).append("</wsa:To>");
		if (replyTo != null) {
			headers.append("<wsa:ReplyTo><wsa:Address>").append(escape(replyTo))
				.append("</wsa:Address></wsa:ReplyTo>");
		}
		if (faultTo != null) {
			headers.append("<wsa:FaultTo><wsa:Address>").append(escape(faultTo))
				.append("</wsa:Address></wsa:FaultTo>");
		}
		String body = "<SOAP-ENV:Envelope xmlns:SOAP-ENV=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:wsa=\""
				+ namespace + "\"><SOAP-ENV:Header>" + headers
				+ "</SOAP-ENV:Header><SOAP-ENV:Body><b:Ping xmlns:b=\"urn:bench\"/></SOAP-ENV:Body></SOAP-ENV:Envelope>";
		HttpClient client = HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NEVER).build();
		HttpRequest request = HttpRequest.newBuilder(URI.create(url))
			.header("Content-Type", "text/xml; charset=utf-8")
			.header("SOAPAction", "\"\"")
			.POST(HttpRequest.BodyPublishers.ofString(body))
			.build();
		HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
		return new Reply(response.statusCode(), response.body());
	}

	private static String escape(String value) {
		return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;");
	}

}
