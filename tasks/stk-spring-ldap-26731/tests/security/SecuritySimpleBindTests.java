package vtesting;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import org.springframework.ldap.core.AuthenticationSource;
import org.springframework.ldap.authentication.DefaultValuesAuthenticationSourceDecorator;
import org.springframework.ldap.core.LdapClient;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.query.LdapQueryBuilder;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.fail;

/**
 * Behavioural cases for a password-less bind through the default (simple) authentication
 * strategy and the public entry points that reach it.
 */
public class SecuritySimpleBindTests {

	private LdapContextSource contextSource;

	@BeforeEach
	public void setUp() {
		RecordingContextFactory.reset();
		this.contextSource = contextSource();
	}

	private static LdapContextSource contextSource() {
		LdapContextSource source = new LdapContextSource();
		source.setUrl("ldap://127.0.0.1:389");
		source.setContextFactory(RecordingContextFactory.class);
		source.afterPropertiesSet();
		return source;
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
	public void getContextWhenPrincipalIsSetAndPasswordIsEmptyThenRefused() {
		requireNamingFailure(() -> this.contextSource.getContext("cn=admin,dc=example,dc=com", ""));
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void getContextWhenPrincipalIsSetAndPasswordIsNullThenRefused() {
		requireNamingFailure(() -> this.contextSource.getContext("cn=admin,dc=example,dc=com", null));
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void getReadWriteContextWhenConfiguredPasswordIsEmptyThenRefused() {
		LdapContextSource source = new LdapContextSource();
		source.setUrl("ldap://127.0.0.1:389");
		source.setContextFactory(RecordingContextFactory.class);
		source.setUserDn("cn=admin,dc=example,dc=com");
		source.setPassword("");
		source.afterPropertiesSet();

		requireNamingFailure(source::getReadWriteContext);
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void ldapTemplateAuthenticateWhenPasswordIsEmptyThenReportsFailure() {
		LdapTemplate template = new LdapTemplate(this.contextSource);

		boolean success = template.authenticate("dc=example,dc=com", "(objectClass=person)", "");

		assertThat(success).isFalse();
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void ldapClientAuthenticateWhenNoPasswordIsSuppliedThenRefused() {
		LdapClient client = LdapClient.builder().contextSource(this.contextSource).build();

		requireNamingFailure(() -> client.authenticate()
			.query(LdapQueryBuilder.query().base("dc=example,dc=com").filter("(objectClass=person)"))
			.execute());
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void authenticationSourceSupplyingEmptyCredentialIsRefused() {
		LdapContextSource source = new LdapContextSource();
		source.setUrl("ldap://127.0.0.1:389");
		source.setContextFactory(RecordingContextFactory.class);
		AuthenticationSource target = new AuthenticationSource() {
			@Override
			public String getPrincipal() {
				return "cn=delegate,dc=example,dc=com";
			}

			@Override
			public String getCredentials() {
				return "";
			}
		};
		DefaultValuesAuthenticationSourceDecorator decorator = new DefaultValuesAuthenticationSourceDecorator(target,
				"cn=fallback,dc=example,dc=com", "fallback-secret");
		source.setAuthenticationSource(decorator);
		source.afterPropertiesSet();

		requireNamingFailure(source::getReadWriteContext);
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

}
