package benchkit;

/** An ordinary user class with a nested value declared by its interface. */
public class PlainEnvelope {

    private Payload payload;
    private String label;

    public PlainEnvelope() {
    }

    public PlainEnvelope(Payload payload, String label) {
        this.payload = payload;
        this.label = label;
    }

    public Payload getPayload() {
        return payload;
    }

    public String getLabel() {
        return label;
    }
}
