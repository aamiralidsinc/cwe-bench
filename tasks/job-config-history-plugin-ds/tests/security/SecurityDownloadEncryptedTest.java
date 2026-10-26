package bench.jch;

import org.htmlunit.Page;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/** A stored revision obtained through the download entry point must not expose encrypted values. */
public class SecurityDownloadEncryptedTest extends BenchBase {

    @Test
    public void downloadDoesNotExposeEncryptedValues() throws Exception {
        createJobWithSecrets("downloaded", FIRST_SECRET, SECOND_SECRET);
        File[] revisions = revisionsWithDifferentSecrets("downloaded");
        String stored = encryptedValue(configXml(revisions[0]));

        Page page = get("job/downloaded/jobConfigHistory/download?timestamp="
                + revisions[0].getName(), READER);

        assertTrue("the download failed with a server error", status(page) < 500);
        assertFalse("an encrypted value from a stored revision was disclosed by the download",
                body(page).contains(stored));
    }
}
