package vtesting;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/**
 * A card that carries an issuer is decompressed a second time while its signature is checked.
 * That decode must also finish in bounded work for a payload that stops advancing.
 */
public class SecR5SignatureTests {

  @Test
  void stalledPayloadSignatureCheckTerminates() throws Exception {
    ProbeRunner.Result result = ProbeRunner.run(
        org.hl7.fhir.r5.elementmodel.SHCParser.class, ProbeR5.class, "signature_stalled");
    assertTrue(result.terminated,
        () -> "signature checking did not finish within " + ProbeRunner.TIMEOUT_SECONDS
            + "s: " + result.output);
    assertEquals(0, result.exit,
        () -> "signature checking crashed instead of ending as handled input: " + result.output);
  }
}
