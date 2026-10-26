package bench.ewm;

import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertTrue;

/** Legitimate relative custom paths, including nested and dotted names, keep working. */
public class FunctionalCustomPathTest extends EwmBase {

    @Test
    public void nestedRelativePathStillWorks() throws Exception {
        WorkflowRun run = runScript(allocateWithPathAndWrite("team/a/1"));
        j.assertBuildStatusSuccess(run);

        File expected = new File(mount, "team/a/1/" + ATTACK_FILE);
        assertTrue("the workspace file is missing: " + expected, expected.isFile());
    }

    @Test
    public void namesMerelyContainingDotsStillWork() throws Exception {
        WorkflowRun run = runScript(allocateWithPathAndWrite("a..b/.cache"));
        j.assertBuildStatusSuccess(run);

        File expected = new File(mount, "a..b/.cache/" + ATTACK_FILE);
        assertTrue("the workspace file is missing: " + expected, expected.isFile());
    }
}
