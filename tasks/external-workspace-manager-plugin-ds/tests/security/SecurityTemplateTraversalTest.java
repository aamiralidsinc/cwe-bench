package bench.ewm;

import hudson.model.Result;
import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;

/**
 * A value substituted into the disk pool's workspace pattern must not be able to leave the mount
 * point; the check has to see the value that is actually used, not the unexpanded text.
 */
public class SecurityTemplateTraversalTest extends EwmBase {

    private String script(String branch) {
        return "def ext = null\n"
                + "withEnv (['BRANCH=" + branch + "']) {\n"
                + "  ext = exwsAllocate diskPoolId: '" + POOL_ID + "'\n"
                + "}\n"
                + "node {\n"
                + "  exws(ext) {\n"
                + "    writeFile file: '" + ATTACK_FILE + "', text: 'x'\n"
                + "  }\n"
                + "}\n";
    }

    @Test
    public void expandedValueCannotEscape() throws Exception {
        configurePool("test/${BRANCH}");

        WorkflowRun run = runScript(script("../../outside"));

        assertNotEquals("a traversal allocation must not complete successfully",
                Result.SUCCESS, run.getResult());
        assertFalse("a file was created outside the mount point", exists(outside, ATTACK_FILE));
    }

    @Test
    public void expandedNestedValueCannotEscape() throws Exception {
        configurePool("test/${BRANCH}");

        WorkflowRun run = runScript(script("sub/../../../outside"));

        assertNotEquals("a traversal allocation must not complete successfully",
                Result.SUCCESS, run.getResult());
        assertFalse("a file was created outside the mount point", exists(outside, ATTACK_FILE));
    }
}
