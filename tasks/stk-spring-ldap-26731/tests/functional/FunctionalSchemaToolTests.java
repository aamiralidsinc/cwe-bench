package vtesting;

import java.io.File;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Legitimate uses of the schema code-generation command: anonymous and with real
 * credentials.
 */
public class FunctionalSchemaToolTests {

	private RecordingLdapServer server;

	@BeforeEach
	public void setUp() throws Exception {
		this.server = new RecordingLdapServer();
	}

	@AfterEach
	public void tearDown() {
		this.server.close();
	}

	private boolean runTool(Path output, String... extra) throws Exception {
		String java = Path.of(System.getProperty("java.home"), "bin", "java").toString();
		List<String> command = new ArrayList<>();
		command.add(java);
		command.add("-cp");
		command.add(System.getProperty("java.class.path"));
		command.add("org.springframework.ldap.odm.tools.SchemaToJava");
		command.add("-l");
		command.add(this.server.url());
		command.add("-c");
		command.add("Person");
		command.add("-k");
		command.add("vtesting.generated");
		command.add("-o");
		command.add("organizationalperson");
		command.add("-t");
		command.add(output.toString());
		for (String value : extra) {
			command.add(value);
		}
		Process process = new ProcessBuilder(command).redirectErrorStream(true)
			.redirectOutput(new File(output.toFile(), "tool.log"))
			.start();
		if (!process.waitFor(90, TimeUnit.SECONDS)) {
			process.destroyForcibly();
			return false;
		}
		return true;
	}

	@Test
	public void anonymousSchemaReadStillWorks(@TempDir Path output) throws Exception {
		assertThat(runTool(output)).isTrue();

		assertThat(this.server.anyBindSeen()).isTrue();
		assertThat(this.server.badBindSeen()).isFalse();
	}

	@Test
	public void blankUserNameSchemaReadStillWorks(@TempDir Path output) throws Exception {
		assertThat(runTool(output, "-u", "")).isTrue();

		assertThat(this.server.anyBindSeen()).isTrue();
		assertThat(this.server.badBindSeen()).isFalse();
	}

	@Test
	public void schemaReadWithRealCredentialsStillWorks(@TempDir Path output) throws Exception {
		assertThat(runTool(output, "-u", "cn=admin,dc=example,dc=com", "-p", "secret")).isTrue();

		assertThat(this.server.badBindSeen()).isFalse();
		boolean passwordSent = this.server.binds()
			.stream()
			.anyMatch((bind) -> "cn=admin,dc=example,dc=com".equals(bind[0]) && "secret".equals(bind[1]));
		assertThat(passwordSent).isTrue();
	}

}
