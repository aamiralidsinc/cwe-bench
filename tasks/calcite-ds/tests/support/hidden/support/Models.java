package hidden.support;

import org.apache.calcite.jdbc.CalciteConnection;
import org.apache.calcite.schema.SchemaPlus;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.Properties;

/** Helpers shared by the hidden model-loading suites. */
public final class Models {
  private Models() {}

  public static Path probeDir() {
    return Path.of(System.getProperty("probe.dir", "/tmp/calcite-probes"));
  }

  public static void clearMarker(String name) throws IOException {
    Files.deleteIfExists(probeDir().resolve(name));
  }

  public static boolean marker(String name) {
    return Files.exists(probeDir().resolve(name));
  }

  /** Builds the value of the jdbc "model" property from YAML lines. */
  public static String inline(String... lines) {
    StringBuilder b = new StringBuilder("inline:\n");
    for (String line : lines) {
      b.append(line).append('\n');
    }
    return b.toString();
  }

  public static Connection connect(String model) throws SQLException {
    final Properties info = new Properties();
    info.setProperty("model", model);
    return DriverManager.getConnection("jdbc:calcite:", info);
  }

  public static SchemaPlus root(Connection connection) throws SQLException {
    return connection.unwrap(CalciteConnection.class).getRootSchema();
  }
}
