package htests;

import javax.servlet.annotation.HttpConstraint;
import javax.servlet.annotation.HttpMethodConstraint;
import javax.servlet.annotation.ServletSecurity;
import javax.servlet.annotation.ServletSecurity.EmptyRoleSemantic;

@ServletSecurity(value = @HttpConstraint(EmptyRoleSemantic.PERMIT),
        httpMethodConstraints = {
            @HttpMethodConstraint(value = "GET", emptyRoleSemantic = EmptyRoleSemantic.DENY)
        })
public class MethodServlet extends MarkerServlet {
    private static final long serialVersionUID = 1L;
}
