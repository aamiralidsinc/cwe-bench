package security;

import com.fasterxml.jackson.core.JacksonException;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;

/**
 * Types that also accept extension attributes still have read-only properties.
 * No request body may set those, whatever way the object is built or updated.
 */
public class ExtensibleTypeBypassTest {

    // Partial update of a member, merging enabled for the mapper.
    @Test
    void memberUpdateKeepsQuota() throws Exception {
        Member m = Member.existing();
        try {
            Model.mergingMapper().readerForUpdating(m)
                    .readValue(Model.q("{'name':'bob','quota':{'limit':1000000,'used':0}}"));
        } catch (JacksonException refused) {
            // refusing the input is also safe, as long as nothing read-only changed
        }
        assertEquals(10, m.getQuota().limit, "read-only quota.limit of a member changed by a partial update");
        assertEquals(4, m.getQuota().used, "read-only quota.used of a member changed by a partial update");
    }

    // A read-only collection on a new member, default mapper.
    @Test
    void newMemberKeepsRoles() throws Exception {
        Member m;
        try {
            m = Model.mapper().readValue(Model.q("{'name':'n','roles':['admin']}"), Member.class);
        } catch (JacksonException refused) {
            return; // refused: nothing was bound
        }
        assertEquals(List.of("member"), m.getRoles(), "read-only roles of a member changed by input");
    }

    // An immutable object built from the request.
    @Test
    void ticketCreatorNotFromInput() throws Exception {
        Ticket t;
        try {
            t = Model.mapper().readValue(Model.q("{'subject':'s','createdBy':'mallory'}"), Ticket.class);
        } catch (JacksonException refused) {
            return; // refused: nothing was bound
        }
        assertNotEquals("mallory", t.getCreatedBy(), "read-only createdBy taken from input");
    }

    // A record built from the request.
    @Test
    void inviteRoleNotFromInput() throws Exception {
        Invite i;
        try {
            i = Model.mapper().readValue(Model.q("{'email':'e@example.com','role':'owner'}"), Invite.class);
        } catch (JacksonException refused) {
            return; // refused: nothing was bound
        }
        assertNotEquals("owner", i.role(), "read-only role of a record taken from input");
    }
}
