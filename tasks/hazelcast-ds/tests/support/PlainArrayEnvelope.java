package benchkit;

/** An ordinary user class with an array of values declared by a concrete plain class. */
public class PlainArrayEnvelope {

    private PlainPayload[] items;

    public PlainArrayEnvelope() {
    }

    public PlainArrayEnvelope(PlainPayload[] items) {
        this.items = items;
    }

    public PlainPayload[] getItems() {
        return items;
    }
}
