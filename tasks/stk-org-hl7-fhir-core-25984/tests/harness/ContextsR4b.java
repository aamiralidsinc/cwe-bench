package vtesting;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * A stand-in for the R4B worker context a parser constructor expects. The paths under test
 * (payload decoding and decompression) do not consult the context; the stand-in only has to
 * satisfy the constructor.
 */
public final class ContextsR4b {
  private ContextsR4b() {
  }

  public static org.hl7.fhir.r4b.context.IWorkerContext stub() {
    return (org.hl7.fhir.r4b.context.IWorkerContext) Stubs.of(
        org.hl7.fhir.r4b.context.IWorkerContext.class, "4.3.0");
  }

  static final class Stubs {
    private Stubs() {
    }

    static Object of(Class<?> iface, String version) {
      InvocationHandler handler = (proxy, method, args) -> {
        if (method.getDeclaringClass() == Object.class) {
          switch (method.getName()) {
            case "toString":
              return "vtesting-context";
            case "hashCode":
              return System.identityHashCode(proxy);
            case "equals":
              return proxy == args[0];
            default:
              return null;
          }
        }
        if (method.getName().equals("getVersion")) {
          return version;
        }
        Class<?> rt = method.getReturnType();
        if (rt == void.class) {
          return null;
        }
        if (rt == boolean.class) {
          return false;
        }
        if (rt == int.class) {
          return 0;
        }
        if (rt == long.class) {
          return 0L;
        }
        if (rt == double.class) {
          return 0d;
        }
        if (rt == float.class) {
          return 0f;
        }
        if (rt == short.class) {
          return (short) 0;
        }
        if (rt == byte.class) {
          return (byte) 0;
        }
        if (rt == char.class) {
          return (char) 0;
        }
        if (List.class.isAssignableFrom(rt)) {
          return new ArrayList<>();
        }
        if (Set.class.isAssignableFrom(rt)) {
          return new HashSet<>();
        }
        if (Map.class.isAssignableFrom(rt)) {
          return new HashMap<>();
        }
        if (Optional.class.isAssignableFrom(rt)) {
          return Optional.empty();
        }
        return null;
      };
      return Proxy.newProxyInstance(Stubs.class.getClassLoader(), new Class<?>[] {iface}, handler);
    }
  }
}
