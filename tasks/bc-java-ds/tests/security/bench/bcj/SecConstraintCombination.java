package bench.bcj;

import static bench.bcj.Fixture.both;
import static bench.bcj.Fixture.directoryName;
import static bench.bcj.Fixture.dn;
import static bench.bcj.Fixture.email;
import static bench.bcj.Fixture.names;

/**
 * A CA certificate that carries both kinds of constraint applies both: a name outside the permitted
 * set is refused even when the same CA also publishes excluded subtrees.
 */
public class SecConstraintCombination
{
    public void testEmailOutsidePermittedSetWithExcludedSubtreesPresent()
        throws Exception
    {
        Checks.mustRefuse("address outside the permitted set, beside an excluded subtree",
            Fixture.chain(both(new org.bouncycastle.asn1.x509.GeneralName[]{email(".bench.example")},
                    new org.bouncycastle.asn1.x509.GeneralName[]{email("bank.com")}),
                dn("C=US, O=Bench, CN=Leaf"), names(email("ok@other.example"))));
    }

    public void testDirectoryNameOutsidePermittedSetWithExcludedSubtreesPresent()
        throws Exception
    {
        Checks.mustRefuse("subject outside the permitted subtree, beside an excluded subtree",
            Fixture.chain(both(new org.bouncycastle.asn1.x509.GeneralName[]{directoryName("O=Bench")},
                    new org.bouncycastle.asn1.x509.GeneralName[]{email("bank.com")}),
                dn("C=US, O=Other, CN=Leaf"), null));
    }

    public void testUriOutsidePermittedSetWithExcludedSubtreesPresent()
        throws Exception
    {
        Checks.mustRefuse("URI outside the permitted subtree, beside an excluded subtree",
            Fixture.chain(both(new org.bouncycastle.asn1.x509.GeneralName[]{Fixture.uri(".bench.example")},
                    new org.bouncycastle.asn1.x509.GeneralName[]{email("bank.com")}),
                dn("C=US, O=Bench, CN=Leaf"), names(Fixture.uri("https://other.example/report"))));
    }
}
