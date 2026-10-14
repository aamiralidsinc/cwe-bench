package security;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * A second, sibling place the same mistake lives: the view filter is consulted
 * for mapped bean properties but NOT for the catch-all that collects otherwise
 * unmapped keys. When that catch-all is restricted to a privileged view, a
 * caller reading under the less-privileged PublicView must NOT have attacker
 * keys routed into it. On vulnerable code the keys leak in (test fails); a
 * correct, general fix leaves the catch-all empty (test passes).
 *
 * Each test goes through the real public API and uses the lower PublicView.
 */
public class AnySetterBypassTest {
    private final ObjectMapper MAPPER = Model.mapper();

    // Extra, unmapped keys an attacker adds next to the public label.
    private static final String JSON = Model.q(
            "{'label':'hi','secret':'LEAKED','role':'root'}");

    // Catch-all collected into an admin-only Map field.
    @Test
    void mapExtrasHidden() throws Exception {
        MapExtrasContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(MapExtrasContainer.class).readValue(JSON);
        assertEquals("hi", r.label);
        assertTrue(r.extras.isEmpty(),
                "admin-only catch-all 'extras' collected attacker keys under PublicView (map-field path)");
    }

    // Catch-all delivered to an admin-only two-arg setter method.
    @Test
    void methodExtrasHidden() throws Exception {
        MethodExtrasContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(MethodExtrasContainer.class).readValue(JSON);
        assertEquals("hi", r.label);
        assertTrue(r.extras.isEmpty(),
                "admin-only catch-all 'extras' collected attacker keys under PublicView (setter-method path)");
    }

    // Catch-all collected into an admin-only JsonNode field.
    @Test
    void nodeExtrasHidden() throws Exception {
        NodeExtrasContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(NodeExtrasContainer.class).readValue(JSON);
        assertEquals("hi", r.label);
        assertNull(r.extras,
                "admin-only catch-all 'extras' collected attacker keys under PublicView (json-node path)");
    }
}
