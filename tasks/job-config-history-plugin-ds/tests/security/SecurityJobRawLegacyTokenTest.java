package bench.jch;

import org.htmlunit.Page;
import org.junit.Test;

import java.io.File;
import java.util.List;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/** A plain-text token kept in an old revision must not be shown to a configuration reader. */
public class SecurityJobRawLegacyTokenTest extends BenchBase {

    @Test
    public void jobRevisionViewDoesNotExposePlainTextToken() throws Exception {
        createJobWithSecrets("raw-legacy-token", FIRST_SECRET, SECOND_SECRET);
        List<File> revisions = revisions("raw-legacy-token");
        File legacy = addPlainTextToken(revisions.get(revisions.size() - 1), LEGACY_TOKEN);

        Page page = get("job/raw-legacy-token/jobConfigHistory/configOutput?type=xml&timestamp="
                + legacy.getName(), READER);

        assertTrue("the history view failed with a server error", status(page) < 500);
        assertFalse("a plain-text token from a stored revision was disclosed to a configuration reader",
                body(page).contains(LEGACY_TOKEN));
    }
}
