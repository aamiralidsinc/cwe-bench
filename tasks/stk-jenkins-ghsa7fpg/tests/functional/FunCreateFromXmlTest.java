package hudson.security.bt;

import hudson.model.AbstractProject;
import hudson.model.FreeStyleProject;
import hudson.model.Item;
import org.junit.Assert;
import org.junit.Test;

/** Creating a job from a document naming a buildable project still works. */
public class FunCreateFromXmlTest extends BtTest {

    @Test
    public void createWithBuildableTarget() throws Exception {
        FreeStyleProject allowed = free("allowed");
        FreeStyleProject template = free("template");
        storeTrigger(template, "allowed");
        String xml = configXml(template);

        enableAcl();
        grant(allowed, ATTACKER, Item.READ, Item.BUILD);

        int status = post("createItem?name=created", xml, "application/xml", ATTACKER);
        assertSuccess(status);
        AbstractProject<?, ?> created =
                (AbstractProject<?, ?>) j.jenkins.getItem("created");
        Assert.assertNotNull("the accepted job was not created", created);
        Assert.assertEquals("allowed", storedChildren(created));
    }
}
