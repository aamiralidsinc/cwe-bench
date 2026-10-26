package jakarta.faces.context;
public abstract class FacesContext {
    public static FacesContext getCurrentInstance() { return null; }
    public abstract ExternalContext getExternalContext();
    public abstract void responseComplete();
}
