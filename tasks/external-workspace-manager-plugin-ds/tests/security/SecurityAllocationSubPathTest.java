package bench.ewm;

import hudson.model.Result;
import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;

/** A job-supplied sub-folder of the default path must not leave the mount point. */
public class SecurityAllocationSubPathTest extends EwmBase {

    @Test
    public void subPathCannotEscapeTheMount() throws Exception {
        WorkflowRun run = runScript(
                "def ext = exwsAllocate diskPoolId: '" + POOL_ID + "', subPath: '../../../outside'\n"
                        + "node {\n"
                        + "  exws(ext) {\n"
                        + "    writeFile file: '" + ATTACK_FILE + "', text: 'x'\n"
                        + "  }\n"
                        + "}\n");

        assertNotEquals("a traversal allocation must not complete successfully",
                Result.SUCCESS, run.getResult());
        assertFalse("a file was created outside the mount point", exists(outside, ATTACK_FILE));
    }
}
