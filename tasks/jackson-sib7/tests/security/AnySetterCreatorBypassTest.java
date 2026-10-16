package security;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * A further, distinct place the same mistake lives: when the free-form "extra
 * attributes" bag is declared as a CONSTRUCTOR parameter (an any-setter on a
 * creator argument), the bean is built through the property-based creator and
 * the unmapped keys are collected on a different binding route than the
 * field/method catch-alls. The view filter is likewise not consulted there, so
 * a caller reading under the less-privileged PublicView still has attacker keys
 * routed into the admin-only bag. On vulnerable code the keys leak in (test
 * fails); a correct, general fix leaves the bag empty (test passes).
 *
 * Each test goes through the real public API and uses the lower PublicView.
 */
public class AnySetterCreatorBypassTest {
    private final ObjectMapper MAPPER = Model.mapper();

    private static final String JSON = Model.q(
            "{'label':'hi','secret':'LEAKED','role':'root'}");

    // Catch-all collected into an admin-only Map creator parameter.
    @Test
    void mapParamExtrasHidden() throws Exception {
        MapParamExtrasContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(MapParamExtrasContainer.class).readValue(JSON);
        assertEquals("hi", r.label);
        assertTrue(r.extras == null || r.extras.isEmpty(),
                "admin-only catch-all 'extras' collected attacker keys under PublicView (map-creator-parameter path)");
    }

    // Catch-all collected into an admin-only JsonNode creator parameter.
    @Test
    void nodeParamExtrasHidden() throws Exception {
        NodeParamExtrasContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(NodeParamExtrasContainer.class).readValue(JSON);
        assertEquals("hi", r.label);
        assertTrue(r.extras == null || r.extras.size() == 0,
                "admin-only catch-all 'extras' collected attacker keys under PublicView (json-node-creator-parameter path)");
    }
}
