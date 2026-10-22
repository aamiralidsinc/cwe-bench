package benchkit;

import com.hazelcast.internal.serialization.Data;

import java.util.Map;

/** An ordinary user class with a map whose keys are declared by their interface. */
public class KeyedMapEnvelope {

    private Map<Payload, Data> items;

    public KeyedMapEnvelope() {
    }

    public Map<Payload, Data> getItems() {
        return items;
    }
}
