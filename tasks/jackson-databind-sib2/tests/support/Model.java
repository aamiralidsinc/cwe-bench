package support;

import com.fasterxml.jackson.annotation.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonPOJOBuilder;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Shared data model for the deserialization view-filtering tests.
 *
 * A document-service back-end deserializes externally supplied JSON into these
 * beans. A viewer requests come in under PublicView; privileged tooling uses
 * AdminView. Fields/properties annotated for AdminView must never be populated
 * from the untrusted JSON of a PublicView reader.
 */
public final class Model {
    private Model() {}

    public static class PublicView { }
    public static class AdminView extends PublicView { }

    public static ObjectMapper mapper() { return new ObjectMapper(); }

    // Pretty-prints single quotes -> double quotes so the test literals read cleanly.
    public static String q(String s) { return s.replace('\'', '"'); }

    public static abstract class Asset {
        public String name;
    }

    public static class PublicAsset extends Asset { }

    public static class AdminAsset extends Asset {
        public String secret;
    }

    // Subtype whose admin-only marker is on the field itself.
    public static class FieldGatedAdminAsset extends Asset {
        @JsonView(AdminView.class)
        public String secret;
    }

    // (1) The whole polymorphic property is admin-only; property-based creator.
    public static class PropertyGatedContainer {
        @JsonTypeInfo(use = JsonTypeInfo.Id.NAME,
                include = JsonTypeInfo.As.EXTERNAL_PROPERTY, property = "kind")
        @JsonSubTypes({
                @JsonSubTypes.Type(value = PublicAsset.class, name = "pub"),
                @JsonSubTypes.Type(value = AdminAsset.class, name = "admin")
        })
        @JsonView(AdminView.class)
        public Asset asset;

        public String label;

        @JsonCreator
        public PropertyGatedContainer(
                @JsonProperty("label") String label,
                @JsonProperty("asset") @JsonView(AdminView.class) Asset asset) {
            this.label = label;
            this.asset = asset;
        }
    }

    // (2) Property always visible; resolved subtype has an admin-only field.
    public static class FieldGatedContainer {
        @JsonTypeInfo(use = JsonTypeInfo.Id.NAME,
                include = JsonTypeInfo.As.EXTERNAL_PROPERTY, property = "kind")
        @JsonSubTypes({
                @JsonSubTypes.Type(value = PublicAsset.class, name = "pub"),
                @JsonSubTypes.Type(value = FieldGatedAdminAsset.class, name = "admin")
        })
        public Asset asset;

        public String label;

        @JsonCreator
        public FieldGatedContainer(
                @JsonProperty("label") String label,
                @JsonProperty("asset") Asset asset) {
            this.label = label;
            this.asset = asset;
        }
    }

    // (3) External type id "kind" is ITSELF a creator parameter (visible); the
    // value "asset" is admin-only. Hiding the value must not drop the type id.
    public static class TypeIdCreatorContainer {
        @JsonTypeInfo(use = JsonTypeInfo.Id.NAME,
                include = JsonTypeInfo.As.EXTERNAL_PROPERTY, property = "kind", visible = true)
        @JsonSubTypes({
                @JsonSubTypes.Type(value = PublicAsset.class, name = "pub"),
                @JsonSubTypes.Type(value = AdminAsset.class, name = "admin")
        })
        @JsonView(AdminView.class)
        public Asset asset;

        public String label;
        public String kind;

        @JsonCreator
        public TypeIdCreatorContainer(
                @JsonProperty("label") String label,
                @JsonProperty("kind") String kind,
                @JsonProperty("asset") @JsonView(AdminView.class) Asset asset) {
            this.label = label;
            this.kind = kind;
            this.asset = asset;
        }
    }

    // (4) Admin-only external-type property on a default-constructor bean.
    public static class DefaultCtorContainer {
        @JsonTypeInfo(use = JsonTypeInfo.Id.NAME,
                include = JsonTypeInfo.As.EXTERNAL_PROPERTY, property = "kind")
        @JsonSubTypes({
                @JsonSubTypes.Type(value = PublicAsset.class, name = "pub"),
                @JsonSubTypes.Type(value = AdminAsset.class, name = "admin")
        })
        @JsonView(AdminView.class)
        public Asset asset;

        public String label;
    }

    // (5) Admin-only external-type property on a @JsonPOJOBuilder bean.
    @JsonDeserialize(builder = BuilderContainer.Builder.class)
    public static class BuilderContainer {
        public final String label;
        public final Asset asset;

        BuilderContainer(String label, Asset asset) {
            this.label = label;
            this.asset = asset;
        }

        @JsonPOJOBuilder(withPrefix = "with")
        public static class Builder {
            String label;
            Asset asset;

            public Builder withLabel(String label) { this.label = label; return this; }

            @JsonTypeInfo(use = JsonTypeInfo.Id.NAME,
                    include = JsonTypeInfo.As.EXTERNAL_PROPERTY, property = "kind")
            @JsonSubTypes({
                    @JsonSubTypes.Type(value = PublicAsset.class, name = "pub"),
                    @JsonSubTypes.Type(value = AdminAsset.class, name = "admin")
            })
            @JsonView(AdminView.class)
            public Builder withAsset(Asset asset) { this.asset = asset; return this; }

