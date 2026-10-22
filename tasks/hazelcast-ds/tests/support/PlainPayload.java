package benchkit;

/** An ordinary user class with no other serialization mechanism. */
public class PlainPayload implements Payload {

    private int value;

    public PlainPayload() {
    }

    public PlainPayload(int value) {
        this.value = value;
    }

    @Override
    public int value() {
        return value;
    }
}
