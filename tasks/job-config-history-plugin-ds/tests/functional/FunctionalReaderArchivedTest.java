package bench.jch;

import hudson.model.FreeStyleProject;
import org.htmlunit.Page;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/** A configuration reader keeps access to the archived history of a deleted job. */
public class FunctionalReaderArchivedTest extends BenchBase {

    @Test
    public void readerStillSeesArchivedConfiguration() throws Exception {
        FreeStyleProject p = createJobWithSecrets("archived-reader", FIRST_SECRET, SECOND_SECRET);
        File[] revisions = revisionsWithDifferentSecrets("archived-reader");
        p.delete();
        String archived = deletedDirectory("archived-reader");

        Page page = get("jobConfigHistory/configOutput?name=" + encode(archived)
                + "&timestamp=" + revisions[0].getName(), READER);

        assertTrue("the archived history view was refused to a configuration reader", status(page) < 400);
        assertFalse("the archived history view told a configuration reader it had no permission",
                body(page).contains("No permission"));
        assertTrue("the non-secret content of the archived configuration disappeared",
                body(page).contains(OLD_DESCRIPTION));
    }
}
