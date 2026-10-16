package security;

import com.fasterxml.jackson.core.JacksonException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Compact (array-shaped) entries whose `owner` and `roles` may only be written
 * under AdminView. A PublicView caller's values must leave them untouched,
 * also when the input is applied on top of an existing entry.
 */
public class CompactEntryBypassTest {
    private final ObjectMapper MAPPER = Model.mapper();

    private static final String ENTRY = Model.q("['new-label','mallory',['admin'],'new-note']");

    // Partial update of an existing entry (e.g. a PATCH request).
    @Test
    void updateKeepsRestrictedValues() throws Exception {
        CompactEntry e = CompactEntry.existing();
        try {
            MAPPER.readerForUpdating(e).withView(PublicView.class).readValue(ENTRY);
        } catch (JacksonException refused) {
            // refusing the input is also safe, as long as nothing restricted changed
        }
        assertEquals("alice", e.owner, "admin-only 'owner' was overwritten under PublicView (update)");
        assertEquals(List.of("reader"), e.roles, "admin-only 'roles' was overwritten under PublicView (update)");
    }

    // New settings document whose entry is laid over server defaults.
    @Test
    void defaultsKeepRestrictedValues() throws Exception {
        EntrySettings s;
        try {
            s = MAPPER.readerWithView(PublicView.class).forType(EntrySettings.class)
                    .readValue(Model.q("{'title':'t','entry':" + ENTRY + "}"));
        } catch (JacksonException refused) {
            return; // refused: nothing was bound
        }
        assertEquals("system", s.entry.owner, "admin-only 'owner' was overwritten under PublicView (defaults)");
        assertEquals(List.of("viewer"), s.entry.roles, "admin-only 'roles' was overwritten under PublicView (defaults)");
    }
}
