package benchkit;

/** An ordinary user class handled by an explicitly registered compact serializer. */
public class CustomPayload {

    private int value;

    public CustomPayload() {
    }

    public CustomPayload(int value) {
        this.value = value;
    }

    public int value() {
        return value;
    }
}
