package vtesting;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/**
 * A tiny local LDAP endpoint used by the command-line tests. It reads the first request on
 * each connection (a BindRequest), records the name and simple password it carried, answers
 * the bind, and then closes the connection. Nothing leaves the machine and no directory is
 * needed: the test only asks whether a given bind shape was ever attempted.
 */
public final class RecordingLdapServer implements AutoCloseable {

	private final ServerSocket server;

	private final Thread acceptor;

	private final List<String[]> binds = Collections.synchronizedList(new ArrayList<>());

	private volatile boolean running = true;

	public RecordingLdapServer() throws IOException {
		this.server = new ServerSocket(0, 50, InetAddress.getByName("127.0.0.1"));
		this.acceptor = new Thread(this::acceptLoop, "recording-ldap");
		this.acceptor.setDaemon(true);
		this.acceptor.start();
	}

	public int port() {
		return this.server.getLocalPort();
	}

	public String url() {
		return "ldap://127.0.0.1:" + port();
	}

	public List<String[]> binds() {
		synchronized (this.binds) {
			return new ArrayList<>(this.binds);
		}
	}

	public boolean anyBindSeen() {
		return !binds().isEmpty();
	}

	/** True when a bind named a user and carried an absent or empty password. */
	public boolean badBindSeen() {
		for (String[] bind : binds()) {
			String name = bind[0];
			String password = bind[1];
			if (name != null && !name.isEmpty() && (password == null || password.isEmpty())) {
				return true;
			}
		}
		return false;
	}

	private void acceptLoop() {
		while (this.running) {
			try {
				Socket socket = this.server.accept();
				Thread worker = new Thread(() -> handle(socket), "recording-ldap-conn");
				worker.setDaemon(true);
				worker.start();
			}
			catch (IOException ex) {
				if (this.running) {
					continue;
				}
				return;
			}
		}
	}

	private void handle(Socket socket) {
		try (Socket s = socket) {
			s.setSoTimeout(30_000);
			InputStream in = s.getInputStream();
			OutputStream out = s.getOutputStream();
			Tlv message = readTlv(in);
			if (message == null || message.tag != 0x30) {
				return;
			}
			Cursor outer = new Cursor(message.value);
			Tlv messageId = outer.read();
			Tlv operation = outer.read();
			if (messageId == null || operation == null || operation.tag != 0x60) {
				return;
			}
			Cursor bind = new Cursor(operation.value);
			bind.read(); // version
			Tlv name = bind.read();
			Tlv authentication = bind.read();
			String dn = name == null ? "" : new String(name.value, java.nio.charset.StandardCharsets.UTF_8);
			String password = (authentication != null && authentication.tag == 0x80)
					? new String(authentication.value, java.nio.charset.StandardCharsets.UTF_8) : null;
			this.binds.add(new String[] { dn, password });
			out.write(bindSuccess(messageId.value));
			out.flush();
			// The next operation from the client will fail; the caller only needs the bind.
		}
		catch (IOException ex) {
			// The connection ending early is expected: the bind has already been recorded.
		}
	}

	private static byte[] bindSuccess(byte[] messageId) throws IOException {
		ByteArrayOutputStream response = new ByteArrayOutputStream();
		ByteArrayOutputStream result = new ByteArrayOutputStream();
		result.write(0x0a); // ENUMERATED
		result.write(1);
		result.write(0); // success
		result.write(0x04); // matchedDN
		result.write(0);
		result.write(0x04); // diagnosticMessage
		result.write(0);
		response.write(tlv(0x02, messageId));
		response.write(tlv(0x61, result.toByteArray()));
		return tlv(0x30, response.toByteArray());
	}

	private static Tlv readTlv(InputStream in) throws IOException {
		int tag = in.read();
		if (tag < 0) {
			return null;
		}
		int length = readLength(in);
		if (length < 0) {
			return null;
		}
		byte[] value = new byte[length];
		int offset = 0;
		while (offset < length) {
			int read = in.read(value, offset, length - offset);
			if (read < 0) {
				return null;
			}
			offset += read;
		}
		return new Tlv(tag, value);
	}

	private static int readLength(InputStream in) throws IOException {
		int first = in.read();
		if (first < 0) {
			return -1;
		}
		if (first < 0x80) {
			return first;
		}
		int octets = first & 0x7f;
		int length = 0;
		for (int i = 0; i < octets; i++) {
			int next = in.read();
			if (next < 0) {
				return -1;
			}
			length = (length << 8) | next;
		}
		return length;
	}

	private static byte[] tlv(int tag, byte[] value) throws IOException {
		ByteArrayOutputStream out = new ByteArrayOutputStream();
		out.write(tag);
		if (value.length < 0x80) {
			out.write(value.length);
		}
		else if (value.length < 0x100) {
			out.write(0x81);
			out.write(value.length);
		}
		else {
			out.write(0x82);
			out.write((value.length >> 8) & 0xff);
			out.write(value.length & 0xff);
		}
		out.write(value);
		return out.toByteArray();
	}

	@Override
	public void close() {
		this.running = false;
		try {
			this.server.close();
		}
		catch (IOException ex) {
			// closing the listener is best effort
		}
		this.acceptor.interrupt();
	}

	private static final class Tlv {

		final int tag;

		final byte[] value;

		Tlv(int tag, byte[] value) {
			this.tag = tag;
			this.value = value;
		}

		@Override
		public String toString() {
			return "Tlv{" + Integer.toHexString(this.tag) + ", " + Arrays.toString(this.value) + "}";
		}

	}

	private static final class Cursor {

		private final byte[] data;

		private int index;

		Cursor(byte[] data) {
			this.data = data;
		}

		Tlv read() {
			if (this.index >= this.data.length) {
				return null;
			}
			int tag = this.data[this.index++] & 0xff;
			int length = readLocalLength();
			if (length < 0 || this.index + length > this.data.length) {
				return null;
			}
			byte[] value = Arrays.copyOfRange(this.data, this.index, this.index + length);
			this.index += length;
			return new Tlv(tag, value);
		}

		private int readLocalLength() {
			if (this.index >= this.data.length) {
				return -1;
			}
			int first = this.data[this.index++] & 0xff;
			if (first < 0x80) {
				return first;
			}
			int octets = first & 0x7f;
			int length = 0;
			for (int i = 0; i < octets; i++) {
				if (this.index >= this.data.length) {
					return -1;
				}
				length = (length << 8) | (this.data[this.index++] & 0xff);
			}
			return length;
		}

	}

}