            public BuilderContainer build() { return new BuilderContainer(label, asset); }
        }
    }

    // ------------------------------------------------------------------
    // Dynamic "extra attributes" beans. A document carries a fixed public
    // label plus a bag of free-form attributes collected from whatever other
    // keys the JSON contains. On these beans that catch-all bag is reserved for
    // privileged tooling, so it is annotated for AdminView: under PublicView no
    // untrusted key may land in it. `label` always binds.
    // ------------------------------------------------------------------

    // (7) Catch-all collected into an admin-only Map field.
    public static class MapExtrasContainer {
        public String label;

        @JsonView(AdminView.class)
        @JsonAnySetter
        public Map<String, Object> extras = new HashMap<>();
    }

    // (8) Catch-all delivered to an admin-only two-arg setter method.
    public static class MethodExtrasContainer {
        public String label;
        public final Map<String, Object> extras = new HashMap<>();

        @JsonView(AdminView.class)
        @JsonAnySetter
        public void put(String key, Object value) { extras.put(key, value); }
    }

    // (9) Catch-all collected into an admin-only JsonNode field.
    public static class NodeExtrasContainer {
        public String label;

        @JsonView(AdminView.class)
        @JsonAnySetter
        public JsonNode extras;
    }

    // (10) Catch-all with NO view restriction: must keep binding under any view
    //      (guards against an over-broad fix that drops every extra attribute).
    public static class OpenExtrasContainer {
        public String label;

        @JsonAnySetter
        public Map<String, Object> extras = new HashMap<>();
    }

    // (6) Reverse of (3): the type id "kind" creator param carries the view, value is visible.
    public static class TypeIdGatedContainer {
        @JsonTypeInfo(use = JsonTypeInfo.Id.NAME,
                include = JsonTypeInfo.As.EXTERNAL_PROPERTY, property = "kind", visible = true)
        @JsonSubTypes({
                @JsonSubTypes.Type(value = PublicAsset.class, name = "pub"),
                @JsonSubTypes.Type(value = AdminAsset.class, name = "admin")
        })
        public Asset asset;

        public String label;
        public String kind;

        @JsonCreator
        public TypeIdGatedContainer(
                @JsonProperty("label") String label,
                @JsonProperty("kind") @JsonView(AdminView.class) String kind,
                @JsonProperty("asset") Asset asset) {
            this.label = label;
            this.kind = kind;
            this.asset = asset;
        }
    }

    // ------------------------------------------------------------------
    // Linked records. Records in one request may point at each other by
    // their identifier ("next": 7 refers to the record whose id is 7). The
    // identifier itself is assigned by the server, so writing it is reserved
    // for AdminView; a PublicView caller may still use identifiers inside the
    // request to link its records together.
    // ------------------------------------------------------------------

    // (11) Linked record built with a no-arg constructor and fields.
    @JsonIdentityInfo(generator = ObjectIdGenerators.PropertyGenerator.class, property = "id")
    public static class LinkedRecord {
        @JsonView(AdminView.class)
        public int id;

        public String name;
        public LinkedRecord next;
    }

    // (12) Linked record built through a constructor.
    @JsonIdentityInfo(generator = ObjectIdGenerators.PropertyGenerator.class, property = "id")
    public static class LinkedCreatorRecord {
        @JsonView(AdminView.class)
        public int id;

        public final String name;
        public LinkedCreatorRecord next;

        @JsonCreator
        public LinkedCreatorRecord(@JsonProperty("name") String name) {
            this.name = name;
        }
    }

    // ------------------------------------------------------------------
    // Compact entries travel as JSON arrays ["label", "owner", [roles], "note"].
    // Owner and roles are reserved for AdminView.
    // ------------------------------------------------------------------

    // (13) Compact, array-shaped entry.
    @JsonFormat(shape = JsonFormat.Shape.ARRAY)
    @JsonPropertyOrder({"label", "owner", "roles", "note"})
    public static class CompactEntry {
        public String label;

        @JsonView(AdminView.class)
        public String owner;

        @JsonView(AdminView.class)
        public List<String> roles = new ArrayList<>();

        public String note;

        public static CompactEntry existing() {
            CompactEntry e = new CompactEntry();
            e.label = "old-label";
            e.owner = "alice";
            e.roles = new ArrayList<>(List.of("reader"));
            e.note = "old-note";
            return e;
        }
    }

    // (14) Settings document whose entry starts from server defaults and
    //      takes the request's values on top of them.
    public static class EntrySettings {
        public String title;

        @JsonMerge
        public CompactEntry entry = defaults();

        public static CompactEntry defaults() {
            CompactEntry e = new CompactEntry();
            e.label = "default-label";
            e.owner = "system";
            e.roles = new ArrayList<>(List.of("viewer"));
            e.note = "default-note";
            return e;
        }
    }
}
