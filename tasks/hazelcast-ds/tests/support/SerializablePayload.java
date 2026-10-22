package benchkit;

import java.io.Serializable;

/** A user class that is already serializable through Java serialization. */
public class SerializablePayload implements Serializable {

    private int value;

    public SerializablePayload() {
    }

    public SerializablePayload(int value) {
        this.value = value;
    }

    public int value() {
        return value;
    }
}
