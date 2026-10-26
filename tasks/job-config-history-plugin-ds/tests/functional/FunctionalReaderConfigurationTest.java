package bench.jch;

import org.htmlunit.Page;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/** A configuration reader keeps seeing the configuration; only secret values are withheld. */
public class FunctionalReaderConfigurationTest extends BenchBase {

    @Test
    public void readerStillSeesTheConfiguration() throws Exception {
        createJobWithSecrets("reader-config", FIRST_SECRET, SECOND_SECRET);
        File[] revisions = revisionsWithDifferentSecrets("reader-config");

        Page page = get("job/reader-config/jobConfigHistory/configOutput?type=xml&timestamp="
                + revisions[0].getName(), READER);

        assertTrue("the configuration view was refused to a configuration reader", status(page) < 400);
        assertFalse("the configuration view told a configuration reader it had no permission",
                body(page).contains("No permission"));
        assertTrue("the non-secret content of the configuration disappeared",
                body(page).contains(OLD_DESCRIPTION));
    }
}
