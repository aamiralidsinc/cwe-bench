package hudson.security.bt;

import hudson.model.FreeStyleProject;
import hudson.model.Item;
import org.junit.Assert;
import org.junit.Test;

/**
 * Duplicating an existing job copies its stored configuration into a new job the copier
 * owns; the copy must be judged as a configuration the copier is writing.
 */
public class SecCopyTest extends BtTest {

    @Test
    public void copySourceTriggeringInvisibleTarget() throws Exception {
        FreeStyleProject source = free("source");
        FreeStyleProject hidden = free("hidden");
        storeTrigger(source, "hidden");

        enableAcl();
        grant(source, ATTACKER, Item.READ);

        int status = post("createItem?name=copied&mode=copy&from=source", null, "application/x-www-form-urlencoded", ATTACKER);
        assertClientError(status);
        Assert.assertNull("the refused copy was registered", j.jenkins.getItem("copied"));
        Assert.assertFalse("the refused copy left a directory behind", jobDir(j.jenkins, "copied").exists());
    }

    @Test
    public void copySourceTriggeringVisibleUnbuildableTarget() throws Exception {
        FreeStyleProject source = free("source");
        FreeStyleProject hidden = free("hidden");
        storeTrigger(source, "hidden");

        enableAcl();
        grant(source, ATTACKER, Item.READ);
        grant(hidden, ATTACKER, Item.READ);

        int status = post("createItem?name=copied&mode=copy&from=source", null, "application/x-www-form-urlencoded", ATTACKER);
        assertClientError(status);
        Assert.assertNull("the refused copy was registered", j.jenkins.getItem("copied"));
    }
}
