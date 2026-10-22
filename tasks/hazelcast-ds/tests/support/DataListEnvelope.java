package benchkit;

import com.hazelcast.internal.serialization.Data;

import java.util.List;

/** An ordinary user class with a list of data values. */
public class DataListEnvelope {

    private List<Data> items;

    public DataListEnvelope() {
    }

    public List<Data> getItems() {
        return items;
    }
}
