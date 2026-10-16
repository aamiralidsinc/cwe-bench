package security;

import com.fasterxml.jackson.core.JacksonException;
import org.junit.jupiter.api.Test;
import support.Model;
import support.Model.*;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * An account's quota is read-only. No request body may change it, whether the
 * body creates a new account or is applied to an existing one.
 */
public class QuotaUpdateBypassTest {

    private static final String RAISE = Model.q("{'quota':{'limit':1000000,'used':0}}");

    // The reported example: a partial update with merging enabled for the mapper.
    @Test
    void updateKeepsQuota() throws Exception {
        Account a = Account.existing();
        try {
            Model.mergingMapper().readerForUpdating(a).readValue(RAISE);
        } catch (JacksonException refused) {
            // refusing the input is also safe, as long as nothing read-only changed
        }
        assertEquals(10, a.getQuota().limit, "read-only quota.limit changed by a partial update");
        assertEquals(3, a.getQuota().used, "read-only quota.used changed by a partial update");
    }

    // A new account read with the same mapper.
    @Test
    void newAccountKeepsDefaultQuota() throws Exception {
        Account a;
        try {
            a = Model.mergingMapper().readValue(Model.q("{'name':'n','quota':{'limit':1000000,'used':0}}"),
                    Account.class);
        } catch (JacksonException refused) {
            return; // refused: nothing was bound
        }
        assertEquals(10, a.getQuota().limit, "read-only quota.limit taken from input on a new account");
    }

    // Merging enabled for the nested type only, not for the whole mapper.
    @Test
    void typeLevelMergeKeepsQuota() throws Exception {
        Account a = Account.existing();
        try {
            Model.typeMergingMapper().readerForUpdating(a).readValue(RAISE);
        } catch (JacksonException refused) {
            // safe
        }
        assertEquals(10, a.getQuota().limit, "read-only quota.limit changed (type-level merging)");
    }

    // Read-only declared on the field; update through updateValue().
    @Test
    void fieldDeclaredQuotaKeptByUpdateValue() throws Exception {
        Workspace w = new Workspace();
        w.title = "w";
        try {
            Model.mergingMapper().updateValue(w, Map.of("quota", Map.of("limit", 999999)));
        } catch (JacksonException refused) {
            // safe
        }
        assertEquals(50, w.getQuota().limit, "read-only quota.limit changed by updateValue()");
    }
}
