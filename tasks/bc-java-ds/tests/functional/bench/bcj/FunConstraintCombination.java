package bench.bcj;

import static bench.bcj.Fixture.both;
import static bench.bcj.Fixture.directoryName;
import static bench.bcj.Fixture.dn;
import static bench.bcj.Fixture.email;
import static bench.bcj.Fixture.names;
import static bench.bcj.Fixture.permitted;

/**
 * A CA certificate may publish permitted and excluded subtrees at once; names that satisfy both
 * keep validating.
 */
public class FunConstraintCombination
{
    public void testEmailInsidePermittedAndNotExcluded()
        throws Exception
    {
        Checks.mustAccept("address inside the permitted set and outside the excluded one",
            Fixture.chain(both(new org.bouncycastle.asn1.x509.GeneralName[]{email(".bench.example")},
                    new org.bouncycastle.asn1.x509.GeneralName[]{email("bank.com")}),
                dn("C=US, O=Bench, CN=Leaf"), names(email("ok@sub.bench.example"))));
    }

    public void testExcludedAddressStillRefused()
        throws Exception
    {
        Checks.mustRefuse("address inside the permitted set but excluded",
            Fixture.chain(both(new org.bouncycastle.asn1.x509.GeneralName[]{email(".bench.example")},
                    new org.bouncycastle.asn1.x509.GeneralName[]{email("bank.com")}),
                dn("C=US, O=Bench, CN=Leaf"), names(email("ok@sub.bench.example"), email("ceo@bank.com"))));
    }

    public void testDirectoryNameInsidePermittedAndEmailOutsideExcluded()
        throws Exception
    {
        Checks.mustAccept("subject inside the permitted subtree and address outside the excluded one",
            Fixture.chain(both(new org.bouncycastle.asn1.x509.GeneralName[]{directoryName("O=Bench")},
                    new org.bouncycastle.asn1.x509.GeneralName[]{email("bank.com")}),
                dn("O=Bench, CN=Leaf"), names(email("ceo@bench.example"))));
    }

    public void testPermittedOnlyConstraintUnchanged()
        throws Exception
    {
        Checks.mustAccept("address inside a permitted-only constraint",
            Fixture.chain(permitted(email(".bench.example")), dn("C=US, O=Bench, CN=Leaf"),
                names(email("ok@sub.bench.example"))));
        Checks.mustRefuse("address outside a permitted-only constraint",
            Fixture.chain(permitted(email(".bench.example")), dn("C=US, O=Bench, CN=Leaf"),
                names(email("ok@other.example"))));
    }
}
