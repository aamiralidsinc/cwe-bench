package functional;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;

/**
 * Linked records: links between records in one request keep resolving under
 * every view (they are visible properties), and privileged readers still set
 * the ids.
 */
public class LinkedRecordFeatureTest {
    private final ObjectMapper MAPPER = Model.mapper();

    private static final String JSON = Model.q(
            "{'id':7,'name':'a','next':{'id':8,'name':'b','next':7}}");

    @Test
    void linksResolveUnderPublicView() throws Exception {
        LinkedRecord r = MAPPER.readerWithView(PublicView.class)
                .forType(LinkedRecord.class).readValue(JSON);
        assertNotNull(r.next);
        assertEquals("b", r.next.name);
        assertSame(r, r.next.next, "visible link 'next' no longer resolves under PublicView");
    }

    @Test
    void constructedLinksResolveUnderPublicView() throws Exception {
        LinkedCreatorRecord r = MAPPER.readerWithView(PublicView.class)
                .forType(LinkedCreatorRecord.class).readValue(JSON);
        assertNotNull(r.next);
        assertEquals("b", r.next.name);
        assertSame(r, r.next.next, "visible link 'next' no longer resolves under PublicView (constructed record)");
    }

    @Test
    void adminSetsIds() throws Exception {
        LinkedRecord r = MAPPER.readerWithView(AdminView.class)
                .forType(LinkedRecord.class).readValue(JSON);
        assertEquals(7, r.id);
        assertEquals(8, r.next.id);
        assertSame(r, r.next.next);
    }

    @Test
    void noViewSetsIdsConstructed() throws Exception {
        LinkedCreatorRecord r = MAPPER.readerFor(LinkedCreatorRecord.class).readValue(JSON);
        assertEquals(7, r.id);
        assertEquals(8, r.next.id);
        assertSame(r, r.next.next);
    }
}
