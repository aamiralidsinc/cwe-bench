package vtesting;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import javax.naming.Binding;
import javax.naming.Context;
import javax.naming.Name;
import javax.naming.NamingEnumeration;
import javax.naming.NamingException;
import javax.naming.directory.BasicAttributes;
import javax.naming.directory.DirContext;
import javax.naming.directory.SearchResult;
import javax.naming.ldap.LdapContext;
import javax.naming.ldap.StartTlsResponse;
import javax.naming.spi.InitialContextFactory;
import javax.net.ssl.SSLSession;
import javax.net.ssl.SSLSocketFactory;

import org.springframework.ldap.core.DirContextAdapter;
import org.springframework.ldap.support.LdapUtils;

/**
 * A JNDI initial context factory used by the behavioural tests. Instead of contacting a
 * directory it records the environment of every context creation and every server-triggering
 * lookup, so the test can tell whether a bind request with a given identity/password shape
 * was ever attempted.
 */
public class RecordingContextFactory implements InitialContextFactory {

	public static final String ENTRY_DN = "cn=john doe,dc=example,dc=com";

	private static final List<Map<String, Object>> BINDS = Collections.synchronizedList(new ArrayList<>());

	public static void reset() {
		BINDS.clear();
	}

	public static List<Map<String, Object>> binds() {
		synchronized (BINDS) {
			return new ArrayList<>(BINDS);
		}
	}

	/** True when some attempted bind names a user but carries no password. */
	public static boolean badBindSeen() {
		for (Map<String, Object> env : binds()) {
			if (isBadPair(env.get(Context.SECURITY_PRINCIPAL), env.get(Context.SECURITY_CREDENTIALS))) {
				return true;
			}
		}
		return false;
	}

	public static boolean isBadPair(Object principal, Object credentials) {
		if (!(principal instanceof String) || ((String) principal).isEmpty()) {
			return false;
		}
		return credentials == null || (credentials instanceof String && ((String) credentials).isEmpty());
	}

	public static Map<String, Object> firstBindWith(String principal) {
		for (Map<String, Object> env : binds()) {
			if (principal.equals(env.get(Context.SECURITY_PRINCIPAL))) {
				return env;
			}
		}
		return null;
	}

	@Override
	public Context getInitialContext(Hashtable<?, ?> environment) throws NamingException {
		Hashtable<String, Object> env = new Hashtable<>();
		for (Map.Entry<?, ?> entry : environment.entrySet()) {
			env.put(String.valueOf(entry.getKey()), entry.getValue());
		}
		BINDS.add(Collections.unmodifiableMap(new Hashtable<>(env)));
		return (Context) Proxy.newProxyInstance(RecordingContextFactory.class.getClassLoader(),
				new Class<?>[] { LdapContext.class }, new RecordingHandler(env));
	}

	private static final class RecordingHandler implements InvocationHandler {

		private final Hashtable<String, Object> env;

		RecordingHandler(Hashtable<String, Object> env) {
			this.env = env;
		}

		@Override
		public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
			switch (method.getName()) {
				case "getEnvironment":
					return new Hashtable<>(this.env);
				case "addToEnvironment":
					return this.env.put((String) args[0], args[1]);
				case "removeFromEnvironment":
					return this.env.remove((String) args[0]);
				case "lookup":
				case "lookupLink":
					// The TLS strategies force a server call after updating the environment.
					BINDS.add(Collections.unmodifiableMap(new Hashtable<>(this.env)));
					return null;
				case "search":
					return searchResult();
				case "extendedOperation":
					return new NoOpStartTlsResponse();
				case "getNameInNamespace":
					return "";
				case "toString":
					return "RecordingLdapContext";
				case "hashCode":
					return System.identityHashCode(proxy);
				case "equals":
					return proxy == args[0];
				case "close":
					return null;
				default:
					return defaultValue(method.getReturnType());
			}
		}

		private NamingEnumeration<SearchResult> searchResult() {
			DirContextAdapter adapter = new DirContextAdapter(new BasicAttributes(true),
					LdapUtils.newLdapName("cn=john doe"), LdapUtils.newLdapName(ENTRY_DN));
			SearchResult result = new SearchResult("cn=john doe", adapter, new BasicAttributes(true));
			return new ListEnumeration<>(List.<SearchResult>of(result).iterator());
		}

	}

	private static Object defaultValue(Class<?> type) {
		if (!type.isPrimitive()) {
			return null;
		}
		if (type == boolean.class) {
			return false;
		}
		if (type == char.class) {
			return '\0';
		}
		if (type == byte.class) {
			return (byte) 0;
		}
		if (type == short.class) {
			return (short) 0;
		}
		if (type == int.class) {
			return 0;
		}
		if (type == long.class) {
			return 0L;
		}
		if (type == float.class) {
			return 0f;
		}
		return 0d;
	}

	private static final class ListEnumeration<T> implements NamingEnumeration<T> {

		private final Iterator<T> iterator;

		ListEnumeration(Iterator<T> iterator) {
			this.iterator = iterator;
		}

		@Override
		public T next() {
			return this.iterator.next();
		}

		@Override
		public boolean hasMore() {
			return this.iterator.hasNext();
		}

		@Override
		public void close() {
		}

		@Override
		public T nextElement() {
			return this.iterator.next();
		}

		@Override
		public boolean hasMoreElements() {
			return this.iterator.hasNext();
		}

	}

	static final class NoOpStartTlsResponse extends StartTlsResponse {

		@Override
		public SSLSession negotiate() {
			return null;
		}

		@Override
		public SSLSession negotiate(SSLSocketFactory factory) {
			return null;
		}

		@Override
		public void setHostnameVerifier(javax.net.ssl.HostnameVerifier verifier) {
		}

		@Override
		public void setEnabledCipherSuites(String[] suites) {
		}

		@Override
		public void close() {
		}

	}

}
