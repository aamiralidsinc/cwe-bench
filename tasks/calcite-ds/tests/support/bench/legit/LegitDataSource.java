package bench.legit;

import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.SQLFeatureNotSupportedException;
import java.util.logging.Logger;
import javax.sql.DataSource;

/** Allowed data source backed by the in-memory HSQLDB driver. */
public class LegitDataSource implements DataSource {
  private final String url;

  public LegitDataSource() {
    this("jdbc:hsqldb:mem:calcite_legit");
  }

  public LegitDataSource(String url) {
    this.url = url;
  }

  @Override public Connection getConnection() throws SQLException {
    return DriverManager.getConnection(url, "SA", "");
  }

  @Override public Connection getConnection(String username, String password)
      throws SQLException {
    return DriverManager.getConnection(url, username, password);
  }

  @Override public PrintWriter getLogWriter() {
    return null;
  }

  @Override public void setLogWriter(PrintWriter out) {
  }

  @Override public void setLoginTimeout(int seconds) {
  }

  @Override public int getLoginTimeout() {
    return 0;
  }

  @Override public Logger getParentLogger() throws SQLFeatureNotSupportedException {
    throw new SQLFeatureNotSupportedException();
  }

  @Override public <T> T unwrap(Class<T> iface) throws SQLException {
    if (iface.isInstance(this)) {
      return iface.cast(this);
    }
    throw new SQLException("not a wrapper for " + iface);
  }

  @Override public boolean isWrapperFor(Class<?> iface) {
    return iface.isInstance(this);
  }
}
