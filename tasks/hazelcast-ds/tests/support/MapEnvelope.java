package benchkit;

import java.util.Map;

/** An ordinary user class with a map of values declared by their interface. */
public class MapEnvelope {

    private Map<String, Payload> items;

    public MapEnvelope() {
    }

    public MapEnvelope(Map<String, Payload> items) {
        this.items = items;
    }

    public Map<String, Payload> getItems() {
        return items;
    }
}
