package vtesting;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/**
 * The same untrusted payload must also finish through the R4B parser's own entry points.
 */
public class SecR4bDecompressionTests {

  @Test
  void emptyInputTerminates() throws Exception {
    assertTerminates("inflate_empty");
  }

  @Test
  void stalledStreamTerminates() throws Exception {
    assertTerminates("inflate_stalled");
  }

  @Test
  void stalledPayloadDecodeTerminates() throws Exception {
    assertTerminates("decode_stalled");
  }

  @Test
  void stalledPayloadFileParseTerminates() throws Exception {
    assertTerminates("parse_stalled");
  }

  private static void assertTerminates(String scenario) throws Exception {
    ProbeRunner.Result result = ProbeRunner.run(
        org.hl7.fhir.r4b.elementmodel.SHCParser.class, ProbeR4b.class, scenario);
    assertTrue(result.terminated,
        () -> "decoding did not finish within " + ProbeRunner.TIMEOUT_SECONDS + "s: " + result.output);
    assertEquals(0, result.exit,
        () -> "decoding crashed instead of ending as handled input: " + result.output);
  }
}
