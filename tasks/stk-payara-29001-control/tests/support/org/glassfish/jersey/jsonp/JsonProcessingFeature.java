package org.glassfish.jersey.jsonp;
import jakarta.ws.rs.core.Feature;
import jakarta.ws.rs.core.FeatureContext;
public class JsonProcessingFeature implements Feature {
    @Override public boolean configure(FeatureContext context) { return true; }
}
