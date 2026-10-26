package hudson.security.bt;

import hudson.model.FreeStyleProject;
import hudson.model.Item;
import org.junit.Assert;
import org.junit.Test;

/**
 * The fixture's own state is persistable: once the permission matrix and its per-job grants
 * are installed, the controller can save its configuration. A refusal path that rolls a
 * half-created item back saves that configuration, so this must work on the untouched code.
 */
public class FunFixtureSaveTest extends BtTest {

    @Test
    public void savesControllerStateWithAclAndGrants() throws Exception {
        FreeStyleProject own = free("own");
        FreeStyleProject allowed = free("allowed");
        storeTrigger(own, "allowed");

        enableAcl();
        grant(own, ATTACKER, Item.READ, Item.CONFIGURE);
        grant(allowed, ATTACKER, Item.READ, Item.BUILD);

        j.jenkins.save();

        Assert.assertNotNull("the configured job disappeared after the save",
                j.jenkins.getItem("own"));
    }
}
