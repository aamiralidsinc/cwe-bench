package vtesting;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.hl7.fhir.r4b.elementmodel.SHCParser;
import org.hl7.fhir.r4b.elementmodel.SHCParser.JWT;
import org.junit.jupiter.api.Test;

/**
 * Legitimate R4B cards must keep decoding exactly as they do today, including large ones.
 */
public class FuncR4bCardTests {

  @Test
  void completeCardStillDecodes() throws Exception {
    JWT jwt = parser().decodeJWT(compressedCard(Payloads.normalCardPayload()));
    assertEquals("normal", jwt.getPayload().get("marker").getAsString());
  }

  @Test
  void uncompressedCardStillDecodes() throws Exception {
    String token = Payloads.token(Payloads.plainHeader("none"),
        Payloads.utf8(Payloads.normalCardPayload()));
    JWT jwt = parser().decodeJWT(token);
    assertEquals("normal", jwt.getPayload().get("marker").getAsString());
  }

  @Test
  void largeCardStillDecodes() throws Exception {
    String token = compressedCard(Payloads.largeCardPayload());
    assertTrue(token.length() > 1195,
        "fixture defect: the encoded card must be larger than a QR-image sized limit");
    JWT jwt = parser().decodeJWT(token);
    assertEquals("large", jwt.getPayload().get("marker").getAsString());
  }

  private static String compressedCard(String payloadJson) {
    return Payloads.defToken(Payloads.completeDeflate(Payloads.utf8(payloadJson)));
  }

  private static SHCParser parser() {
    return new SHCParser(ContextsR4b.stub());
  }
}
