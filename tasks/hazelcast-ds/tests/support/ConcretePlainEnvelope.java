package benchkit;

/** An ordinary user class with a nested value declared by a concrete plain class. */
public class ConcretePlainEnvelope {

    private PlainPayload payload;

    public ConcretePlainEnvelope() {
    }

    public ConcretePlainEnvelope(PlainPayload payload) {
        this.payload = payload;
    }

    public PlainPayload getPayload() {
        return payload;
    }
}
