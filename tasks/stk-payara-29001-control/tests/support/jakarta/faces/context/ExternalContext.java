package jakarta.faces.context;
import java.util.Map;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
public abstract class ExternalContext {
    public abstract Map<String, Object> getSessionMap();
    public abstract HttpSession getSession(boolean create);
    public abstract Object getRequest();
    public abstract Object getResponse();
}
