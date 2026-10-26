package bench.bcj;

import static bench.bcj.Fixture.dn;
import static bench.bcj.Fixture.email;
import static bench.bcj.Fixture.excluded;
import static bench.bcj.Fixture.names;
import static bench.bcj.Fixture.permitted;

/**
 * The four forms an email subtree can take keep their documented meaning.
 */
public class FunEmailConstraints
{
    private static final org.bouncycastle.asn1.x500.X500Name LEAF = dn("C=US, O=Bench, CN=Leaf");

    public void testHostFormPermitsExactHostOnly()
        throws Exception
    {
        Checks.mustAccept("mail at the permitted host",
            Fixture.chain(permitted(email("bench.example")), LEAF, names(email("ceo@bench.example"))));
        Checks.mustRefuse("mail at a subdomain of the permitted host",
            Fixture.chain(permitted(email("bench.example")), LEAF, names(email("ceo@sub.bench.example"))));
    }

    public void testDomainFormPermitsSubdomains()
        throws Exception
    {
        Checks.mustAccept("mail in a permitted domain",
            Fixture.chain(permitted(email(".bench.example")), LEAF, names(email("ceo@sub.bench.example"))));
        Checks.mustRefuse("mail at the domain itself, not in a permitted subtree",
            Fixture.chain(permitted(email(".bench.example")), LEAF, names(email("ceo@bench.example"))));
        Checks.mustRefuse("mail in another domain",
            Fixture.chain(permitted(email(".bench.example")), LEAF, names(email("ceo@other.example"))));
    }

    public void testMailboxFormPermitsOnlyThatMailbox()
        throws Exception
    {
        Checks.mustAccept("the permitted mailbox",
            Fixture.chain(permitted(email("ceo@bench.example")), LEAF, names(email("ceo@bench.example"))));
        Checks.mustRefuse("another mailbox at the same host",
            Fixture.chain(permitted(email("ceo@bench.example")), LEAF, names(email("other@bench.example"))));
    }

    public void testExcludedHostFormMatchesExactHostOnly()
        throws Exception
    {
        Checks.mustRefuse("mail at the excluded host",
            Fixture.chain(excluded(email("bank.com")), LEAF, names(email("ceo@bank.com"))));
        Checks.mustAccept("mail at a subdomain of the excluded host",
            Fixture.chain(excluded(email("bank.com")), LEAF, names(email("ceo@sub.bank.com"))));
        Checks.mustAccept("mail at a host that merely ends with the excluded name",
            Fixture.chain(excluded(email("bank.com")), LEAF, names(email("ceo@notbank.com"))));
    }

    public void testExcludedDomainFormMatchesSubdomains()
        throws Exception
    {
        Checks.mustRefuse("mail in the excluded domain",
            Fixture.chain(excluded(email(".bank.com")), LEAF, names(email("ceo@sub.bank.com"))));
        Checks.mustRefuse("mail in the excluded domain, host written with its root label",
            Fixture.chain(excluded(email(".bank.com")), LEAF, names(email("ceo@sub.bank.com."))));
        Checks.mustAccept("mail outside the excluded domain",
            Fixture.chain(excluded(email(".bank.com")), LEAF, names(email("ceo@bank.com"))));
    }

    public void testCaseOfTheHostDoesNotMatter()
        throws Exception
    {
        Checks.mustRefuse("excluded host in another case",
            Fixture.chain(excluded(email("Bank.Com")), LEAF, names(email("ceo@BANK.COM"))));
        Checks.mustAccept("permitted host in another case",
            Fixture.chain(permitted(email("bench.example")), LEAF, names(email("ceo@BENCH.EXAMPLE"))));
    }
}
