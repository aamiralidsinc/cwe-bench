package support;

import com.fasterxml.jackson.annotation.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonPOJOBuilder;

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
}
