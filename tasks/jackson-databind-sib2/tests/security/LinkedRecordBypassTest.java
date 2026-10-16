package security;

import com.fasterxml.jackson.core.JacksonException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

/**
 * Records that link to each other within one request. Their `id` may only be
 * written under AdminView. A PublicView caller supplies ids; they must not end
 * up in the records' `id` property.
 */
public class LinkedRecordBypassTest {
    private final ObjectMapper MAPPER = Model.mapper();

    private static final String JSON = Model.q(
            "{'id':7,'name':'a','next':{'id':8,'name':'b'}}");

    @Test
    void recordIdHidden() throws Exception {
        LinkedRecord r;
        try {
            r = MAPPER.readerWithView(PublicView.class).forType(LinkedRecord.class).readValue(JSON);
        } catch (JacksonException refused) {
            return; // refused: nothing was bound
        }
        assertEquals("a", r.name);
        assertNotEquals(7, r.id, "admin-only 'id' was set from input under PublicView");
        assertNotNull(r.next);
        assertNotEquals(8, r.next.id, "admin-only 'id' of nested record was set from input under PublicView");
    }

    @Test
    void constructedRecordIdHidden() throws Exception {
        LinkedCreatorRecord r;
        try {
            r = MAPPER.readerWithView(PublicView.class).forType(LinkedCreatorRecord.class).readValue(JSON);
        } catch (JacksonException refused) {
            return; // refused: nothing was bound
        }
        assertEquals("a", r.name);
        assertNotEquals(7, r.id, "admin-only 'id' was set from input under PublicView (constructed record)");
        assertNotNull(r.next);
        assertNotEquals(8, r.next.id, "admin-only 'id' of nested record was set from input under PublicView (constructed record)");
    }
}
