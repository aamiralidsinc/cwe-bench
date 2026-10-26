package vtesting;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.zip.Deflater;

/**
 * Builds the card payloads the suites use. Everything here is computed independently of the
 * product: a raw-DEFLATE stream is written by hand (stalled) or produced with java.util.zip
 * (complete), and the JWT compact serialization is assembled from its three base64url parts.
 */
public final class Payloads {
  private Payloads() {
  }

  public static final String DEF_HEADER = "{\"alg\":\"ES256\",\"zip\":\"DEF\"}";

  public static String plainHeader(String alg) {
    return "{\"alg\":\"" + alg + "\"}";
  }

  /**
   * A raw-DEFLATE non-final stored block carrying exactly {@code data}. The block is complete,
   * so every byte of {@code data} is produced, but no final block follows: a decoder that keeps
   * waiting for the stream to finish without noticing that no input remains spins forever.
   */
  public static byte[] stalledStoredBlock(byte[] data) {
    ByteArrayOutputStream out = new ByteArrayOutputStream(data.length + 5);
    out.write(0x00); // BFINAL=0, BTYPE=00 (stored block), padded to a byte boundary
    int n = data.length;
    out.write(n & 0xFF);
    out.write((n >>> 8) & 0xFF);
    int inv = (~n) & 0xFFFF;
    out.write(inv & 0xFF);
    out.write((inv >>> 8) & 0xFF);
    out.write(data, 0, n);
    return out.toByteArray();
  }

  /** A complete raw-DEFLATE stream (final block) of {@code data}. */
  public static byte[] completeDeflate(byte[] data) {
    Deflater d = new Deflater(Deflater.DEFAULT_COMPRESSION, true);
    try {
      d.setInput(data);
      d.finish();
      ByteArrayOutputStream out = new ByteArrayOutputStream();
      byte[] buf = new byte[4096];
      while (!d.finished()) {
        int n = d.deflate(buf);
        out.write(buf, 0, n);
      }
      return out.toByteArray();
    } finally {
      d.end();
    }
  }

  public static String b64(byte[] bytes) {
    return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
  }

  public static byte[] utf8(String s) {
    return s.getBytes(StandardCharsets.UTF_8);
  }

  /** Compact JWS serialization; the signature part is opaque to the decoder until it verifies. */
  public static String token(String headerJson, byte[] payloadBytes) {
    return b64(utf8(headerJson)) + "." + b64(payloadBytes) + "." + b64(new byte[] {0, 1, 2, 3});
  }

  public static String defToken(byte[] compressedPayload) {
    return token(DEF_HEADER, compressedPayload);
  }

  /** A payload the decoder can inflate and parse; carries no issuer, so nothing is fetched. */
  public static String stalledCardPayload() {
    return "{\"marker\":\"stalled\",\"nbf\":1}";
  }

  /** A payload the signature path can decompress and parse; carries an issuer. */
  public static String stalledSignedPayload() {
    return "{\"iss\":\"https://issuer.example/health\",\"marker\":\"signed\"}";
  }

  /** A large but legitimate card payload (the encoded card is well over any QR-image size). */
  public static String largeCardPayload() {
    return "{\"iss\":\"https://issuer.example/health\",\"nbf\":1600000000,\"marker\":\"large\","
        + "\"vc\":{\"type\":[\"https://smarthealth.cards#health-card\"],"
        + "\"credentialSubject\":{\"fhirVersion\":\"5.0.0\",\"fhirBundle\":{\"entry\":\""
        + incompressible(4000) + "\"}}}}";
  }

  /** Deterministic near-incompressible text, so the encoded card stays large too. */
  public static String incompressible(int length) {
    java.util.Random random = new java.util.Random(20261026L);
    String alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    StringBuilder out = new StringBuilder(length);
    for (int i = 0; i < length; i++) {
      out.append(alphabet.charAt(random.nextInt(alphabet.length())));
    }
    return out.toString();
  }

  public static String normalCardPayload() {
    return "{\"iss\":\"https://issuer.example/health\",\"nbf\":1600000000,\"marker\":\"normal\"}";
  }
}
