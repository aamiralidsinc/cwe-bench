package bench.ewm;

import hudson.model.Result;
import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;

/** A literal custom workspace path must not allow the workspace to resolve outside the mount. */
public class SecurityCustomPathTest extends EwmBase {

    @Test
    public void leadingParentSegmentCannotEscape() throws Exception {
        WorkflowRun run = runScript(allocateWithPathAndWrite("../outside"));

        assertNotEquals("a traversal allocation must not complete successfully",
                Result.SUCCESS, run.getResult());
        assertFalse("a file was created outside the mount point", exists(outside, ATTACK_FILE));
    }

    @Test
    public void nestedParentSegmentCannotEscape() throws Exception {
        WorkflowRun run = runScript(allocateWithPathAndWrite("sub/../../outside"));

        assertNotEquals("a traversal allocation must not complete successfully",
                Result.SUCCESS, run.getResult());
        assertFalse("a file was created outside the mount point", exists(outside, ATTACK_FILE));
    }
}
