package hudson.security.bt;

import hudson.model.AbstractProject;
import hudson.model.FreeStyleProject;
import hudson.model.Item;
import org.junit.Assert;
import org.junit.Test;

/** Copying a job whose trigger names a project the copier may build still works. */
public class FunCopyTest extends BtTest {

    @Test
    public void copyWithBuildableTrigger() throws Exception {
        FreeStyleProject source = free("source");
        FreeStyleProject allowed = free("allowed");
        storeTrigger(source, "allowed");

        enableAcl();
        grant(source, ATTACKER, Item.READ);
        grant(allowed, ATTACKER, Item.READ, Item.BUILD);

        int status = post("createItem?name=copied&mode=copy&from=source", null, "application/x-www-form-urlencoded", ATTACKER);
        assertSuccess(status);
        AbstractProject<?, ?> copied = (AbstractProject<?, ?>) j.jenkins.getItem("copied");
        Assert.assertNotNull("the accepted copy was not created", copied);
        Assert.assertEquals("allowed", storedChildren(copied));
    }
}
