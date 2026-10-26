package bench.jch;

import org.htmlunit.Page;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/** The difference view keeps showing ordinary changes to a configuration reader. */
public class FunctionalReaderDifferenceTest extends BenchBase {

    @Test
    public void readerStillSeesOrdinaryDifferences() throws Exception {
        createJobWithSecrets("reader-diff", FIRST_SECRET, SECOND_SECRET);
        File[] revisions = revisionsWithDifferentSecrets("reader-diff");

        Page page = get("job/reader-diff/jobConfigHistory/showDiffFiles?timestamp1="
                + revisions[0].getName() + "&timestamp2=" + revisions[1].getName(), READER);

        assertTrue("the difference view was refused to a configuration reader", status(page) < 400);
        assertFalse("the difference view told a configuration reader it had no permission",
                body(page).contains("No permission"));
        assertTrue("an ordinary change disappeared from the difference view",
                body(page).contains(NEW_DESCRIPTION));
    }
}
