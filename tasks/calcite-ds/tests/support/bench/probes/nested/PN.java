package bench.probes.nested;

/** A denied class in a package that is denied by a package-prefix entry. */
class PN {
  static {
    try {
      java.nio.file.Files.write(
          java.nio.file.Path.of(System.getProperty("probe.dir", "/tmp/calcite-probes"), "PN"),
          new byte[] {1}, java.nio.file.StandardOpenOption.CREATE,
          java.nio.file.StandardOpenOption.APPEND);
    } catch (Throwable t) {
      // ignored
    }
  }
}
