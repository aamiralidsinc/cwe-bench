package functional;

import com.fasterxml.jackson.annotation.*;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import java.beans.ConstructorProperties;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Cases ported from the library's own test suite (Apache License 2.0):
 * src/test/java/com/fasterxml/jackson/databind/deser/filter/ReadOrWriteOnlyTest.java
 * and the ignoral cases of .../deser/AnySetterTest.java, adapted to plain JUnit.
 */
public class UpstreamReadOnlyTest {

    static class ReadXWriteY {
        @JsonProperty(access = JsonProperty.Access.READ_ONLY)
        public int x = 1;

        @JsonProperty(access = JsonProperty.Access.WRITE_ONLY)
        public int y = 2;

        public void setX(int x) { throw new Error("Should NOT set x"); }

        public int getY() { throw new Error("Should NOT get y"); }
    }

    public static class Pojo935 {
        private String firstName = "Foo";
        private String lastName = "Bar";

        @JsonProperty(access = JsonProperty.Access.READ_ONLY)
        public String getFullName() { return firstName + " " + lastName; }

        public String getFirstName() { return firstName; }
        public void setFirstName(String n) { firstName = n; }
        public String getLastName() { return lastName; }
        public void setLastName(String n) { lastName = n; }
    }

    static class Foo1345 {
        @JsonProperty(access = JsonProperty.Access.READ_ONLY)
        public String id;
        public String name;

        @ConstructorProperties({ "id", "name" })
        public Foo1345(String id, String name) { this.id = id; this.name = name; }

        protected Foo1345() { }
    }

    static class Foo1382 {
        @JsonProperty(access = JsonProperty.Access.READ_ONLY)
        private List<Long> list = new ArrayList<>();

        List<Long> getList() { return list; }

        public Foo1382 setList(List<Long> list) { this.list = list; return this; }
    }

    static class UserWithReadOnly1805 {
        public String name;

        @JsonProperty(access = JsonProperty.Access.READ_ONLY)
        public List<String> getRoles() { return Arrays.asList("admin", "monitor"); }
    }

    @JsonIgnoreProperties(value = { "roles" }, allowGetters = true)
    static class UserAllowGetters1805 {
        public String name;

        public List<String> getRoles() { return Arrays.asList("admin", "monitor"); }
    }

    static class Bean2779 {
        String works;

        @JsonProperty(value = "t", access = JsonProperty.Access.READ_ONLY)
        public String getDoesntWork() { return "pleaseFixThisBug"; }

        public String getWorks() { return works; }
        public void setWorks(String works) { this.works = works; }
    }

    @JsonIgnoreProperties("dummy")
    static class Ignored {
        HashMap<String, Object> map = new HashMap<>();

        @JsonIgnore
        public String bogus;

        @JsonAnySetter
        void addEntry(String key, Object value) { map.put(key, value); }
    }

    static class Bean744 {
        protected Map<String, Object> additionalProperties;

        @JsonAnySetter
        public void addAdditionalProperty(String key, Object value) {
            if (additionalProperties == null) additionalProperties = new HashMap<>();
            additionalProperties.put(key, value);
        }

        public void setAdditionalProperties(Map<String, Object> additionalProperties) {
            this.additionalProperties = additionalProperties;
        }

        @JsonAnyGetter
        public Map<String, Object> getAdditionalProperties() { return additionalProperties; }

        @JsonIgnore
        public String getName() { return (String) additionalProperties.get("name"); }
    }

    private final ObjectMapper MAPPER = new ObjectMapper();

    @Test
    void readOnlyAndWriteOnly() throws Exception {
        assertEquals("{\"x\":1}", MAPPER.writeValueAsString(new ReadXWriteY()));
        ReadXWriteY result = MAPPER.readValue("{\"x\":5, \"y\":6}", ReadXWriteY.class);
        assertEquals(1, result.x);
        assertEquals(6, result.y);
    }

    @Test
    void readOnly935() throws Exception {
        String json = MAPPER.writeValueAsString(new Pojo935());
        assertNotNull(MAPPER.readValue(json, Pojo935.class));
    }

    @Test
    void readOnly1345() throws Exception {
        Foo1345 result = MAPPER.readValue("{\"name\":\"test\"}", Foo1345.class);
        assertEquals("test", result.name);
        assertNull(result.id);
    }

    @Test
    void readOnly1382() throws Exception {
        Foo1382 foo = MAPPER.readValue("{\"list\":[1,2,3,4]}", Foo1382.class);
        assertTrue(foo.getList().isEmpty());
    }

    @Test
    void viaReadOnly1805() throws Exception {
        UserWithReadOnly1805 user = new UserWithReadOnly1805();
        user.name = "foo";
        String json = MAPPER.writeValueAsString(user);
        assertNotNull(MAPPER.readValue(json, UserWithReadOnly1805.class));
    }

    @Test
    void usingAllowGetters1805() throws Exception {
        UserAllowGetters1805 user = new UserAllowGetters1805();
        user.name = "foo";
        String json = MAPPER.writeValueAsString(user);
        assertTrue(json.contains("roles"));
        assertNotNull(MAPPER.readValue(json, UserAllowGetters1805.class));
    }

    @Test
    void renamedReadOnly2779() throws Exception {
        Bean2779 bean = new Bean2779();
        bean.setWorks("works");
        String json = MAPPER.writeValueAsString(bean);
        assertNotNull(MAPPER.readValue(json, Bean2779.class));
    }

    @Test
    void ignoralsWithCatchAll() throws Exception {
        for (boolean failOnUnknown : new boolean[] { true, false }) {
            ObjectMapper mapper = new ObjectMapper();
            mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, failOnUnknown);
            Ignored bean = mapper.readValue("{\"name\":\"Bob\", \"bogus\": [ 1, 2, 3], \"dummy\" : 13 }",
                    Ignored.class);
            // class-level ignoral blocks; an ignored property's key still reaches the catch-all
            assertNull(bean.map.get("dummy"));
            assertEquals("[1, 2, 3]", "" + bean.map.get("bogus"));
            assertEquals("Bob", bean.map.get("name"));
            assertEquals(2, bean.map.size());
        }
    }

    @Test
    void ignoredGetterWithCatchAll744() throws Exception {
        Bean744 bean = MAPPER.readValue("{\"name\":\"Bob\"}", Bean744.class);
        assertNotNull(bean.additionalProperties);
        assertEquals("Bob", bean.getName());
    }
}
