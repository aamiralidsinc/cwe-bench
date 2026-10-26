package bench.ewm;

import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertTrue;

/** A legitimate sub-folder of the default workspace path keeps working. */
public class FunctionalSubPathTest extends EwmBase {

    @Test
    public void legitimateSubPathStillWorks() throws Exception {
        WorkflowRun run = runScript(
                "def ext = exwsAllocate diskPoolId: '" + POOL_ID + "', subPath: 'nested/dir'\n"
                        + "node {\n"
                        + "  exws(ext) {\n"
                        + "    writeFile file: 'ok.txt', text: 'ok'\n"
                        + "  }\n"
                        + "}\n");
        j.assertBuildStatusSuccess(run);

        File expected = new File(mount,
                run.getParent().getName() + "/" + run.getNumber() + "/nested/dir/ok.txt");
        assertTrue("the workspace file is missing: " + expected, expected.isFile());
    }
}
