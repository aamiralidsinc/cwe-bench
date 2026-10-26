package hudson.security.bt;

import hudson.model.FreeStyleProject;
import org.junit.Assert;
import org.junit.Test;

/**
 * A stored trigger keeps firing when its upstream job builds: the guard belongs to
 * configuration writes, not to the build that follows.
 */
public class FunTriggerBuildsTest extends BtTest {

    @Test
    public void storedTriggerBuildsDownstream() throws Exception {
        FreeStyleProject up = free("up");
        FreeStyleProject down = free("down");
        storeTrigger(up, "down");

        j.buildAndAssertSuccess(up);
        j.waitUntilNoActivity();

        Assert.assertNotNull("the stored trigger did not start the downstream job",
                down.getLastBuild());
    }
}
