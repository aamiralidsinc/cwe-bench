package vtesting;

import java.util.HashMap;
import java.util.Map;

import javax.naming.Context;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import org.springframework.ldap.core.AuthenticationSource;
import org.springframework.ldap.authentication.DefaultValuesAuthenticationSourceDecorator;
import org.springframework.ldap.core.LdapClient;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.DefaultTlsDirContextAuthenticationStrategy;
import org.springframework.ldap.core.support.DigestMd5DirContextAuthenticationStrategy;
import org.springframework.ldap.core.support.ExternalTlsDirContextAuthenticationStrategy;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.query.LdapQueryBuilder;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Legitimate sign-in paths that must keep working: real credentials, the documented
 * anonymous mode, and mechanisms that authenticate without a password.
 */
public class FunctionalAuthenticationTests {

	@BeforeEach
	public void setUp() {
		RecordingContextFactory.reset();
	}

	private static LdapContextSource contextSource() {
		LdapContextSource source = new LdapContextSource();
		source.setUrl("ldap://127.0.0.1:389");
		source.setContextFactory(RecordingContextFactory.class);
		source.afterPropertiesSet();
		return source;
	}

	@Test
	public void simpleBindWithPasswordStillWorks() throws Exception {
		LdapContextSource source = contextSource();

		source.getContext("cn=admin,dc=example,dc=com", "secret").close();

		Map<String, Object> bind = RecordingContextFactory.firstBindWith("cn=admin,dc=example,dc=com");
		assertThat(bind).isNotNull();
		assertThat(bind.get(Context.SECURITY_CREDENTIALS)).isEqualTo("secret");
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void documentedAnonymousReadOnlyModeStillWorks() {
		LdapContextSource source = new LdapContextSource();
		source.setUrl("ldap://127.0.0.1:389");
		source.setContextFactory(RecordingContextFactory.class);
		source.setUserDn("");
		source.setPassword("");
		source.afterPropertiesSet();

		assertThat(source.getReadOnlyContext()).isNotNull();

		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void unrelatedBaseEnvironmentPropertiesStillWork() {
		LdapContextSource source = new LdapContextSource();
		source.setUrl("ldap://127.0.0.1:389");
		source.setContextFactory(RecordingContextFactory.class);
		source.setUserDn("");
		source.setPassword("");
		Map<String, Object> base = new HashMap<>();
		base.put("com.example.connection.tag", "primary");
		source.setBaseEnvironmentProperties(base);
		source.afterPropertiesSet();

		assertThat(source.getReadOnlyContext()).isNotNull();

		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void digestBindWithPasswordStillWorks() throws Exception {
		LdapContextSource source = new LdapContextSource();
		source.setUrl("ldap://127.0.0.1:389");
		source.setContextFactory(RecordingContextFactory.class);
		source.setAuthenticationStrategy(new DigestMd5DirContextAuthenticationStrategy());
		source.afterPropertiesSet();

		source.getContext("cn=admin", "secret").close();

		Map<String, Object> bind = RecordingContextFactory.firstBindWith("cn=admin");
		assertThat(bind).isNotNull();
		assertThat(bind.get(Context.SECURITY_CREDENTIALS)).isEqualTo("secret");
		assertThat(bind.get(Context.SECURITY_AUTHENTICATION)).isEqualTo("DIGEST-MD5");
	}

	@Test
	public void tlsBindWithPasswordStillWorks() {
		LdapContextSource source = new LdapContextSource();
		source.setUrl("ldap://127.0.0.1:389");
		source.setContextFactory(RecordingContextFactory.class);
		source.setAuthenticationStrategy(new DefaultTlsDirContextAuthenticationStrategy());
		source.afterPropertiesSet();

		assertThat(source.getContext("cn=admin,dc=example,dc=com", "secret")).isNotNull();

		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void externalTlsAuthenticationWithoutPasswordStillWorks() {
		LdapContextSource source = new LdapContextSource();
		source.setUrl("ldap://127.0.0.1:389");
		source.setContextFactory(RecordingContextFactory.class);
		source.setAuthenticationStrategy(new ExternalTlsDirContextAuthenticationStrategy());
		source.afterPropertiesSet();

		assertThat(source.getContext("cn=service,dc=example,dc=com", "")).isNotNull();

		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void ldapTemplateAuthenticationWithPasswordStillWorks() {
		LdapTemplate template = new LdapTemplate(contextSource());

		boolean success = template.authenticate("dc=example,dc=com", "(objectClass=person)", "secret");

		assertThat(success).isTrue();
		assertThat(RecordingContextFactory.binds())
			.anyMatch((bind) -> "secret".equals(bind.get(Context.SECURITY_CREDENTIALS)));
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void ldapClientAuthenticationWithPasswordStillWorks() {
		LdapClient client = LdapClient.builder().contextSource(contextSource()).build();

		client.authenticate()
			.query(LdapQueryBuilder.query().base("dc=example,dc=com").filter("(objectClass=person)"))
			.password("secret")
			.execute();

		assertThat(RecordingContextFactory.binds())
			.anyMatch((bind) -> "secret".equals(bind.get(Context.SECURITY_CREDENTIALS)));
		assertThat(RecordingContextFactory.badBindSeen()).isFalse();
	}

	@Test
	public void authenticationSourceDefaultsStillWork() throws Exception {
		LdapContextSource source = new LdapContextSource();
		source.setUrl("ldap://127.0.0.1:389");
		source.setContextFactory(RecordingContextFactory.class);
		AuthenticationSource target = new AuthenticationSource() {
			@Override
			public String getPrincipal() {
				return "";
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

		source.getReadWriteContext().close();

		Map<String, Object> bind = RecordingContextFactory.firstBindWith("cn=fallback,dc=example,dc=com");
		assertThat(bind).isNotNull();
		assertThat(bind.get(Context.SECURITY_CREDENTIALS)).isEqualTo("fallback-secret");
	}

}
