package support;

import com.fasterxml.jackson.annotation.*;
import com.fasterxml.jackson.annotation.JsonProperty.Access;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Shared data model for the read-only property tests.
 *
 * An account service binds untrusted request bodies to these types, to create
 * new objects and to apply partial updates to existing ones. Server-maintained
 * values are declared read-only: clients see them in responses but must never
 * set them.
 */
public final class Model {
    private Model() {}

    public static ObjectMapper mapper() { return new ObjectMapper(); }

    /** Mapper used for partial updates: nested objects are merged, not replaced. */
    public static ObjectMapper mergingMapper() {
        ObjectMapper m = new ObjectMapper();
        m.setDefaultMergeable(Boolean.TRUE);
        return m;
    }

    /** Mapper that enables merging for the nested types only. */
    public static ObjectMapper typeMergingMapper() {
        ObjectMapper m = new ObjectMapper();
        m.configOverride(Quota.class).setMergeable(Boolean.TRUE);
        m.configOverride(Preferences.class).setMergeable(Boolean.TRUE);
        return m;
    }

    /** Single quotes to double quotes, so the JSON literals in tests read cleanly. */
    public static String q(String s) { return s.replace('\'', '"'); }

    public static class Quota {
        public int limit;
        public int used;
        public Quota() { }
        public Quota(int limit, int used) { this.limit = limit; this.used = used; }
    }

    public static class Profile {
        public String displayName;
        public String bio;
    }

    public static class Preferences {
        public String theme = "light";
        public boolean digest = true;
    }

    /** Account: read-only quota (declared on the getter), writable nested values. */
    public static class Account {
        public String name;
        public Profile profile = new Profile();

        private final Quota quota = new Quota(10, 0);
        private final Preferences prefs = new Preferences();
        private final List<String> tagList = new ArrayList<>();

        @JsonProperty(access = Access.READ_ONLY)
        public Quota getQuota() { return quota; }

        public Preferences getPreferences() { return prefs; }

        public List<String> getTags() { return tagList; }

        public static Account existing() {
            Account a = new Account();
            a.name = "alice";
            a.profile.displayName = "Alice";
            a.profile.bio = "hello";
            a.quota.limit = 10;
            a.quota.used = 3;
            a.tagList.add("early");
            return a;
        }
    }

    /** Same idea, with the read-only marker on the field. */
    public static class Workspace {
        public String title;

        @JsonProperty(access = Access.READ_ONLY)
        private Quota quota = new Quota(50, 0);

        public Quota getQuota() { return quota; }
    }

    /** Read-only declared at class level, keeping the getter. */
    @JsonIgnoreProperties(value = { "quota", "roles" }, allowGetters = true)
    public static class Plan {
        public String name;
        private final Quota quota = new Quota(5, 0);
        private final List<String> roles = new ArrayList<>(List.of("viewer"));

        public Quota getQuota() { return quota; }
        public List<String> getRoles() { return roles; }
    }

    /**
     * Member: read-only quota and roles, plus a map that collects extension
     * attributes (keys the type does not declare).
     */
    public static class Member {
        public String name;
        public Profile profile = new Profile();

        @JsonProperty(access = Access.READ_ONLY)
        private Quota quota = new Quota(10, 0);

        private final List<String> roles = new ArrayList<>(List.of("member"));
        private final List<String> tagList = new ArrayList<>();
        private final Preferences prefs = new Preferences();

        /** Internal bookkeeping, never part of the JSON form. */
        @JsonIgnore
        public String internalNote = "none";

        @JsonAnySetter
        public Map<String, Object> attributes = new LinkedHashMap<>();

        public Quota getQuota() { return quota; }

        @JsonProperty(access = Access.READ_ONLY)
        public List<String> getRoles() { return roles; }

        public List<String> getTags() { return tagList; }

        public Preferences getPreferences() { return prefs; }

        public static Member existing() {
            Member m = new Member();
            m.name = "bob";
            m.profile.displayName = "Bob";
            m.quota.limit = 10;
            m.quota.used = 4;
            return m;
        }
    }

    /** Immutable ticket created from a request; createdBy is server-assigned. */
    public static class Ticket {
        private final String subject;
        private final String assignee;

        @JsonProperty(access = Access.READ_ONLY)
        private final String createdBy;

        private final Map<String, Object> extra = new LinkedHashMap<>();

        @JsonCreator
        public Ticket(@JsonProperty("subject") String subject,
                      @JsonProperty("assignee") String assignee,
                      @JsonProperty("createdBy") String createdBy) {
            this.subject = subject;
            this.assignee = assignee;
            this.createdBy = (createdBy == null) ? "system" : createdBy;
        }

        public String getSubject() { return subject; }
        public String getAssignee() { return assignee; }
        public String getCreatedBy() { return createdBy; }

        @JsonAnySetter
        public void putExtra(String key, Object value) { extra.put(key, value); }

        public Map<String, Object> extra() { return extra; }
    }

    /** Same ticket shape without extension attributes. */
    public static class PlainTicket {
        private final String subject;

        @JsonProperty(access = Access.READ_ONLY)
        private final String createdBy;

        @JsonCreator
        public PlainTicket(@JsonProperty("subject") String subject,
                           @JsonProperty("createdBy") String createdBy) {
            this.subject = subject;
            this.createdBy = (createdBy == null) ? "system" : createdBy;
        }

        public String getSubject() { return subject; }
        public String getCreatedBy() { return createdBy; }
    }

    /** Invitation record; role is decided by the server. */
    public record Invite(String email,
                         @JsonProperty(access = Access.READ_ONLY) String role,
                         @JsonAnySetter Map<String, Object> extra) { }

    /** Invitation record without extension attributes. */
    public record PlainInvite(String email,
                              @JsonProperty(access = Access.READ_ONLY) String role) { }

    public static class OwnerRef {
        public long id;
        public String display;
        public OwnerRef() { }
        public OwnerRef(long id, String display) { this.id = id; this.display = display; }
    }

    /**
     * Responses show the owner as an object; requests name the owner by id.
     * Both use the JSON name "owner".
     */
    public static class Document {
        public String title;
        private long ownerId = 1;

        @JsonProperty(value = "owner", access = Access.READ_ONLY)
        public OwnerRef getOwnerSummary() { return new OwnerRef(ownerId, "user#" + ownerId); }

        @JsonProperty(value = "owner", access = Access.WRITE_ONLY)
        public void setOwnerId(long id) { ownerId = id; }

        public long ownerId() { return ownerId; }
    }

    /** Document with extension attributes. */
    public static class ExtDocument extends Document {
        @JsonAnySetter
        public Map<String, Object> attributes = new LinkedHashMap<>();
    }
}
