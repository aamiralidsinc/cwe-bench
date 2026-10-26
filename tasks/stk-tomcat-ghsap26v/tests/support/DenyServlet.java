package htests;

import javax.servlet.annotation.HttpConstraint;
import javax.servlet.annotation.ServletSecurity;
import javax.servlet.annotation.ServletSecurity.EmptyRoleSemantic;

@ServletSecurity(@HttpConstraint(EmptyRoleSemantic.DENY))
public class DenyServlet extends MarkerServlet {
    private static final long serialVersionUID = 1L;
}
