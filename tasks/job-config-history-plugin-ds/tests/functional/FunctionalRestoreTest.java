package bench.jch;

import hudson.model.ParametersDefinitionProperty;
import hudson.model.PasswordParameterDefinition;
import org.htmlunit.Page;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

/** Restoring a stored revision must apply the exact values that were stored. */
public class FunctionalRestoreTest extends BenchBase {

    @Test
    public void restoreKeepsTheOriginalStoredValue() throws Exception {
        createJobWithSecrets("restore-job", FIRST_SECRET, SECOND_SECRET);
        File[] revisions = revisionsWithDifferentSecrets("restore-job");
        String olderTimestamp = revisions[0].getName();

        Page response = post("job/restore-job/jobConfigHistory/restore",
                "timestamp=" + olderTimestamp, ADMIN);
        assertTrue("restoring a stored revision was refused", status(response) < 400);

        hudson.model.FreeStyleProject restoredJob =
                j.jenkins.getItemByFullName("restore-job", hudson.model.FreeStyleProject.class);
        PasswordParameterDefinition restored = (PasswordParameterDefinition) restoredJob
                .getProperty(ParametersDefinitionProperty.class).getParameterDefinition("P");
        assertEquals("the restored configuration did not keep the value that was stored",
                FIRST_SECRET, restored.getDefaultValue());
    }
}
