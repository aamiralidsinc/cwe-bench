package functional;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertNotNull;

/**
 * Legitimate uses of external-type-id deserialization with @JsonView. These must
 * keep working: a fix that over-restricts (drops the property whenever any view
 * is active, or deletes the feature) breaks at least one of these.
 */
public class ViewFeatureTest {
    private final ObjectMapper MAPPER = Model.mapper();

    private static final String ADMIN_JSON = Model.q(
            "{'label':'hello','kind':'admin','asset':{'name':'foo','secret':'shh'}}");
    private static final String PUB_JSON = Model.q(
            "{'label':'hi','kind':'pub','asset':{'name':'bar'}}");
    // Value before its sibling discriminator: equally valid JSON (member order is free).
    private static final String ADMIN_JSON_VALUE_FIRST = Model.q(
            "{'label':'hello','asset':{'name':'foo','secret':'shh'},'kind':'admin'}");

    // With AdminView the admin-only property IS bound (creator path).
    @Test
    void adminSeesGatedProperty() throws Exception {
        PropertyGatedContainer r = MAPPER.readerWithView(AdminView.class)
                .forType(PropertyGatedContainer.class).readValue(ADMIN_JSON);
        AdminAsset a = assertInstanceOf(AdminAsset.class, r.asset);
        assertEquals("foo", a.name);
        assertEquals("shh", a.secret);
    }

    // With no active view at all, everything binds as normal.
    @Test
    void noViewBindsEverything() throws Exception {
        PropertyGatedContainer r = MAPPER.readerFor(PropertyGatedContainer.class)
                .readValue(ADMIN_JSON);
        AdminAsset a = assertInstanceOf(AdminAsset.class, r.asset);
        assertEquals("shh", a.secret);
    }

    // Non-gated properties still bind under the restricted view (creator path).
    @Test
    void publicPropertiesStillBindUnderPublicView() throws Exception {
        PropertyGatedContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(PropertyGatedContainer.class).readValue(ADMIN_JSON);
        assertEquals("hello", r.label);
    }

    // Default-ctor bean: admin view binds the property.
    @Test
    void adminSeesGatedPropertyDefaultCtor() throws Exception {
        DefaultCtorContainer r = MAPPER.readerWithView(AdminView.class)
                .forType(DefaultCtorContainer.class).readValue(ADMIN_JSON);
        assertNotNull(r.asset);
        assertInstanceOf(AdminAsset.class, r.asset);
    }

    // Builder bean: admin view binds the property.
    @Test
    void adminSeesGatedPropertyBuilder() throws Exception {
        BuilderContainer r = MAPPER.readerWithView(AdminView.class)
                .forType(BuilderContainer.class).readValue(ADMIN_JSON);
        assertNotNull(r.asset);
        assertInstanceOf(AdminAsset.class, r.asset);
    }

    // Value before discriminator: admin view still binds it (default-ctor and builder).
    @Test
    void adminSeesGatedPropertyValueFirst() throws Exception {
        DefaultCtorContainer d = MAPPER.readerWithView(AdminView.class)
                .forType(DefaultCtorContainer.class).readValue(ADMIN_JSON_VALUE_FIRST);
        AdminAsset a = assertInstanceOf(AdminAsset.class, d.asset);
        assertEquals("shh", a.secret);
        BuilderContainer b = MAPPER.readerWithView(AdminView.class)
                .forType(BuilderContainer.class).readValue(ADMIN_JSON_VALUE_FIRST);
        AdminAsset ba = assertInstanceOf(AdminAsset.class, b.asset);
        assertEquals("shh", ba.secret);
    }

    // A view never rewrites the type id: with the property visible but a field
    // of the resolved subtype admin-gated, the subtype still resolves and only
    // the gated field is withheld under PublicView.
    @Test
    void visiblePropertyResolvesSubtypeFieldGated() throws Exception {
        FieldGatedContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(FieldGatedContainer.class).readValue(ADMIN_JSON);
        FieldGatedAdminAsset a = assertInstanceOf(FieldGatedAdminAsset.class, r.asset);
        assertEquals("foo", a.name);
    }

    // Case 6 feature half: the value carries no view, so under PublicView it is
    // still bound and the type id still selects the correct subtype.
    @Test
    void visibleValueStillBoundWhenTypeIdGated() throws Exception {
        TypeIdGatedContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(TypeIdGatedContainer.class).readValue(ADMIN_JSON);
        AdminAsset a = assertInstanceOf(AdminAsset.class, r.asset);
        assertEquals("foo", a.name);
    }

    // Case 3 feature half: the visible type id creator property is still bound
    // even though the value it describes is withheld under PublicView.
    @Test
    void visibleTypeIdCreatorPropStillBound() throws Exception {
        TypeIdCreatorContainer r = MAPPER.readerWithView(PublicView.class)
                .forType(TypeIdCreatorContainer.class).readValue(ADMIN_JSON);
        assertEquals("admin", r.kind);
    }

    // A fully public document round-trips under PublicView.
    @Test
    void publicAssetUnderPublicView() throws Exception {
        PropertyGatedContainer r = MAPPER.readerWithView(AdminView.class)
                .forType(PropertyGatedContainer.class).readValue(PUB_JSON);
        PublicAsset a = assertInstanceOf(PublicAsset.class, r.asset);
        assertEquals("bar", a.name);
    }
}
