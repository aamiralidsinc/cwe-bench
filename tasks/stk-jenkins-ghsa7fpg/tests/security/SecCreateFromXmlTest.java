package hudson.security.bt;

import hudson.model.FreeStyleProject;
import hudson.model.Item;
import org.junit.Assert;
import org.junit.Test;

/**
 * Creating a job from a whole document must judge the trigger it brings with it, and a
 * refusal must not leave the created job (or its directory) behind.
 */
public class SecCreateFromXmlTest extends BtTest {

    @Test
    public void createNamesInvisibleTarget() throws Exception {
        FreeStyleProject hidden = free("hidden");
        FreeStyleProject template = free("template");
        storeTrigger(template, "hidden");
        String xml = configXml(template);

        enableAcl();
        // Job.CREATE is granted to the attacker by the fixture; no permission on 'hidden'.

        int status = post("createItem?name=created", xml, "application/xml", ATTACKER);
        assertClientError(status);
        Assert.assertNull("the refused job was registered", j.jenkins.getItem("created"));
        Assert.assertFalse("the refused job left a directory behind", jobDir(j.jenkins, "created").exists());
    }
}
