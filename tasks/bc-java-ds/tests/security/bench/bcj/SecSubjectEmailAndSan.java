package bench.bcj;

import static bench.bcj.Fixture.email;
import static bench.bcj.Fixture.excluded;
import static bench.bcj.Fixture.names;
import static bench.bcj.Fixture.permitted;

/**
 * Every email address a certificate carries is subject to the email name constraints, whichever
 * attribute holds it and whatever else the certificate also carries.
 */
public class SecSubjectEmailAndSan
{
    public void testExcludedSubjectEmailBesideAllowedSanEmail()
        throws Exception
    {
        Checks.mustRefuse("excluded address in the subject DN beside an allowed alternative name",
            Fixture.chain(excluded(email("bank.com")), Fixture.dnWithEmail("ceo@bank.com"),
                names(email("ok@bench.example"))));
    }

    public void testSubjectEmailOutsidePermittedSetBesideAllowedSanEmail()
        throws Exception
    {
        Checks.mustRefuse("address outside the permitted set in the subject DN beside an allowed alternative name",
            Fixture.chain(permitted(email(".bench.example")), Fixture.dnWithEmail("ceo@other.example"),
                names(email("ok@sub.bench.example"))));
    }
}
