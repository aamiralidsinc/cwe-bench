package vtesting;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.hl7.fhir.r5.elementmodel.SHCParser;
import org.hl7.fhir.r5.elementmodel.SHCParser.JWT;
import org.hl7.fhir.utilities.json.model.JsonObject;
import org.hl7.fhir.utilities.json.parser.JsonParser;
import org.junit.jupiter.api.Test;

/**
 * Legitimate cards must keep decoding exactly as they do today: complete compressed cards,
 * cards without compression, cards that carry an issuer (so the signature path runs), and cards
 * whose encoded or decoded content is legitimately large.
 */
public class FuncR5CardTests {

  @Test
  void completeCardStillDecodes() throws Exception {
    JWT jwt = parser().decodeJWT(null, compressedCard(Payloads.normalCardPayload()));
    assertEquals("normal", jwt.getPayload().asString("marker"));
  }

  @Test
  void uncompressedCardStillDecodes() throws Exception {
    String token = Payloads.token(Payloads.plainHeader("none"),
        Payloads.utf8(Payloads.normalCardPayload()));
    JWT jwt = parser().decodeJWT(null, token);
    assertEquals("normal", jwt.getPayload().asString("marker"));
  }

  @Test
  void compressedCardWithoutIssuerStillDecodes() throws Exception {
    String payload = "{\"marker\":\"plain\",\"nbf\":1}";
    JWT jwt = parser().decodeJWT(null, compressedCard(payload));
    assertEquals("plain", jwt.getPayload().asString("marker"));
  }

  @Test
  void largeCardStillDecodes() throws Exception {
    String token = compressedCard(Payloads.largeCardPayload());
    assertTrue(token.length() > 1195,
        "fixture defect: the encoded card must be larger than a QR-image sized limit");
    JWT jwt = parser().decodeJWT(null, token);
    assertEquals("large", jwt.getPayload().asString("marker"));
    assertTrue(jwt.getPayloadSrc().length > 1500,
        "the decoded payload must survive intact, not be truncated");
  }

  @Test
  void issuerBearingCardStillDecodes() throws Exception {
    // An issuer sends the decoded payload through the signature path as well; the card still has
    // to decode when the key set is empty.
    JsonObject payload = parser()
        .decodeJWT(null, compressedCard(Payloads.normalCardPayload())).getPayload();
    assertEquals("normal", payload.asString("marker"));
    assertEquals("https://issuer.example/health", payload.asString("iss"));
  }

  private static String compressedCard(String payloadJson) {
    return Payloads.defToken(Payloads.completeDeflate(Payloads.utf8(payloadJson)));
  }

  private static SHCParser parser() {
    SHCParser parser = new SHCParser(ContextsR5.stub());
    parser.setSignatureServices(
        new org.hl7.fhir.utilities.validation.IDigitalSignatureServices() {
          @Override
          public JsonObject fetchJWKS(String address)
              throws org.hl7.fhir.utilities.json.JsonException, java.io.IOException {
            return JsonParser.parseObject("{\"keys\":[]}");
          }
        });
    return parser;
  }
}
