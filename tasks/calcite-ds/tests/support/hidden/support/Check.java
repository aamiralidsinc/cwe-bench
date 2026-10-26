package hidden.support;

/** Small assertion helper used by the plain-Java hidden suites. */
public final class Check {
  private Check() {}

  public static void that(boolean condition, String message) {
    if (!condition) {
      throw new AssertionError(message);
    }
  }

  public static void notNull(Object value, String message) {
    that(value != null, message);
  }

  public static void equal(Object expected, Object actual, String message) {
    if (expected == null ? actual != null : !expected.equals(actual)) {
      throw new AssertionError(message + " (expected " + expected + ", got " + actual + ")");
    }
  }
}
