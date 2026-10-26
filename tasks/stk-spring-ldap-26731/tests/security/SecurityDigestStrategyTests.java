package vtesting;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import org.springframework.ldap.core.support.DigestMd5DirContextAuthenticationStrategy;
import org.springframework.ldap.core.support.LdapContextSource;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.fail;

/**
 * Behavioural cases for the DIGEST-MD5 strategy, which is wired explicitly by applications.
 */
public class SecurityDigestStrategyTests {

	private LdapContextSource contextSource;

	@BeforeEach
	public void setUp() {
		RecordingContextFactory.reset();
		this.contextSource = new LdapContextSource();
		this.contextSource.setUrl("ldap://127.0.0.1:389");
		this.contextSource.setContextFactory(RecordingContextFactory.class);
		this.contextSource.setAuthenticationStrategy(new DigestMd5DirContextAuthenticationStrategy());
		this.contextSource.afterPropertiesSet();
	}

	private static void requireNamingFailure(Runnable action) {
		try {
			action.run();
			fail("the bind should have been refused");
		}
		catch (org.springframework.ldap.NamingException expected) {
			// the library's authentication failure form
		}
	}

	@Test
	public void digestAuthenticationWithPrincipalAndEmptyPasswordIsRefused() {
		requireNamingFailure(() -> this.contextSource.getContext("cn=admin,dc=example,dc=com", ""));
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void digestAuthenticationWithPrincipalAndNullPasswordIsRefused() {
		requireNamingFailure(() -> this.contextSource.getContext("cn=admin,dc=example,dc=com", null));
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

}
