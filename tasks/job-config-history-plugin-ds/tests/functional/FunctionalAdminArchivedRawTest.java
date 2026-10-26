package bench.jch;

import hudson.model.FreeStyleProject;
import org.htmlunit.Page;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertTrue;

/** A user who may configure keeps full access to an archived configuration. */
public class FunctionalAdminArchivedRawTest extends BenchBase {

    @Test
    public void administratorSeesArchivedStoredValue() throws Exception {
        FreeStyleProject p = createJobWithSecrets("archived-admin", FIRST_SECRET, SECOND_SECRET);
        File[] revisions = revisionsWithDifferentSecrets("archived-admin");
        String stored = encryptedValue(configXml(revisions[0]));
        p.delete();
        String archived = deletedDirectory("archived-admin");

        Page page = get("jobConfigHistory/configOutput?name=" + encode(archived)
                + "&timestamp=" + revisions[0].getName(), ADMIN);

        assertTrue("the archived history view was refused to an administrator", status(page) < 400);
        assertTrue("an administrator no longer sees the stored encrypted value",
                body(page).contains(stored));
    }
}
