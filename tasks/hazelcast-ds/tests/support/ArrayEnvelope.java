package benchkit;

/** An ordinary user class with an array of values declared by their interface. */
public class ArrayEnvelope {

    private Payload[] items;

    public ArrayEnvelope() {
    }

    public ArrayEnvelope(Payload[] items) {
        this.items = items;
    }

    public Payload[] getItems() {
        return items;
    }
}
