package benchkit;

/** An ordinary user class with a nested value declared by a concrete serializable class. */
public class CounterEnvelope {

    private CounterPayload payload;

    public CounterEnvelope() {
    }

    public CounterPayload getPayload() {
        return payload;
    }
}
