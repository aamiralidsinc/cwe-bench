package hudson.security.bt;

import hudson.model.FreeStyleProject;
import hudson.model.Item;
import hudson.matrix.MatrixProject;
import org.junit.Assert;
import org.junit.Test;

/**
 * Ordinary configuration saving keeps working: saving unrelated changes, using a target
 * the editor may build, and saving while an unrelated upstream project exists.
 */
public class FunFormSubmitTest extends BtTest {

    @Test
    public void savesWithoutTrigger() throws Exception {
        FreeStyleProject own = free("own");
        storeTrigger(own, "");

        enableAcl();
        grant(own, ATTACKER, Item.READ, Item.CONFIGURE);

        int status = submitConfigForm(own, ATTACKER, "");
        assertSuccess(status);
        String stored = storedChildren(own);
        Assert.assertTrue("an empty trigger must not name anything",
                stored == null || stored.trim().isEmpty());
    }

    @Test
    public void addsBuildableTarget() throws Exception {
        FreeStyleProject own = free("own");
        FreeStyleProject allowed = free("allowed");
        storeTrigger(own, "");

        enableAcl();
        grant(own, ATTACKER, Item.READ, Item.CONFIGURE);
        grant(allowed, ATTACKER, Item.READ, Item.BUILD);

        int status = submitConfigForm(own, ATTACKER, "allowed");
        assertSuccess(status);
        Assert.assertEquals("allowed", storedChildren(own));
    }

    @Test
    public void matrixAddsBuildableTarget() throws Exception {
        MatrixProject own = matrix("mown");
        FreeStyleProject allowed = free("allowed");
        storeTrigger(own, "");

        enableAcl();
        grant(own, ATTACKER, Item.READ, Item.CONFIGURE);
        grant(allowed, ATTACKER, Item.READ, Item.BUILD);

        int status = submitConfigForm(own, ATTACKER, "allowed");
        assertSuccess(status);
        Assert.assertEquals("allowed", storedChildren(own));
    }

    @Test
    public void savesWhileUnconfigurableUpstreamExists() throws Exception {
        FreeStyleProject own = free("own");
        FreeStyleProject up = free("up");
        storeTrigger(own, "");
        storeTrigger(up, "own");

        enableAcl();
        grant(own, ATTACKER, Item.READ, Item.CONFIGURE);
        grant(up, ATTACKER, Item.READ);       // may see it, may not configure it

        int status = submitConfigForm(own, ATTACKER, "");
        assertSuccess(status);
        Assert.assertNotNull(j.jenkins.getItem("own"));
    }
}
