package htests;

import javax.servlet.annotation.HttpConstraint;
import javax.servlet.annotation.ServletSecurity;

@ServletSecurity(@HttpConstraint(rolesAllowed = { "admin" }))
public class RoleAdminServlet extends MarkerServlet {
    private static final long serialVersionUID = 1L;
}
