package bench.bcj;

import static bench.bcj.Fixture.dn;
import static bench.bcj.Fixture.excluded;
import static bench.bcj.Fixture.names;
import static bench.bcj.Fixture.permitted;
import static bench.bcj.Fixture.uri;

/**
 * URI subtrees are matched on the host of the URI, in the two documented forms.
 */
public class FunUriConstraints
{
    private static final org.bouncycastle.asn1.x500.X500Name LEAF = dn("C=US, O=Bench, CN=Leaf");

    public void testExactHostFormMatchesThatHostOnly()
        throws Exception
    {
        Checks.mustAccept("URI at the permitted host",
            Fixture.chain(permitted(uri("competitor.example")), LEAF,
                names(uri("https://competitor.example/report"))));
        Checks.mustRefuse("URI at a subdomain of the permitted host",
            Fixture.chain(permitted(uri("competitor.example")), LEAF,
                names(uri("https://sub.competitor.example/report"))));
    }

    public void testDomainFormMatchesSubdomains()
        throws Exception
    {
        Checks.mustAccept("URI in a permitted domain",
            Fixture.chain(permitted(uri(".competitor.example")), LEAF,
                names(uri("https://sub.competitor.example/report"))));
        Checks.mustRefuse("URI at the domain itself",
            Fixture.chain(permitted(uri(".competitor.example")), LEAF,
                names(uri("https://competitor.example/report"))));
    }

    public void testPortAndPathAreNotPartOfTheHost()
        throws Exception
    {
        Checks.mustRefuse("URI with a port at the excluded host",
            Fixture.chain(excluded(uri("competitor.example")), LEAF,
                names(uri("https://competitor.example:8443/report"))));
        Checks.mustAccept("URI at another host with a similar path",
            Fixture.chain(excluded(uri("competitor.example")), LEAF,
                names(uri("https://other.example/competitor.example/report"))));
    }

    public void testUserInformationIsNotTheHost()
        throws Exception
    {
        Checks.mustAccept("URI whose user information names the excluded host",
            Fixture.chain(excluded(uri("competitor.example")), LEAF,
                names(uri("https://competitor.example@other.example/report"))));
    }

    public void testQueryIsNotPartOfTheHost()
        throws Exception
    {
        Checks.mustAccept("URI whose query names the excluded host",
            Fixture.chain(excluded(uri("competitor.example")), LEAF,
                names(uri("https://other.example/report?next=https://competitor.example"))));
    }
}
