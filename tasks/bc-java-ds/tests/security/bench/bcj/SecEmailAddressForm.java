package bench.bcj;

import static bench.bcj.Fixture.dn;
import static bench.bcj.Fixture.email;
import static bench.bcj.Fixture.excluded;
import static bench.bcj.Fixture.names;

/**
 * The host of a mail address is what follows the last unquoted '@'; a quoted local part may itself
 * contain '@' and must not be mistaken for the separator.
 */
public class SecEmailAddressForm
{
    private static final org.bouncycastle.asn1.x500.X500Name LEAF = dn("C=US, O=Bench, CN=Leaf");

    public void testQuotedLocalPartAtExcludedHost()
        throws Exception
    {
        Checks.mustRefuse("quoted local part hides the real host",
            Fixture.chain(excluded(email("bank.com")), LEAF,
                names(email("\"a@bench.example\"@bank.com"))));
    }

    public void testQuotedLocalPartAtExcludedDomain()
        throws Exception
    {
        Checks.mustRefuse("quoted local part hides the real host from an excluded domain constraint",
            Fixture.chain(excluded(email("@bank.com")), LEAF,
                names(email("\"a@bench.example\"@bank.com"))));
    }

    public void testQuotedLocalPartWithEscapedQuote()
        throws Exception
    {
        Checks.mustRefuse("quoted local part with an escaped quote hides the real host",
            Fixture.chain(excluded(email("@bank.com")), LEAF,
                names(email("\"a\\\"@bench.example\"@bank.com"))));
    }

    public void testQuotedLocalPartWithSeveralAts()
        throws Exception
    {
        Checks.mustRefuse("quoted local part containing several at signs hides the real host",
            Fixture.chain(excluded(email("bank.com")), LEAF,
                names(email("\"a@b@c\"@bank.com"))));
    }
}
