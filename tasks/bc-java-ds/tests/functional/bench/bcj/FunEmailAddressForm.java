package bench.bcj;

import static bench.bcj.Fixture.dn;
import static bench.bcj.Fixture.email;
import static bench.bcj.Fixture.excluded;
import static bench.bcj.Fixture.names;
import static bench.bcj.Fixture.permitted;

/**
 * Addresses whose local part is a quoted string stay usable, and the host is still read correctly.
 */
public class FunEmailAddressForm
{
    private static final org.bouncycastle.asn1.x500.X500Name LEAF = dn("C=US, O=Bench, CN=Leaf");

    public void testQuotedLocalPartInsidePermittedDomain()
        throws Exception
    {
        Checks.mustAccept("quoted local part inside a permitted domain",
            Fixture.chain(permitted(email(".bench.example")), LEAF,
                names(email("\"a@other.example\"@sub.bench.example"))));
        Checks.mustAccept("plain local part inside a permitted domain",
            Fixture.chain(permitted(email(".bench.example")), LEAF,
                names(email("ceo@sub.bench.example"))));
    }

    public void testQuotedLocalPartOutsideExcludedHost()
        throws Exception
    {
        Checks.mustAccept("quoted local part naming the excluded host, at another host",
            Fixture.chain(excluded(email("bank.com")), LEAF,
                names(email("\"a@bank.com\"@bench.example"))));
    }

    public void testOrdinaryAddressesAreUnaffected()
        throws Exception
    {
        Checks.mustAccept("ordinary address with a permitted mailbox",
            Fixture.chain(permitted(email("ceo@bench.example")), LEAF, names(email("ceo@bench.example"))));
        Checks.mustRefuse("ordinary address outside the permitted mailbox",
            Fixture.chain(permitted(email("ceo@bench.example")), LEAF,
                names(email("other@bench.example"))));
    }
}
