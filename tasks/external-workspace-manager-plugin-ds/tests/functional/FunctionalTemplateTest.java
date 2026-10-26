package bench.ewm;

import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertTrue;

/** Legitimate workspace patterns, with and without a substituted value, keep working. */
public class FunctionalTemplateTest extends EwmBase {

    @Test
    public void jobAndBuildNumberPatternStillWorks() throws Exception {
        configurePool("${JOB_NAME}/${BUILD_NUMBER}");

        WorkflowRun run = runScript(
                "def ext = exwsAllocate diskPoolId: '" + POOL_ID + "'\n"
                        + "node {\n"
                        + "  exws(ext) {\n"
                        + "    writeFile file: 'ok.txt', text: 'ok'\n"
                        + "  }\n"
                        + "}\n");
        j.assertBuildStatusSuccess(run);

        File expected = new File(mount,
                run.getParent().getName() + "/" + run.getNumber() + "/ok.txt");
        assertTrue("the workspace file is missing: " + expected, expected.isFile());
    }

    @Test
    public void nestedSubstitutedValueStillWorks() throws Exception {
        configurePool("team/${BRANCH}");

        WorkflowRun run = runScript(
                "def ext = null\n"
                        + "withEnv (['BRANCH=feature/x']) {\n"
                        + "  ext = exwsAllocate diskPoolId: '" + POOL_ID + "'\n"
                        + "}\n"
                        + "node {\n"
                        + "  exws(ext) {\n"
                        + "    writeFile file: 'ok.txt', text: 'ok'\n"
                        + "  }\n"
                        + "}\n");
        j.assertBuildStatusSuccess(run);

        File expected = new File(mount, "team/feature/x/ok.txt");
        assertTrue("the workspace file is missing: " + expected, expected.isFile());
    }
}
