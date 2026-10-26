package hudson.security.bt;

import hudson.model.FreeStyleProject;
import hudson.model.Item;
import org.junit.Assert;
import org.junit.Test;

/** A whole-document update naming a buildable project still applies. */
public class FunUpdateXmlTest extends BtTest {

    @Test
    public void xmlUpdateToBuildableTarget() throws Exception {
        FreeStyleProject own = free("own");
        FreeStyleProject allowed = free("allowed");
        FreeStyleProject template = free("template");
        storeTrigger(own, "");
        storeTrigger(template, "allowed");
        String xml = configXml(template);

        enableAcl();
        grant(own, ATTACKER, Item.READ, Item.CONFIGURE);
        grant(allowed, ATTACKER, Item.READ, Item.BUILD);

        int status = postXml("job/own/config.xml", xml, ATTACKER);
        assertSuccess(status);
        Assert.assertEquals("allowed", storedChildren(own));
    }
}
