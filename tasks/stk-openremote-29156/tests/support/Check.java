package hidden.support;

import jakarta.ws.rs.WebApplicationException;

/** Assertions a test class uses; every failure throws, which the runner records. */
public final class Check {

    public interface Call {
        void run() throws Exception;
    }

    public static void refused(Call call, String what) {
        try {
            call.run();
        } catch (WebApplicationException e) {
            int status = e.getResponse() == null ? 0 : e.getResponse().getStatus();
            if (status >= 400 && status < 500) return;
            throw new AssertionError(what + ": refused with " + status
                + " (" + e.getClass().getSimpleName() + "), expected a client error", e);
        } catch (AssertionError e) {
            throw e;
        } catch (Throwable t) {
            throw new AssertionError(what + ": threw " + t.getClass().getName()
                + " instead of a client-error refusal", t);
        }
        throw new AssertionError(what + ": request was accepted");
    }

    public static void ok(Call call, String what) {
        try {
            call.run();
        } catch (Throwable t) {
            throw new AssertionError(what + ": expected success, got " + t.getClass().getName()
                + ": " + t.getMessage(), t);
        }
    }

    public static void isTrue(boolean value, String what) {
        if (!value) throw new AssertionError(what);
    }

    public static void equal(Object actual, Object expected, String what) {
        if (!java.util.Objects.equals(actual, expected)) {
            throw new AssertionError(what + ": expected " + expected + ", got " + actual);
        }
    }

    public static void notNull(Object value, String what) {
        if (value == null) throw new AssertionError(what + ": expected a value, got null");
    }
}
