package bench.jch;

import org.htmlunit.Page;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/** The rendered difference between two stored revisions must not reveal encrypted values. */
public class SecurityJobDiffEncryptedTest extends BenchBase {

    @Test
    public void differenceViewDoesNotExposeEncryptedValues() throws Exception {
        createJobWithSecrets("diff-encrypted", FIRST_SECRET, SECOND_SECRET);
        File[] revisions = revisionsWithDifferentSecrets("diff-encrypted");
        String older = encryptedValue(configXml(revisions[0]));
        String newer = encryptedValue(configXml(revisions[1]));

        Page page = get("job/diff-encrypted/jobConfigHistory/showDiffFiles?timestamp1="
                + revisions[0].getName() + "&timestamp2=" + revisions[1].getName(), READER);

        assertTrue("the difference view failed with a server error", status(page) < 500);
        assertFalse("an older stored encrypted value was disclosed in the difference view",
                body(page).contains(older));
        assertFalse("a newer stored encrypted value was disclosed in the difference view",
                body(page).contains(newer));
    }
}
