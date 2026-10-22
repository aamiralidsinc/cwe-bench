package benchkit;

/** An ordinary user class with a nested value declared by a concrete class. */
public class ConcreteEnvelope {

    private SerializablePayload payload;

    public ConcreteEnvelope() {
    }

    public ConcreteEnvelope(SerializablePayload payload) {
        this.payload = payload;
    }

    public SerializablePayload getPayload() {
        return payload;
    }
}
