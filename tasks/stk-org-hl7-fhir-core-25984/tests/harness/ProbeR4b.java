package vtesting;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;

/**
 * Child-process entry point for the R4B parser. Each run drives one real product entry point with
 * one attack payload and exits, so a decoder that never returns can be killed from the parent
 * without taking the test suite down.
 *
 * <p>Exit status 0 means the decode finished: it returned normally or raised an exception the
 * caller can handle (the product's normal invalid-input path). An uncaught {@link Error} ends the
 * JVM non-zero and is reported by the parent as a crash rather than a refusal.
 */
public final class ProbeR4b {
  private ProbeR4b() {
  }

  public static void main(String[] args) {
    try {
      run(args[0]);
    } catch (Exception handled) {
      // The product reports invalid input by throwing; that is a completed decode.
    }
    System.exit(0);
  }

  static void run(String scenario) throws Exception {
    switch (scenario) {
      case "inflate_empty":
        org.hl7.fhir.r4b.elementmodel.SHCParser.inflate(new byte[0]);
        break;

      case "inflate_stalled":
        org.hl7.fhir.r4b.elementmodel.SHCParser.inflate(
            Payloads.stalledStoredBlock(Payloads.utf8(Payloads.stalledCardPayload())));
        break;

      case "decode_stalled": {
        org.hl7.fhir.r4b.elementmodel.SHCParser parser =
            new org.hl7.fhir.r4b.elementmodel.SHCParser(ContextsR4b.stub());
        parser.decodeJWT(Payloads.defToken(
            Payloads.stalledStoredBlock(Payloads.utf8(Payloads.stalledCardPayload()))));
        break;
      }

      case "parse_stalled": {
        byte[] token = Payloads.defToken(
            Payloads.stalledStoredBlock(Payloads.utf8(Payloads.stalledCardPayload())))
            .getBytes(StandardCharsets.UTF_8);
        org.hl7.fhir.r4b.elementmodel.Manager.parse(ContextsR4b.stub(),
            new ByteArrayInputStream(token), org.hl7.fhir.r4b.elementmodel.Manager.FhirFormat.SHC);
        break;
      }

      default:
        throw new IllegalArgumentException("unknown scenario: " + scenario);
    }
  }
}
