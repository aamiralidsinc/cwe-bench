package hudson.security.bt;

import hudson.model.FreeStyleProject;
import hudson.model.Item;
import org.junit.Test;

/**
 * A configuration written as a whole document must be judged as strictly as one written
 * through the page. A name the editor cannot even see still has to be judged.
 */
public class SecUpdateXmlTest extends BtTest {

    @Test
    public void xmlUpdateNamesInvisibleTarget() throws Exception {
        FreeStyleProject own = free("own");
        FreeStyleProject hidden = free("hidden");
        FreeStyleProject template = free("template");
        storeTrigger(own, "");
        storeTrigger(template, "hidden");
        String xml = configXml(template);

        enableAcl();
        grant(own, ATTACKER, Item.READ, Item.CONFIGURE);
        // no permission at all on 'hidden': the editor cannot see it

        int status = postXml("job/own/config.xml", xml, ATTACKER);
        assertClientError(status);
        org.junit.Assert.assertEquals("", storedChildren(own));
    }

    @Test
    public void xmlUpdateNamesVisibleUnbuildableTarget() throws Exception {
        FreeStyleProject own = free("own");
        FreeStyleProject hidden = free("hidden");
        FreeStyleProject template = free("template");
        storeTrigger(own, "");
        storeTrigger(template, "hidden");
        String xml = configXml(template);

        enableAcl();
        grant(own, ATTACKER, Item.READ, Item.CONFIGURE);
        grant(hidden, ATTACKER, Item.READ);

        int status = postXml("job/own/config.xml", xml, ATTACKER);
        assertClientError(status);
        org.junit.Assert.assertEquals("", storedChildren(own));
    }
}
