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
 * Types that accept extension attributes: writable values and extension
 * attributes bind exactly as before.
 */
public class ExtensibleTypeFeatureTest {

    @Test
    void memberWritableValuesBindOnUpdate() throws Exception {
        Member m = Member.existing();
        Model.mergingMapper().readerForUpdating(m).readValue(Model.q(
                "{'name':'robert','profile':{'bio':'b'},'preferences':{'theme':'dark'},'tags':['t1'],'quota':{'limit':1}}"));
        assertEquals("robert", m.name);
        assertEquals("Bob", m.profile.displayName);
        assertEquals("b", m.profile.bio);
        assertEquals("dark", m.getPreferences().theme);
        assertTrue(m.getPreferences().digest);
        assertEquals(List.of("t1"), m.getTags());
    }

    @Test
    void memberTagsStillCollectedWithoutMerging() throws Exception {
        Member m = Model.mapper().readValue(Model.q("{'name':'n','tags':['a','b'],'roles':['admin']}"), Member.class);
        assertEquals("n", m.name);
        assertEquals(List.of("a", "b"), m.getTags());
    }

    @Test
    void unknownKeysStillReachExtensionAttributes() throws Exception {
        for (ObjectMapper mapper : List.of(Model.mapper(), Model.mergingMapper())) {
            Member m = mapper.readValue(Model.q("{'name':'n','team':'core','level':3}"), Member.class);
            assertEquals("n", m.name);
            assertEquals("core", m.attributes.get("team"));
            assertEquals(3, m.attributes.get("level"));
        }
    }

    // A property excluded from the JSON form (not a read-only one): its key keeps
    // arriving with the extension attributes, as before.
    @Test
    void excludedPropertyKeyStillReachesExtensionAttributes() throws Exception {
        Member m = Model.mapper().readValue(Model.q("{'name':'n','internalNote':'from-client'}"), Member.class);
        assertEquals("none", m.internalNote);
        assertEquals("from-client", m.attributes.get("internalNote"));
    }

    @Test
    void ticketBindsVisibleValuesAndExtras() throws Exception {
        Ticket t = Model.mapper().readValue(
                Model.q("{'subject':'s','assignee':'carol','createdBy':'mallory','priority':'high'}"), Ticket.class);
        assertEquals("s", t.getSubject());
        assertEquals("carol", t.getAssignee());
        assertEquals("high", t.extra().get("priority"));
    }

    @Test
    void inviteBindsVisibleValuesAndExtras() throws Exception {
        Invite i = Model.mapper().readValue(
                Model.q("{'email':'e@example.com','role':'owner','source':'web'}"), Invite.class);
        assertEquals("e@example.com", i.email());
        assertEquals("web", i.extra().get("source"));
    }

    @Test
    void plainCreatedObjectsUnchanged() throws Exception {
        PlainTicket t = Model.mapper().readValue(Model.q("{'subject':'s','createdBy':'x'}"), PlainTicket.class);
        assertEquals("s", t.getSubject());
        assertEquals("system", t.getCreatedBy());
        PlainInvite i = Model.mapper().readValue(Model.q("{'email':'e','role':'x'}"), PlainInvite.class);
        assertEquals("e", i.email());
        assertNull(i.role());
    }

    // Input names the owner by id under the same JSON name that responses use
    // for the read-only owner summary: the input must keep binding.
    @Test
    void sameNameWritableInputStillBinds() throws Exception {
        ObjectMapper m = Model.mapper();
        Document d = m.readValue(Model.q("{'title':'t','owner':42}"), Document.class);
        assertEquals("t", d.title);
        assertEquals(42, d.ownerId());
        JsonNode out = m.readTree(m.writeValueAsString(d));
        assertEquals(42, out.path("owner").path("id").asLong());
        assertEquals("user#42", out.path("owner").path("display").asText());

        Document u = new Document();
        Model.mergingMapper().readerForUpdating(u).readValue(Model.q("{'owner':7}"));
        assertEquals(7, u.ownerId());
    }

    @Test
    void sameNameWritableInputStillBindsWithExtensions() throws Exception {
        ExtDocument d = Model.mapper().readValue(Model.q("{'title':'t','owner':9,'lang':'en'}"), ExtDocument.class);
        assertEquals(9, d.ownerId());
        assertEquals("en", d.attributes.get("lang"));
        assertFalse(d.attributes.containsKey("owner"), "the owner id is bound, not collected");
        Map<?, ?> out = Model.mapper().convertValue(d, Map.class);
        assertTrue(out.containsKey("owner"));
    }
}
