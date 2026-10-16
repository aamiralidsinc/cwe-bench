package functional;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

/**
 * Legitimate uses of the catch-all "extra attributes" feature. These must keep
 * working: a fix that over-restricts (drops the catch-all whenever any view is
 * active, or drops catch-alls that carry no view restriction) breaks at least
 * one of these.
 */
public class AnySetterFeatureTest {
    private final ObjectMapper MAPPER = Model.mapper();

    private static final String JSON = Model.q(
            "{'label':'hi','secret':'shh','role':'root'}");

    // With AdminView the admin-only catch-all IS populated (map-field path).
    @Test
    void adminSeesMapExtras() throws Exception {
        MapExtrasContainer r = MAPPER.readerWithView(AdminView.class)
                .forType(MapExtrasContainer.class).readValue(JSON);
        assertEquals("hi", r.label);
        assertEquals("shh", r.extras.get("secret"));
        assertEquals("root", r.extras.get("role"));
    }

    // With no active view everything binds, including the catch-all.
    @Test
    void noViewBindsMapExtras() throws Exception {
        MapExtrasContainer r = MAPPER.readerFor(MapExtrasContainer.class).readValue(JSON);
        assertEquals("shh", r.extras.get("secret"));
        assertEquals("root", r.extras.get("role"));
    }

    // Admin view populates the catch-all through the setter-method path too.
    @Test
    void adminSeesMethodExtras() throws Exception {
        MethodExtrasContainer r = MAPPER.readerWithView(AdminView.class)
                .forType(MethodExtrasContainer.class).readValue(JSON);
        assertEquals("shh", r.extras.get("secret"));
        assertEquals("root", r.extras.get("role"));
    }

    // Admin view populates the JsonNode catch-all.
    @Test
    void adminSeesNodeExtras() throws Exception {
        NodeExtrasContainer r = MAPPER.readerWithView(AdminView.class)
                .forType(NodeExtrasContainer.class).readValue(JSON);
        assertNotNull(r.extras, "admin view should populate the JsonNode catch-all");
        JsonNode extras = r.extras;
        assertEquals("shh", extras.path("secret").asText());
        assertEquals("root", extras.path("role").asText());
    }

    // A catch-all with NO view restriction must keep collecting under the
    // restricted PublicView: the fix must not drop every catch-all.
    @Test
    void unrestrictedExtrasStillBindUnderPublicView() throws Exception {
        OpenExtrasContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(OpenExtrasContainer.class).readValue(JSON);
        assertEquals("hi", r.label);
        assertEquals("shh", r.extras.get("secret"));
        assertEquals("root", r.extras.get("role"));
    }

    // The public label on a bean whose catch-all is admin-gated still binds
    // under PublicView: filtering the catch-all must not drop public properties.
    @Test
    void publicLabelStillBindsOnGatedCatchAllBean() throws Exception {
        MapExtrasContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(MapExtrasContainer.class).readValue(JSON);
        assertEquals("hi", r.label);
    }
}
