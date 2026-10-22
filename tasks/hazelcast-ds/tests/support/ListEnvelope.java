package benchkit;

import java.util.List;

/** An ordinary user class with a list of values declared by their interface. */
public class ListEnvelope {

    private List<Payload> items;

    public ListEnvelope() {
    }

    public ListEnvelope(List<Payload> items) {
        this.items = items;
    }

    public List<Payload> getItems() {
        return items;
    }
}
