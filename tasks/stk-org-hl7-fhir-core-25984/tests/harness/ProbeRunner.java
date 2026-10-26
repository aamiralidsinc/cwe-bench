package vtesting;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.security.CodeSource;
import java.util.LinkedHashSet;
import java.util.concurrent.TimeUnit;

/**
 * Runs one scenario from a probe class in a separate JVM and reports whether it finished.
 *
 * <p>The child gets the same classpath as the test JVM. Surefire may hand the forked JVM a
 * manifest-only booter jar, so the anchor classes' own code sources are added explicitly; this
 * keeps the child able to load the product classes under either surefire mode.
 */
public final class ProbeRunner {
  private ProbeRunner() {
  }

  public static final int TIMEOUT_SECONDS = 30;

  public static final class Result {
    public final boolean terminated;
    public final int exit;
    public final String output;

    Result(boolean terminated, int exit, String output) {
      this.terminated = terminated;
      this.exit = exit;
      this.output = output;
    }
  }

  public static Result run(Class<?> productAnchor, Class<?> probeClass, String scenario)
      throws Exception {
    String java = System.getProperty("java.home") + File.separator + "bin" + File.separator + "java";
    ProcessBuilder pb = new ProcessBuilder(
        java, "-cp", classpath(productAnchor, probeClass), probeClass.getName(), scenario);
    pb.redirectErrorStream(true);
    Process process = pb.start();

    ByteArrayOutputStream captured = new ByteArrayOutputStream();
    Thread reader = new Thread(() -> {
      try (InputStream in = process.getInputStream()) {
        byte[] buf = new byte[4096];
        int n;
        while ((n = in.read(buf)) > 0) {
          captured.write(buf, 0, n);
        }
      } catch (Exception ignored) {
        // The process was killed while reading; the parent's verdict does not depend on this.
      }
    }, "probe-reader");
    reader.setDaemon(true);
    reader.start();

    boolean done = process.waitFor(TIMEOUT_SECONDS, TimeUnit.SECONDS);
    if (!done) {
      process.destroyForcibly();
      process.waitFor(10, TimeUnit.SECONDS);
    }
    reader.join(2000);
    String output;
    synchronized (captured) {
      output = captured.toString(StandardCharsets.UTF_8);
    }
    return new Result(done, done ? process.exitValue() : -1, output);
  }

  private static String classpath(Class<?> productAnchor, Class<?> probeClass) {
    LinkedHashSet<String> parts = new LinkedHashSet<>();
    addCodeSource(parts, probeClass);
    addCodeSource(parts, productAnchor);
    for (String key : new String[] {"surefire.test.class.path", "java.class.path"}) {
      String value = System.getProperty(key);
      if (value == null || value.isEmpty()) {
        continue;
      }
      for (String entry : value.split(File.pathSeparator)) {
        if (!entry.isEmpty()) {
          parts.add(entry);
        }
      }
    }
    return String.join(File.pathSeparator, parts);
  }

  private static void addCodeSource(LinkedHashSet<String> parts, Class<?> type) {
    try {
      CodeSource source = type.getProtectionDomain().getCodeSource();
      if (source != null && source.getLocation() != null) {
        parts.add(new File(source.getLocation().toURI()).getAbsolutePath());
      }
    } catch (URISyntaxException ignored) {
      // No code source (e.g. a bootstrap class); the classpath properties still cover it.
    }
  }
}
