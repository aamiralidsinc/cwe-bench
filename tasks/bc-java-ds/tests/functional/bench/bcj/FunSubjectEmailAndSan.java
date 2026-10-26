package bench.bcj;

import static bench.bcj.Fixture.dn;
import static bench.bcj.Fixture.email;
import static bench.bcj.Fixture.excluded;
import static bench.bcj.Fixture.names;
import static bench.bcj.Fixture.permitted;
import static bench.bcj.Fixture.uri;

/**
 * Certificates that carry an address in the subject DN keep validating when every name they carry
 * is allowed.
 */
public class FunSubjectEmailAndSan
{
    public void testSubjectEmailAndSanEmailBothPermitted()
        throws Exception
    {
        Checks.mustAccept("subject address and alternative name both inside the permitted set",
            Fixture.chain(permitted(email(".bench.example")), Fixture.dnWithEmail("ceo@sub.bench.example"),
                names(email("ok@sub.bench.example"))));
    }

    public void testSubjectEmailAndSanUriBothPermitted()
        throws Exception
    {
        Checks.mustAccept("subject address and URI alternative name both inside the permitted set",
            Fixture.chain(permitted(email(".bench.example")),
                Fixture.dnWithEmail("ceo@sub.bench.example"), names(uri("https://sub.bench.example/report"))));
    }

    public void testSubjectEmailExcludedWithoutAlternativeName()
        throws Exception
    {
        Checks.mustRefuse("excluded subject address with no alternative name",
            Fixture.chain(excluded(email("bank.com")), Fixture.dnWithEmail("ceo@bank.com"), null));
    }

    public void testSubjectEmailAndUriBothExcluded()
        throws Exception
    {
        Checks.mustRefuse("excluded subject address beside an excluded alternative name",
            Fixture.chain(excluded(email("bank.com"), uri("bank.com")), Fixture.dnWithEmail("ceo@bank.com"),
                names(uri("https://bank.com/report"))));
    }
}
