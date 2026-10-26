package bench.bcj;

/** Assertions shared by the test classes. A crash is never accepted as a refusal. */
public final class Checks
{
    private Checks()
    {
    }

    public static void mustRefuse(String label, Fixture.Chain chain)
    {
        String refusal = chain.refusal();
        if (refusal == null)
        {
            throw new AssertionError(label + ": the path was accepted but must be refused");
        }
        if (refusal.startsWith("unexpected "))
        {
            throw new AssertionError(label + ": the validator failed instead of refusing the name: " + refusal);
        }
    }

    public static void mustAccept(String label, Fixture.Chain chain)
    {
        String refusal = chain.refusal();
        if (refusal != null)
        {
            throw new AssertionError(label + ": legitimate path was refused: " + refusal);
        }
    }
}
