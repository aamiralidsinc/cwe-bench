package functional;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

/**
 * Legitimate uses of the creator-parameter "extra attributes" feature. These
 * must keep working: a fix that over-restricts (drops the creator-parameter
 * catch-all whenever any view is active, or drops a catch-all that carries no
 * view restriction) breaks at least one of these.
 */
public class AnySetterCreatorFeatureTest {
    private final ObjectMapper MAPPER = Model.mapper();

    private static final String JSON = Model.q(
            "{'label':'hi','secret':'shh','role':'root'}");

    // With AdminView the admin-only Map creator-parameter catch-all IS populated.
    @Test
    void adminSeesMapParamExtras() throws Exception {
        MapParamExtrasContainer r = MAPPER.readerWithView(AdminView.class)
                .forType(MapParamExtrasContainer.class).readValue(JSON);
        assertEquals("hi", r.label);
        assertNotNull(r.extras);
        assertEquals("shh", r.extras.get("secret"));
        assertEquals("root", r.extras.get("role"));
    }

    // With AdminView the admin-only JsonNode creator-parameter catch-all IS populated.
    @Test
    void adminSeesNodeParamExtras() throws Exception {
        NodeParamExtrasContainer r = MAPPER.readerWithView(AdminView.class)
                .forType(NodeParamExtrasContainer.class).readValue(JSON);
        assertEquals("hi", r.label);
        assertNotNull(r.extras, "admin view should populate the JsonNode creator-parameter catch-all");
        JsonNode extras = r.extras;
        assertEquals("shh", extras.path("secret").asText());
        assertEquals("root", extras.path("role").asText());
    }

    // With no active view everything binds, including the creator-parameter catch-all.
    @Test
    void noViewBindsMapParamExtras() throws Exception {
        MapParamExtrasContainer r = MAPPER.readerFor(MapParamExtrasContainer.class).readValue(JSON);
        assertNotNull(r.extras);
        assertEquals("shh", r.extras.get("secret"));
        assertEquals("root", r.extras.get("role"));
    }

    // A creator-parameter catch-all with NO view restriction must keep
    // collecting under the restricted PublicView: the fix must not drop every
    // creator-parameter catch-all.
    @Test
    void unrestrictedParamExtrasStillBindUnderPublicView() throws Exception {
        OpenParamExtrasContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(OpenParamExtrasContainer.class).readValue(JSON);
        assertEquals("hi", r.label);
        assertNotNull(r.extras);
        assertEquals("shh", r.extras.get("secret"));
        assertEquals("root", r.extras.get("role"));
    }

    // The public label on a bean whose creator-parameter catch-all is admin-gated
    // still binds under PublicView: filtering the catch-all must not drop the
    // public constructor properties.
    @Test
    void publicLabelStillBindsOnGatedParamCatchAllBean() throws Exception {
        MapParamExtrasContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(MapParamExtrasContainer.class).readValue(JSON);
        assertEquals("hi", r.label);
    }
}
