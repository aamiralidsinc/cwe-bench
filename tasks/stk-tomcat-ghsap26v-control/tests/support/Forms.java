package htests;

import java.io.IOException;

/** Drives the ordinary form-login flow of the fixture application. */
public final class Forms {

    private Forms() {
    }

    /** Log in and replay the saved request; returns the session cookie. */
    public static String login(Harness h, String user, String password) throws IOException {
        Harness.Resp first = h.get("/app/protected");
        String cookie = first.cookie;
        Harness.Resp auth = h.post("/j_security_check", cookie,
                "j_username=" + user + "&j_password=" + password);
        if (auth.cookie != null) cookie = auth.cookie;
        String path = "/app/protected";
        if (auth.location != null) {
            int slash = auth.location.indexOf('/', 8);
            if (slash >= 0) path = auth.location.substring(slash);
        }
        Harness.Resp replay = h.get(path, cookie);
        if (replay.cookie != null) cookie = replay.cookie;
        return cookie;
    }
}
