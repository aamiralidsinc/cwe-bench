package security;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Each test reads attacker-controlled JSON with the less-privileged PublicView
 * active and asserts that an AdminView-only property/parameter is NOT populated.
 * On vulnerable code the value leaks in (test fails); a correct fix leaves it
 * unbound (test passes). Every path that can set a property must be covered.
 */
public class ViewBypassTest {
    private final ObjectMapper MAPPER = Model.mapper();

    private static final String JSON = Model.q(
            "{'label':'hello','kind':'admin','asset':{'name':'foo','secret':'LEAKED'}}");

    // Creator (property-based @JsonCreator) path.
    @Test
    void creatorPropertyHidden() throws Exception {
        PropertyGatedContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(PropertyGatedContainer.class).readValue(JSON);
        assertEquals("hello", r.label);
        assertNull(r.asset, "admin-only 'asset' leaked under PublicView (creator path)");
    }

    // Default-constructor bean path (eager binding via complete(bean)).
    @Test
    void defaultCtorPropertyHidden() throws Exception {
        DefaultCtorContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(DefaultCtorContainer.class).readValue(JSON);
        assertEquals("hello", r.label);
        assertNull(r.asset, "admin-only 'asset' leaked under PublicView (default-ctor path)");
    }

    // @JsonPOJOBuilder path.
    @Test
    void builderPropertyHidden() throws Exception {
        BuilderContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(BuilderContainer.class).readValue(JSON);
        assertEquals("hello", r.label);
        assertNull(r.asset, "admin-only 'asset' leaked under PublicView (builder path)");
    }

    // Creator path where the external type id is itself a (visible) creator
    // parameter: only the value is admin-only. The value must not bind.
    @Test
    void creatorValueHiddenTypeIdVisible() throws Exception {
        TypeIdCreatorContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(TypeIdCreatorContainer.class).readValue(JSON);
        assertNull(r.asset, "admin-only 'asset' leaked under PublicView (type-id-creator path)");
    }

    // Reverse: the external-type-id creator parameter carries the view. The
    // hidden type id parameter must not be bound (the resolved value may still bind).
    @Test
    void typeIdCreatorParamHidden() throws Exception {
        TypeIdGatedContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(TypeIdGatedContainer.class).readValue(JSON);
        assertNull(r.kind, "admin-only type id 'kind' leaked under PublicView");
    }
}
