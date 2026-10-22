package benchkit;

import java.io.Serializable;
import java.util.concurrent.atomic.AtomicInteger;

/** A user class that is already serializable through Java serialization. */
public class CounterPayload implements Payload, Serializable {

    public static final AtomicInteger CONSTRUCTIONS = new AtomicInteger();

    private int value;

    public CounterPayload() {
        CONSTRUCTIONS.incrementAndGet();
    }

    public CounterPayload(int value) {
        CONSTRUCTIONS.incrementAndGet();
        this.value = value;
    }

    @Override
    public int value() {
        return value;
    }
}
