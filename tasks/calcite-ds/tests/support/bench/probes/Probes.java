package bench.probes;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

/**
 * Classes whose static initializer records that the JVM loaded them. Each class is named in the
 * deployment deny list used by the security suite, and none of them is referenced by the test
 * code except as a string.
 */
public final class Probes {
  private Probes() {}

  public static void mark(String id) {
    try {
      final Path dir = Path.of(System.getProperty("probe.dir", "/tmp/calcite-probes"));
      Files.createDirectories(dir);
      Files.write(dir.resolve(id), new byte[] {1},
          StandardOpenOption.CREATE, StandardOpenOption.APPEND);
    } catch (Throwable t) {
      // A marker failure must not mask the load itself.
    }
  }
}

class P01 {
  static {
    Probes.mark("P01");
  }
}

class P02 {
  static {
    Probes.mark("P02");
  }
}

class P03 {
  static {
    Probes.mark("P03");
  }
}

class P04 {
  static {
    Probes.mark("P04");
  }
}

class P05 {
  static {
    Probes.mark("P05");
  }
}

class P06 {
  static {
    Probes.mark("P06");
  }
}

class P07 {
  static {
    Probes.mark("P07");
  }
}

class P08 {
  static {
    Probes.mark("P08");
  }
}

class P09 {
  static {
    Probes.mark("P09");
  }
}

class P10 {
  static {
    Probes.mark("P10");
  }
}

class P11 {
  static {
    Probes.mark("P11");
  }
}

class P12 {
  static {
    Probes.mark("P12");
  }
}

class P13 {
  static {
    Probes.mark("P13");
  }
}

class P14 {
  static {
    Probes.mark("P14");
  }
}

class P15 {
  static {
    Probes.mark("P15");
  }
}

class P16 {
  static {
    Probes.mark("P16");
  }
}
