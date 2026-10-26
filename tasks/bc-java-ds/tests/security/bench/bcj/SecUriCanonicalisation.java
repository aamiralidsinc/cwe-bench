package bench.bcj;

import static bench.bcj.Fixture.dn;
import static bench.bcj.Fixture.excluded;
import static bench.bcj.Fixture.names;
import static bench.bcj.Fixture.uri;

/**
 * A URI host written with its root label must be judged as the same host it denotes, on either
 * side of the comparison and wherever the host sits in the authority.
 */
public class SecUriCanonicalisation
{
    private static final org.bouncycastle.asn1.x500.X500Name LEAF = dn("C=US, O=Bench, CN=Leaf");

    public void testExcludedHostWithRootDotOnName()
        throws Exception
    {
        Checks.mustRefuse("URI host written with its root label",
            Fixture.chain(excluded(uri("competitor.example")), LEAF,
                names(uri("https://competitor.example./report"))));
    }

    public void testExcludedHostWithRootDotBeforePort()
        throws Exception
    {
        Checks.mustRefuse("URI host written with its root label and a port",
            Fixture.chain(excluded(uri("competitor.example")), LEAF,
                names(uri("https://competitor.example.:443/report"))));
    }

    public void testExcludedHostWithRootDotOnConstraint()
        throws Exception
    {
        Checks.mustRefuse("excluded URI host written with its root label",
            Fixture.chain(excluded(uri("competitor.example.")), LEAF,
                names(uri("https://competitor.example/report"))));
    }

    public void testExcludedHostWithRootDotBehindUserInfo()
        throws Exception
    {
        Checks.mustRefuse("URI host written with its root label behind user information",
            Fixture.chain(excluded(uri("competitor.example")), LEAF,
                names(uri("https://user@competitor.example./report"))));
    }

    public void testExcludedHostWithRootDotAndQuery()
        throws Exception
    {
        Checks.mustRefuse("URI host written with its root label, with a query",
            Fixture.chain(excluded(uri("competitor.example")), LEAF,
                names(uri("https://competitor.example.?q=1"))));
    }
}
