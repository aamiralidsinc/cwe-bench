package bench.bcj;

import static bench.bcj.Fixture.dn;
import static bench.bcj.Fixture.email;
import static bench.bcj.Fixture.excluded;
import static bench.bcj.Fixture.names;

/**
 * A host written with its root label (the trailing dot of an RFC 1034 fully qualified name) must
 * be judged as the same host it denotes, on either side of the comparison.
 */
public class SecEmailCanonicalisation
{
    private static final org.bouncycastle.asn1.x500.X500Name LEAF = dn("C=US, O=Bench, CN=Leaf");

    public void testExcludedHostWithRootDotOnName()
        throws Exception
    {
        Checks.mustRefuse("trailing-dot mailbox at an excluded host",
            Fixture.chain(excluded(email("bank.com")), LEAF, names(email("ceo@bank.com."))));
    }

    public void testExcludedHostWithRootDotOnConstraint()
        throws Exception
    {
        Checks.mustRefuse("excluded host written with its root label",
            Fixture.chain(excluded(email("bank.com.")), LEAF, names(email("ceo@bank.com"))));
    }

    public void testExcludedAtDomainWithRootDotOnConstraint()
        throws Exception
    {
        Checks.mustRefuse("excluded domain constraint written with its root label",
            Fixture.chain(excluded(email("@bank.com.")), LEAF, names(email("ceo@bank.com"))));
    }

    public void testExcludedAtDomainWithRootDotOnName()
        throws Exception
    {
        Checks.mustRefuse("mailbox at an excluded domain, name written with its root label",
            Fixture.chain(excluded(email("@bank.com")), LEAF, names(email("ceo@bank.com."))));
    }

    public void testExcludedMailboxWithRootDotOnName()
        throws Exception
    {
        Checks.mustRefuse("excluded mailbox, name written with its root label",
            Fixture.chain(excluded(email("ceo@bank.com")), LEAF, names(email("ceo@bank.com."))));
    }

    public void testExcludedMailboxWithRootDotOnConstraint()
        throws Exception
    {
        Checks.mustRefuse("excluded mailbox written with its root label",
            Fixture.chain(excluded(email("ceo@bank.com.")), LEAF, names(email("ceo@bank.com"))));
    }
}
