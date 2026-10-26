package bench.ewm;

import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.Test;

/** A workspace allocated by one build and reused by a later build keeps working. */
public class FunctionalStoredAllocationReplayTest extends EwmBase {

    @Test
    public void legitimateStoredAllocationStillReplays() throws Exception {
        WorkflowRun upstream = runScript(
                "def ext = exwsAllocate diskPoolId: '" + POOL_ID + "'\n"
                        + "node {\n"
                        + "  exws(ext) {\n"
                        + "    writeFile file: 'up.txt', text: 'from-upstream'\n"
                        + "  }\n"
                        + "}\n");
        j.assertBuildStatusSuccess(upstream);

        String upstreamName = upstream.getParent().getName();
        WorkflowRun downstream = runScript(
                "def run = selectRun job: '" + upstreamName + "'\n"
                        + "def ext = exwsAllocate selectedRun: run\n"
                        + "node {\n"
                        + "  exws(ext) {\n"
                        + "    echo readFile(file: 'up.txt')\n"
                        + "  }\n"
                        + "}\n");

        j.assertBuildStatusSuccess(downstream);
        j.assertLogContains("from-upstream", downstream);
    }
}
