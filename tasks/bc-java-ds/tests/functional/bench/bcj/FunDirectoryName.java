package bench.bcj;

import org.bouncycastle.util.Properties;

import static bench.bcj.Fixture.directoryName;
import static bench.bcj.Fixture.dn;
import static bench.bcj.Fixture.permitted;

/**
 * Directory name subtrees keep their prefix meaning, and the relaxed matching the product offers
 * for one deployment profile still works when that profile is enabled.
 */
public class FunDirectoryName
{
    public void testSubjectStartingWithThePermittedSequenceIsPermitted()
        throws Exception
    {
        Checks.mustAccept("subject that starts with the permitted sequence",
            Fixture.chain(permitted(directoryName("O=Bench")), dn("O=Bench, CN=Leaf"), null));
        Checks.mustAccept("subject that starts with a longer permitted sequence",
            Fixture.chain(permitted(directoryName("O=Bench, OU=Unit")), dn("O=Bench, OU=Unit, CN=Leaf"), null));
    }

    public void testSubjectOutsideThePermittedSequenceIsRefused()
        throws Exception
    {
        Checks.mustRefuse("subject that does not start with the permitted sequence",
            Fixture.chain(permitted(directoryName("O=Bench")), dn("O=Other, CN=Leaf"), null));
    }

    public void testRelaxedProfileStillMatchesAnywhereInTheSubject()
        throws Exception
    {
        System.setProperty(Properties.X509_SGP22_NAME_CONSTRAINTS, "true");
        try
        {
            Checks.mustAccept("subject carrying the permitted name after other attributes",
                Fixture.chain(permitted(directoryName("O=Bench")), dn("C=US, O=Bench, CN=Leaf"), null));
        }
        finally
        {
            System.clearProperty(Properties.X509_SGP22_NAME_CONSTRAINTS);
        }
    }
}
