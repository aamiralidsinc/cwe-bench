package bench.bcj;

import static bench.bcj.Fixture.directoryName;
import static bench.bcj.Fixture.dn;
import static bench.bcj.Fixture.permitted;

/**
 * A permitted directory-name subtree is a constraint on where a subject name starts, not on which
 * of its elements it happens to contain.
 */
public class SecDirectoryNamePrefix
{
    public void testSubjectWithRdnAheadOfPermittedSequence()
        throws Exception
    {
        Checks.mustRefuse("subject carries names ahead of the permitted sequence",
            Fixture.chain(permitted(directoryName("O=Bench, CN=Permitted Sequence")),
                dn("C=FR, O=Attacker, O=Bench, CN=Permitted Sequence, CN=Leaf"), null));
    }

    public void testSubjectWithTwoRdnsAheadOfPermittedSequence()
        throws Exception
    {
        Checks.mustRefuse("subject carries two names ahead of the permitted sequence",
            Fixture.chain(permitted(directoryName("O=Bench")),
                dn("C=FR, O=Attacker, O=Bench, CN=Leaf"), null));
    }
}
