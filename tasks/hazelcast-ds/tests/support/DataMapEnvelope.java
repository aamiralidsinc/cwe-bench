package benchkit;

import com.hazelcast.internal.serialization.Data;

import java.util.Map;

/** An ordinary user class with a map of data values. */
public class DataMapEnvelope {

    private Map<String, Data> items;

    public DataMapEnvelope() {
    }

    public Map<String, Data> getItems() {
        return items;
    }
}
