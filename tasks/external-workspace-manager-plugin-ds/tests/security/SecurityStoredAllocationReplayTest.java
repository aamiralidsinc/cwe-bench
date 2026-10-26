package bench.ewm;

import hudson.model.Result;
import org.jenkinsci.plugins.ewm.model.ExternalWorkspace;
import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;

/**
 * A workspace recorded by an earlier allocation and reused by a later build must not let that
 * later build work outside the mount point.
 */
public class SecurityStoredAllocationReplayTest extends EwmBase {

    @Test
    public void replayOfStoredTraversalCannotWriteOutside() throws Exception {
        WorkflowRun upstream = runScript("echo 'upstream'\n");

        ExternalWorkspace workspace = storedWorkspace("sub/../../outside");
        if (workspace == null
                || !registerFingerprint(upstream, workspace)
                || !attachStoredAllocation(upstream, workspace)) {
            // The product refused to load or record the value: the attack cannot be driven.
            assertFalse("a file was created outside the mount point", exists(outside, ATTACK_FILE));
            return;
        }

        String upstreamName = upstream.getParent().getName();
        WorkflowRun downstream = runScript(
                "def run = selectRun job: '" + upstreamName + "'\n"
                        + "def ext = exwsAllocate selectedRun: run\n"
                        + "node {\n"
                        + "  exws(ext) {\n"
                        + "    writeFile file: '" + ATTACK_FILE + "', text: 'x'\n"
                        + "  }\n"
                        + "}\n");

        assertNotEquals("a later build reused a recorded traversal workspace",
                Result.SUCCESS, downstream.getResult());
        assertFalse("a file was created outside the mount point", exists(outside, ATTACK_FILE));
    }
}
