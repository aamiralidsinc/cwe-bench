package bench.jch;

import org.htmlunit.Page;
import org.junit.Test;

import java.io.File;
import java.util.List;

import static org.junit.Assert.assertTrue;

/** A user who may configure the job keeps full access to the stored values. */
public class FunctionalConfigureRawTest extends BenchBase {

    @Test
    public void configuringUserSeesStoredValues() throws Exception {
        createJobWithSecrets("configure-raw", FIRST_SECRET, SECOND_SECRET);
        File[] revisions = revisionsWithDifferentSecrets("configure-raw");
        String stored = encryptedValue(configXml(revisions[0]));

        Page raw = get("job/configure-raw/jobConfigHistory/configOutput?type=xml&timestamp="
                + revisions[0].getName(), CONFIGURER);
        assertTrue("the configuration view was refused to a configuring user", status(raw) < 400);
        assertTrue("a configuring user no longer sees the stored encrypted value", body(raw).contains(stored));

        Page download = get("job/configure-raw/jobConfigHistory/download?timestamp="
                + revisions[0].getName(), CONFIGURER);
        assertTrue("the download was refused to a configuring user", status(download) < 400);
        assertTrue("a configuring user no longer receives the stored encrypted value from the download",
                body(download).contains(stored));

        List<File> all = revisions("configure-raw");
        File legacy = addPlainTextToken(all.get(all.size() - 1), LEGACY_TOKEN);
        Page legacyRaw = get("job/configure-raw/jobConfigHistory/configOutput?type=xml&timestamp="
                + legacy.getName(), CONFIGURER);
        assertTrue("the configuration view was refused to a configuring user", status(legacyRaw) < 400);
        assertTrue("a configuring user no longer sees a plain-text value kept in an old revision",
                body(legacyRaw).contains(LEGACY_TOKEN));
    }
}
