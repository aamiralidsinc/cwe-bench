package bench.jch;

import org.htmlunit.Page;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/** A user who may inspect a job's configuration must not receive stored encrypted values. */
public class SecurityJobRawEncryptedTest extends BenchBase {

    @Test
    public void jobRevisionViewDoesNotExposeEncryptedValues() throws Exception {
        createJobWithSecrets("raw-encrypted", FIRST_SECRET, SECOND_SECRET);
        File[] revisions = revisionsWithDifferentSecrets("raw-encrypted");
        String stored = encryptedValue(configXml(revisions[0]));

        Page page = get("job/raw-encrypted/jobConfigHistory/configOutput?type=xml&timestamp="
                + revisions[0].getName(), READER);

        assertTrue("the history view failed with a server error", status(page) < 500);
        assertFalse("an encrypted value from a stored revision was disclosed to a configuration reader",
                body(page).contains(stored));
    }
}
