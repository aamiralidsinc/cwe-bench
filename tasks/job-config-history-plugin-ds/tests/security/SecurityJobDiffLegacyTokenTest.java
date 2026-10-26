package bench.jch;

import org.htmlunit.Page;
import org.junit.Test;

import java.io.File;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/** A plain-text token in an old revision must not appear in the rendered difference either. */
public class SecurityJobDiffLegacyTokenTest extends BenchBase {

    @Test
    public void differenceViewDoesNotExposePlainTextToken() throws Exception {
        createJobWithSecrets("diff-legacy-token", FIRST_SECRET, SECOND_SECRET);
        File[] revisions = revisionsWithDifferentSecrets("diff-legacy-token");
        File legacy = addPlainTextToken(revisions[1], LEGACY_TOKEN);

        Page page = get("job/diff-legacy-token/jobConfigHistory/showDiffFiles?timestamp1="
                + revisions[0].getName() + "&timestamp2=" + legacy.getName(), READER);

        assertTrue("the difference view failed with a server error", status(page) < 500);
        assertFalse("a plain-text token from a stored revision was disclosed in the difference view",
                body(page).contains(LEGACY_TOKEN));
    }
}
