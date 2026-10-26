package hudson.security.bt;

import hudson.model.AbstractItem;
import hudson.model.Job;
import hudson.security.ACL;
import hudson.security.AuthorizationStrategy;
import hudson.security.Permission;
import org.acegisecurity.Authentication;

import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * A per-resource permission authority: each user holds a set of permissions on the controller
 * and on each job, exactly like the product's own per-project matrix. The controller itself
 * (and the build machinery) keeps every permission.
 *
 * <p>Grants are keyed by the job's full name, so the controller's own configuration (which
 * includes this authority) can be serialised: no live item object is reachable from it.
 */
public class BtAuthz extends AuthorizationStrategy {

    private final Map<String, Set<Permission>> root = new HashMap<String, Set<Permission>>();
    private final Map<String, Map<String, Set<Permission>>> items =
            new HashMap<String, Map<String, Set<Permission>>>();

    public void grant(String user, Permission... perms) {
        add(root, user, perms);
    }

    public void grant(Job<?, ?> job, String user, Permission... perms) {
        String key = job.getFullName();
        Map<String, Set<Permission>> m = items.get(key);
        if (m == null) {
            m = new HashMap<String, Set<Permission>>();
            items.put(key, m);
        }
        add(m, user, perms);
    }

    private static void add(Map<String, Set<Permission>> m, String user, Permission... perms) {
        Set<Permission> s = m.get(user);
        if (s == null) {
            s = new HashSet<Permission>();
            m.put(user, s);
        }
        for (Permission p : perms) {
            s.add(p);
        }
    }

    public ACL getRootACL() {
        return new BtAcl(null);
    }

    public ACL getACL(Job<?, ?> job) {
        return new BtAcl(job);
    }

    public ACL getACL(AbstractItem item) {
        return item instanceof Job ? new BtAcl((Job<?, ?>) item) : getRootACL();
    }

    public Collection<String> getGroups() {
        Set<String> groups = new HashSet<String>();
        for (Map<String, Set<Permission>> m : items.values()) {
            groups.addAll(m.keySet());
        }
        groups.addAll(root.keySet());
        return Collections.unmodifiableSet(groups);
    }

    private static boolean held(Set<Permission> set, Permission p) {
        for (Permission q = p; q != null; q = q.impliedBy) {
            if (set.contains(q)) {
                return true;
            }
        }
        return false;
    }

    private final class BtAcl extends ACL {
        private final Job<?, ?> job;

        BtAcl(Job<?, ?> job) {
            this.job = job;
        }

        public boolean hasPermission(Authentication a, Permission permission) {
            if (a == null) {
                return false;
            }
            String name = a.getName();
            if ("SYSTEM".equals(name)) {
                return true;                      // the controller's own work
            }
            Map<String, Set<Permission>> m = job == null ? null : items.get(job.getFullName());
            Set<Permission> own = m == null ? null : m.get(name);
            if (own != null && held(own, permission)) {
                return true;
            }
            Set<Permission> base = root.get(name);
            return base != null && held(base, permission);
        }
    }
}
