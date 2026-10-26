package bench.jch;

import hudson.model.FreeStyleProject;
import org.htmlunit.Page;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/** The controller-level history of an archived job must not expose encrypted values either. */
public class SecurityRootDeletedRawTest extends BenchBase {

    @Test
    public void archivedRevisionViewDoesNotExposeEncryptedValues() throws Exception {
        FreeStyleProject p = createJobWithSecrets("archived-raw", FIRST_SECRET, SECOND_SECRET);
        File[] revisions = revisionsWithDifferentSecrets("archived-raw");
        String stored = encryptedValue(configXml(revisions[0]));
        p.delete();
        String archived = deletedDirectory("archived-raw");

        Page page = get("jobConfigHistory/configOutput?name=" + encode(archived)
                + "&timestamp=" + revisions[0].getName(), READER);

        assertTrue("the archived history view failed with a server error", status(page) < 500);
        assertFalse("an encrypted value from an archived revision was disclosed to a configuration reader",
                body(page).contains(stored));
    }
}
