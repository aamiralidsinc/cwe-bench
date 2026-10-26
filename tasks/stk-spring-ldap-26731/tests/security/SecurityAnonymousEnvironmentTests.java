package vtesting;

import java.util.HashMap;
import java.util.Map;

import javax.naming.Context;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import org.springframework.ldap.core.support.LdapContextSource;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Behavioural cases where an application-supplied base environment names a user. The whole
 * environment is handed to the provider when the documented anonymous mode is used, so the
 * strategy is never consulted.
 */
public class SecurityAnonymousEnvironmentTests {

	@BeforeEach
	public void setUp() {
		RecordingContextFactory.reset();
	}

	private static LdapContextSource source(Map<String, Object> base) {
		LdapContextSource source = new LdapContextSource();
		source.setUrl("ldap://127.0.0.1:389");
		source.setContextFactory(RecordingContextFactory.class);
		source.setUserDn("");
		source.setPassword("");
		source.setBaseEnvironmentProperties(base);
		source.afterPropertiesSet();
		return source;
	}

	@Test
	public void baseEnvironmentWithPrincipalAndEmptyPasswordIsRefused() {
		Map<String, Object> base = new HashMap<>();
		base.put(Context.SECURITY_PRINCIPAL, "cn=admin,dc=example,dc=com");
		base.put(Context.SECURITY_CREDENTIALS, "");
		try {
			source(base).getReadOnlyContext();
		}
		catch (org.springframework.ldap.NamingException expected) {
			// refused, at construction time or at context creation
		}
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void baseEnvironmentWithPrincipalAndNoCredentialsIsRefused() {
		Map<String, Object> base = new HashMap<>();
		base.put(Context.SECURITY_PRINCIPAL, "cn=admin,dc=example,dc=com");
		try {
			source(base).getReadOnlyContext();
		}
		catch (org.springframework.ldap.NamingException expected) {
			// refused, at construction time or at context creation
		}
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

}
