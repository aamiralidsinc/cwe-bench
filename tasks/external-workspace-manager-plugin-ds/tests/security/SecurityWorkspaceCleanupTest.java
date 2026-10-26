package bench.ewm;

import org.jenkinsci.plugins.ewm.model.ExternalWorkspace;
import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.Test;

import static org.junit.Assert.assertTrue;

/**
 * Removing an allocated workspace must never remove anything outside the mount point, including
 * for a workspace value recorded by an earlier allocation.
 */
public class SecurityWorkspaceCleanupTest extends EwmBase {

    @Test
    public void cleanupCannotDeleteOutsideTheMount() throws Exception {
        WorkflowRun owner = runScript("echo 'owner'\n");
        writeMarker(outside, "keep.txt");

        ExternalWorkspace workspace = storedWorkspace("../outside");
        if (workspace == null || !registerFingerprint(owner, workspace)) {
            // The product refused to load the recorded value: the attack cannot be driven.
            assertTrue("a file outside the mount point was removed", exists(outside, "keep.txt"));
            return;
        }

        HttpResult result = http("POST", "exws/browse/" + workspace.getId() + "/cleanup");

        assertTrue("the request failed with a server error", result.status < 500);
        assertTrue("a file outside the mount point was deleted", exists(outside, "keep.txt"));
    }
}
