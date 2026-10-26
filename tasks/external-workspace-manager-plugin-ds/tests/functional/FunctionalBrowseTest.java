package bench.ewm;

import org.jenkinsci.plugins.ewm.model.ExternalWorkspace;
import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.Test;

import java.io.File;
import java.nio.file.Files;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/** A legitimate recorded workspace stays browsable. */
public class FunctionalBrowseTest extends EwmBase {

    @Test
    public void legitimateStoredWorkspaceIsBrowsable() throws Exception {
        WorkflowRun owner = runScript("echo 'owner'\n");

        ExternalWorkspace workspace = storedWorkspace("job/1");
        assertNotNull("a legitimate recorded workspace could not be loaded", workspace);
        assertTrue("a legitimate recorded workspace could not be fingerprinted",
                registerFingerprint(owner, workspace));

        File inside = new File(mount, "job/1");
        Files.createDirectories(inside.toPath());
        writeMarker(inside, "inside.txt");

        HttpResult result = http("GET", "exws/browse/" + workspace.getId() + "/ws/");

        assertEquals("the legitimate workspace page was not served: " + result.body,
                200, result.status);
        assertTrue("the legitimate workspace contents were not listed",
                result.body.contains("inside.txt"));
    }
}
