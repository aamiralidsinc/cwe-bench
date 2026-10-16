package functional;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Legitimate use: everything that is not a read-only property binds exactly as
 * before, read-only input is ignored without an error, and responses still show
 * read-only values.
 */
public class BindingFeatureTest {

    // Writable nested values still merge on a partial update.
    @Test
    void writableNestedValuesMergeOnUpdate() throws Exception {
        Account a = Account.existing();
        Model.mergingMapper().readerForUpdating(a).readValue(Model.q(
                "{'profile':{'bio':'new'},'preferences':{'theme':'dark'},'tags':['late']}"));
        assertEquals("alice", a.name);
        assertEquals("Alice", a.profile.displayName, "merge must keep untouched nested values");
        assertEquals("new", a.profile.bio);
        assertEquals("dark", a.getPreferences().theme);
        assertTrue(a.getPreferences().digest);
        assertEquals(List.of("early", "late"), a.getTags());
    }

    // Merging enabled for one nested type still works.
    @Test
    void typeLevelMergeStillWorks() throws Exception {
        Account a = Account.existing();
        Model.typeMergingMapper().readerForUpdating(a).readValue(Model.q("{'preferences':{'digest':false}}"));
        assertEquals("light", a.getPreferences().theme);
        assertFalse(a.getPreferences().digest);
    }

    // Read-only input next to writable input: no error, the writable part binds.
    @Test
    void readOnlyInputIgnoredWithoutError() throws Exception {
        String body = Model.q("{'name':'n','quota':{'limit':5,'used':5},'profile':{'bio':'b'},'tags':['x']}");
        for (ObjectMapper m : List.of(Model.mapper(), Model.mergingMapper(), Model.typeMergingMapper())) {
            Account a = m.readValue(body, Account.class);
            assertEquals("n", a.name);
            assertEquals("b", a.profile.bio);
            assertEquals(List.of("x"), a.getTags());
            Account u = Account.existing();
            m.readerForUpdating(u).readValue(body);
            assertEquals("n", u.name);
            assertEquals("b", u.profile.bio);
        }
        Workspace w = Model.mergingMapper().readValue(Model.q("{'title':'t','quota':{'limit':1}}"), Workspace.class);
        assertEquals("t", w.title);
    }

    // Values that are read-only on input are still written out.
    @Test
    void serializationShowsReadOnlyValues() throws Exception {
        ObjectMapper m = Model.mapper();
        JsonNode acc = m.readTree(m.writeValueAsString(Account.existing()));
        assertEquals(10, acc.path("quota").path("limit").asInt());
        assertEquals(3, acc.path("quota").path("used").asInt());
        JsonNode mem = m.readTree(m.writeValueAsString(Member.existing()));
        assertEquals("member", mem.path("roles").path(0).asText());
        assertEquals(4, mem.path("quota").path("used").asInt());
        JsonNode t = m.readTree(m.writeValueAsString(new Ticket("s", "a", "ops")));
        assertEquals("ops", t.path("createdBy").asText());
        JsonNode i = m.readTree(m.writeValueAsString(new Invite("e", "admin", Map.of())));
        assertEquals("admin", i.path("role").asText());
        JsonNode p = m.readTree(m.writeValueAsString(new Plan()));
        assertEquals(5, p.path("quota").path("limit").asInt());
        assertEquals("viewer", p.path("roles").path(0).asText());
        JsonNode w = m.readTree(m.writeValueAsString(new Workspace()));
        assertEquals(50, w.path("quota").path("limit").asInt());
    }

    // Read-only declared at class level keeps working as before.
    @Test
    void classLevelReadOnlyStillHonoured() throws Exception {
        String body = Model.q("{'name':'p','quota':{'limit':999},'roles':['admin']}");
        for (ObjectMapper m : List.of(Model.mapper(), Model.mergingMapper())) {
            Plan p = m.readValue(body, Plan.class);
            assertEquals("p", p.name);
            assertEquals(5, p.getQuota().limit);
            assertEquals(List.of("viewer"), p.getRoles());
        }
    }

    // Without merging, nested values are replaced as before.
    @Test
    void plainMapperReplacesNestedValues() throws Exception {
        Account a = Account.existing();
        Model.mapper().readerForUpdating(a).readValue(Model.q("{'profile':{'bio':'only'}}"));
        assertNull(a.profile.displayName, "without merging a nested value is replaced");
        assertEquals("only", a.profile.bio);
    }
}
