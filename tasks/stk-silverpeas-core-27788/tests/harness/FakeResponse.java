package silverpeas.hidden;

import javax.servlet.ServletOutputStream;
import javax.servlet.WriteListener;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletResponse;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Locale;

/** A response that records the status, the headers and the bytes written to the client. */
public final class FakeResponse implements HttpServletResponse {

  private final ByteArrayOutputStream bytes = new ByteArrayOutputStream();
  private final ServletOutputStream stream = new ServletOutputStream() {
    @Override
    public boolean isReady() {
      return true;
    }

    @Override
    public void setWriteListener(WriteListener writeListener) {
    }

    @Override
    public void write(int b) {
      bytes.write(b);
    }
  };
  private final List<String> headers = new ArrayList<>();
  private int status = 200;
  private String redirect;
  private boolean forwarded;
  private Throwable thrown;
  private String contentType;
  private String encoding = "UTF-8";
  private long contentLength = -1;
  private PrintWriter writer;

  void setThrown(Throwable t) {
    this.thrown = t;
  }

  Throwable thrown() {
    return thrown;
  }

  void markForwarded() {
    this.forwarded = true;
  }

  boolean isForwarded() {
    return forwarded;
  }

  String redirect() {
    return redirect;
  }

  String body() {
    if (writer != null) {
      writer.flush();
    }
    return new String(bytes.toByteArray(), StandardCharsets.UTF_8);
  }

  int status() {
    return status;
  }

  @Override
  public int getStatus() {
    return status;
  }

  @Override
  public void setStatus(int sc) {
    this.status = sc;
  }

  @Override
  public void setStatus(int sc, String sm) {
    this.status = sc;
  }

  @Override
  public void sendError(int sc) {
    this.status = sc;
  }

  @Override
  public void sendError(int sc, String msg) {
    this.status = sc;
  }

  @Override
  public void sendRedirect(String location) throws IOException {
    this.redirect = location;
    this.status = 302;
  }

  @Override
  public void setHeader(String name, String value) {
    headers.add(name + ": " + value);
  }

  @Override
  public void addHeader(String name, String value) {
    headers.add(name + ": " + value);
  }

  @Override
  public void setIntHeader(String name, int value) {
    headers.add(name + ": " + value);
  }

  @Override
  public void addIntHeader(String name, int value) {
    headers.add(name + ": " + value);
  }

  @Override
  public void setDateHeader(String name, long date) {
    headers.add(name + ": " + date);
  }

  @Override
  public void addDateHeader(String name, long date) {
    headers.add(name + ": " + date);
  }

  @Override
  public boolean containsHeader(String name) {
    for (String h : headers) {
      if (h.startsWith(name + ":")) {
        return true;
      }
    }
    return false;
  }

  @Override
  public String getHeader(String name) {
    for (String h : headers) {
      if (h.startsWith(name + ":")) {
        return h.substring(name.length() + 1).trim();
      }
    }
    return null;
  }

  @Override
  public Collection<String> getHeaders(String name) {
    List<String> out = new ArrayList<>();
    for (String h : headers) {
      if (h.startsWith(name + ":")) {
        out.add(h.substring(name.length() + 1).trim());
      }
    }
    return out;
  }

  @Override
  public Collection<String> getHeaderNames() {
    List<String> out = new ArrayList<>();
    for (String h : headers) {
      out.add(h.substring(0, h.indexOf(':')));
    }
    return out;
  }

  @Override
  public String encodeURL(String url) {
    return url;
  }

  @Override
  public String encodeRedirectURL(String url) {
    return url;
  }

  @Override
  @SuppressWarnings("deprecation")
  public String encodeUrl(String url) {
    return url;
  }

  @Override
  @SuppressWarnings("deprecation")
  public String encodeRedirectUrl(String url) {
    return url;
  }

  @Override
  public void addCookie(Cookie cookie) {
  }

  @Override
  public void setContentType(String type) {
    this.contentType = type;
  }

  @Override
  public String getContentType() {
    return contentType;
  }

  @Override
  public void setCharacterEncoding(String charset) {
    this.encoding = charset;
  }

  @Override
  public String getCharacterEncoding() {
    return encoding;
  }

  @Override
  public void setContentLength(int len) {
    this.contentLength = len;
  }

  @Override
  public void setContentLengthLong(long len) {
    this.contentLength = len;
  }

  @Override
  public ServletOutputStream getOutputStream() {
    return stream;
  }

  @Override
  public PrintWriter getWriter() {
    if (writer == null) {
      writer = new PrintWriter(bytes, true, StandardCharsets.UTF_8);
    }
    return writer;
  }

  @Override
  public void setBufferSize(int size) {
  }

  @Override
  public int getBufferSize() {
    return 8192;
  }

  @Override
  public void flushBuffer() {
  }

  @Override
  public void resetBuffer() {
    bytes.reset();
  }

  @Override
  public boolean isCommitted() {
    return false;
  }

  @Override
  public void reset() {
    bytes.reset();
    status = 200;
  }

  @Override
  public void setLocale(Locale loc) {
  }

  @Override
  public Locale getLocale() {
    return Locale.ROOT;
  }
}
