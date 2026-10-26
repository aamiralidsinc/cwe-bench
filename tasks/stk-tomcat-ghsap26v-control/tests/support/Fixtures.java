package htests;

import java.util.Map;

/** Reusable deployment descriptors for the suites. */
public final class Fixtures {

    private Fixtures() {
    }

    /** A form-login application with two protected servlets, one of which ends in the action name. */
    public static String formApp() {
        return Harness.webXml(
            "  <servlet><servlet-name>area</servlet-name><servlet-class>htests.PlainServlet</servlet-class></servlet>\n"
          + "  <servlet><servlet-name>action</servlet-name><servlet-class>htests.PlainServlet</servlet-class></servlet>\n"
          + "  <servlet><servlet-name>adminarea</servlet-name><servlet-class>htests.PlainServlet</servlet-class></servlet>\n"
          + "  <servlet-mapping><servlet-name>area</servlet-name><url-pattern>/app/protected</url-pattern></servlet-mapping>\n"
          + "  <servlet-mapping><servlet-name>action</servlet-name><url-pattern>/app/j_security_check</url-pattern></servlet-mapping>\n"
          + "  <servlet-mapping><servlet-name>adminarea</servlet-name><url-pattern>/app/admin</url-pattern></servlet-mapping>\n"
          + "  <security-constraint>\n"
          + "    <web-resource-collection><url-pattern>/app/protected</url-pattern></web-resource-collection>\n"
          + "    <auth-constraint><role-name>user</role-name></auth-constraint>\n"
          + "  </security-constraint>\n"
          + "  <security-constraint>\n"
          + "    <web-resource-collection><url-pattern>/app/admin</url-pattern></web-resource-collection>\n"
          + "    <auth-constraint><role-name>admin</role-name></auth-constraint>\n"
          + "  </security-constraint>\n"
          + "  <security-constraint>\n"
          + "    <web-resource-collection><url-pattern>/app/j_security_check</url-pattern></web-resource-collection>\n"
          + "    <auth-constraint><role-name>admin</role-name></auth-constraint>\n"
          + "  </security-constraint>\n"
          + "  <login-config><auth-method>FORM</auth-method><form-login-config>\n"
          + "    <form-login-page>/login.html</form-login-page>\n"
          + "    <form-error-page>/error.html</form-error-page>\n"
          + "  </form-login-config></login-config>\n"
          + "  <security-role><role-name>admin</role-name></security-role>\n"
          + "  <security-role><role-name>user</role-name></security-role>\n");
    }

    public static Map<String, String> formFiles() {
        return Harness.files(
            "login.html", "<html><body>sign in</body></html>",
            "error.html", "<html><body>sign in failed</body></html>");
    }

    /** A metadata-complete application that protects a resource only through the descriptor. */
    public static String metadataCompleteApp() {
        return "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n"
             + "<web-app xmlns=\"http://java.sun.com/xml/ns/javaee\" version=\"3.0\" metadata-complete=\"true\">\n"
             + "  <servlet><servlet-name>p</servlet-name><servlet-class>htests.PlainServlet</servlet-class></servlet>\n"
             + "  <servlet-mapping><servlet-name>p</servlet-name><url-pattern>/protected</url-pattern></servlet-mapping>\n"
             + "  <security-constraint>\n"
             + "    <web-resource-collection><url-pattern>/protected</url-pattern></web-resource-collection>\n"
             + "    <auth-constraint/>\n"
             + "  </security-constraint>\n"
             + "</web-app>\n";
    }
}
