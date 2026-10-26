package bench.ewm;

import org.jenkinsci.plugins.ewm.model.ExternalWorkspace;
import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.Test;

import java.io.File;
import java.nio.file.Files;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/** A legitimate workspace cleanup removes the workspace and nothing beside it. */
public class FunctionalCleanupTest extends EwmBase {

    @Test
    public void legitimateCleanupDeletesOnlyTheWorkspace() throws Exception {
        WorkflowRun owner = runScript("echo 'owner'\n");

        ExternalWorkspace workspace = storedWorkspace("job/1");
        assertNotNull("a legitimate recorded workspace could not be loaded", workspace);
        assertTrue("a legitimate recorded workspace could not be fingerprinted",
                registerFingerprint(owner, workspace));

        File inside = new File(mount, "job/1");
        Files.createDirectories(inside.toPath());
        writeMarker(inside, "inside.txt");
        writeMarker(outside, "sibling.txt");

        HttpResult result = http("POST", "exws/browse/" + workspace.getId() + "/cleanup");

        assertTrue("the cleanup request failed with a server error", result.status < 500);
        assertFalse("the legitimate workspace was not removed", inside.exists());
        assertTrue("a file outside the mount point was removed", exists(outside, "sibling.txt"));
    }
}
