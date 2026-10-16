package functional;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Compact (array-shaped) entries: visible values keep binding in their own
 * position next to hidden ones, and privileged or view-less reads and updates
 * work as before.
 */
public class CompactEntryFeatureTest {
    private final ObjectMapper MAPPER = Model.mapper();

    private static final String ENTRY = Model.q("['new-label','mallory',['admin','x'],'new-note']");

    @Test
    void publicUpdateBindsVisibleValues() throws Exception {
        CompactEntry e = CompactEntry.existing();
        MAPPER.readerForUpdating(e).withView(PublicView.class).readValue(ENTRY);
        assertEquals("new-label", e.label);
        assertEquals("new-note", e.note, "visible value after a hidden one did not bind in place (update)");
    }

    @Test
    void adminUpdateBindsEverything() throws Exception {
        CompactEntry e = CompactEntry.existing();
        MAPPER.readerForUpdating(e).withView(AdminView.class).readValue(ENTRY);
        assertEquals("new-label", e.label);
        assertEquals("mallory", e.owner);
        assertEquals(List.of("admin", "x"), e.roles);
        assertEquals("new-note", e.note);
    }

    @Test
    void noViewUpdateBindsEverything() throws Exception {
        CompactEntry e = CompactEntry.existing();
        MAPPER.readerForUpdating(e).readValue(ENTRY);
        assertEquals("mallory", e.owner);
        assertEquals("new-note", e.note);
    }

    @Test
    void publicDefaultsBindVisibleValues() throws Exception {
        EntrySettings s = MAPPER.readerWithView(PublicView.class).forType(EntrySettings.class)
                .readValue(Model.q("{'title':'t','entry':" + ENTRY + "}"));
        assertEquals("t", s.title);
        assertEquals("new-label", s.entry.label);
        assertEquals("new-note", s.entry.note, "visible value after a hidden one did not bind in place (defaults)");
    }

    @Test
    void adminDefaultsBindEverything() throws Exception {
        EntrySettings s = MAPPER.readerWithView(AdminView.class).forType(EntrySettings.class)
                .readValue(Model.q("{'title':'t','entry':" + ENTRY + "}"));
        assertEquals("mallory", s.entry.owner);
        assertEquals(List.of("admin", "x"), s.entry.roles);
        assertEquals("new-note", s.entry.note);
    }

    @Test
    void publicNewEntryBindsVisibleValues() throws Exception {
        CompactEntry e = MAPPER.readerWithView(PublicView.class).forType(CompactEntry.class).readValue(ENTRY);
        assertEquals("new-label", e.label);
        assertEquals("new-note", e.note);
    }
}
