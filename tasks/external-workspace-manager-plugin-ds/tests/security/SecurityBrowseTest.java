package bench.ewm;

import org.jenkinsci.plugins.ewm.model.ExternalWorkspace;
import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/**
 * A workspace value recorded by an earlier allocation must never make the plugin serve content
 * from outside the mount point.
 */
public class SecurityBrowseTest extends EwmBase {

    @Test
    public void storedWorkspaceOutsideMountIsNotServed() throws Exception {
        WorkflowRun owner = runScript("echo 'owner'\n");
        writeMarker(outside, "secret.txt");

        ExternalWorkspace workspace = storedWorkspace("../outside");
        if (workspace == null || !registerFingerprint(owner, workspace)) {
            // The product refused to load the recorded value: the attack cannot be driven.
            assertTrue("a file outside the mount point was removed", exists(outside, "secret.txt"));
            return;
        }

        HttpResult result = http("GET", "exws/browse/" + workspace.getId() + "/ws/");

        assertTrue("the request failed with a server error", result.status < 500);
        assertFalse("content outside the mount point was disclosed", result.body.contains(SECRET));
        assertFalse("a file outside the mount point was listed", result.body.contains("secret.txt"));
    }
}
