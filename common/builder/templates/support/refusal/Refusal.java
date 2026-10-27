package bench.support;

import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.concurrent.Callable;
import java.util.function.Consumer;
import java.util.function.Predicate;

/**
 * Refusal-tolerant assertions for JUnit security tests. Copy into tests/support/bench/support/ (adjust the
 * package to the task's harness package).
 *
 * <p>A security test that drives a hardened entry point must accept every secure outcome the instruction allows:
 * the call is refused (a client error, or one of the product's own refusal exceptions), or it completes and leaves
 * nothing unsafe behind. A crash is not a refusal: a 5xx, or an exception outside the declared refusal types, fails
 * the test, so a fix that merely breaks the call is still caught (wrong-fix class crash_as_refusal).
 *
 * <pre>
 *   Refusal.refusedOr(() -&gt; servlet.handle(request), result -&gt; assertNoSecret(result),
 *       SecurityException.class, PrincipalException.class);
 *   assertStateUnchanged();   // side effects are checked after every outcome
 * </pre>
 */
public final class Refusal {
    private Refusal() {}

    /** What one call did. */
    public static final class Outcome<T> {
        public final boolean refused;
        public final T value;
        public final String reason;

        Outcome(boolean refused, T value, String reason) {
            this.refused = refused;
            this.value = value;
            this.reason = reason;
        }
    }

    static Integer status(Object o) {
        if (o == null) return null;
        for (String name : new String[] {"getStatus", "getStatusCode", "status", "getCode"}) {
            try {
                Method m = o.getClass().getMethod(name);
                Object v = m.invoke(o);
                if (v instanceof Integer && (Integer) v >= 100 && (Integer) v <= 599) return (Integer) v;
            } catch (ReflectiveOperationException | RuntimeException ignored) {
                // not a status carrier
            }
        }
        return null;
    }

    @SafeVarargs
    public static <T> Outcome<T> attempt(Callable<T> call, Class<? extends Throwable>... refusals) {
        T value;
        try {
            value = call.call();
        } catch (AssertionError e) {
            throw e;
        } catch (Throwable e) {
            Integer s = status(e);
            if (s != null) {
                if (s >= 400 && s < 500) return new Outcome<>(true, null, e.getClass().getSimpleName() + " " + s);
                throw new AssertionError("server error " + s + ": a crash is not a refusal", e);
            }
            if (Arrays.stream(refusals).anyMatch(r -> r.isInstance(e))) {
                return new Outcome<>(true, null, e.getClass().getSimpleName());
            }
            throw new AssertionError("unexpected exception (not a declared refusal): " + e, e);
        }
        Integer s = status(value);
        if (s != null && s >= 400 && s < 500) return new Outcome<>(true, value, "status " + s);
        if (s != null && s >= 500) throw new AssertionError("server error " + s + ": a crash is not a refusal");
        return new Outcome<>(false, value, "");
    }

    /** Passes when the call is refused, or when it completes and ok accepts the result. */
    @SafeVarargs
    public static <T> Outcome<T> refusedOr(Callable<T> call, Consumer<T> ok, Class<? extends Throwable>... refusals) {
        Outcome<T> out = attempt(call, refusals);
        if (!out.refused && ok != null) ok.accept(out.value);
        return out;
    }

    /** Passes only when the call is refused. */
    @SafeVarargs
    public static <T> Outcome<T> mustRefuse(Callable<T> call, Class<? extends Throwable>... refusals) {
        Outcome<T> out = attempt(call, refusals);
        if (!out.refused) throw new AssertionError("expected a refusal (a client error or a refusal exception)");
        return out;
    }

    /** Predicate form, for products that signal refusal through a result object. */
    public static <T> boolean refusedBy(T result, Predicate<T> isRefusal) {
        return result != null && isRefusal.test(result);
    }
}
