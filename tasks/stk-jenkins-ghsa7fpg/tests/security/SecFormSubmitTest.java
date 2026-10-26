package hudson.security.bt;

import hudson.model.FreeStyleProject;
import hudson.model.Item;
import hudson.matrix.MatrixProject;
import org.junit.Test;

/**
 * The configuration page must not store a build-other-projects entry that names a
 * project the editor may not build.
 */
public class SecFormSubmitTest extends BtTest {

    @Test
    public void addsUnbuildableTarget() throws Exception {
        FreeStyleProject own = free("own");
        FreeStyleProject hidden = free("hidden");
        storeTrigger(own, "");

        enableAcl();
        grant(own, ATTACKER, Item.READ, Item.CONFIGURE);
        grant(hidden, ATTACKER, Item.READ);          // visible, but may not build it

        int status = submitConfigForm(own, ATTACKER, "hidden");
        assertClientError(status);
        assertStored(own, "");
    }

    @Test
    public void replacesAllowedWithUnbuildable() throws Exception {
        FreeStyleProject own = free("own");
        FreeStyleProject allowed = free("allowed");
        FreeStyleProject hidden = free("hidden");
        storeTrigger(own, "allowed");

        enableAcl();
        grant(own, ATTACKER, Item.READ, Item.CONFIGURE);
        grant(allowed, ATTACKER, Item.READ, Item.BUILD);
        grant(hidden, ATTACKER, Item.READ);

        int status = submitConfigForm(own, ATTACKER, "hidden");
        assertClientError(status);
        assertStored(own, "allowed");
    }

    @Test
    public void twoChildrenOneUnbuildable() throws Exception {
        FreeStyleProject own = free("own");
        FreeStyleProject allowed = free("allowed");
        FreeStyleProject hidden = free("hidden");
        storeTrigger(own, "");

        enableAcl();
        grant(own, ATTACKER, Item.READ, Item.CONFIGURE);
        grant(allowed, ATTACKER, Item.READ, Item.BUILD);
        grant(hidden, ATTACKER, Item.READ);

        int status = submitConfigForm(own, ATTACKER, "allowed,hidden");
        assertClientError(status);
        assertStored(own, "");
    }

    @Test
    public void matrixAddsUnbuildableTarget() throws Exception {
        MatrixProject own = matrix("mown");
        FreeStyleProject hidden = free("hidden");
        storeTrigger(own, "");

        enableAcl();
        grant(own, ATTACKER, Item.READ, Item.CONFIGURE);
        grant(hidden, ATTACKER, Item.READ);

        int status = submitConfigForm(own, ATTACKER, "hidden");
        assertClientError(status);
        assertStored(own, "");
    }

    private static void assertStored(FreeStyleProject p, String expected) throws Exception {
        org.junit.Assert.assertEquals("the stored trigger changed", expected, storedChildren(p));
    }

    private static void assertStored(MatrixProject p, String expected) throws Exception {
        org.junit.Assert.assertEquals("the stored trigger changed", expected, storedChildren(p));
    }
}
