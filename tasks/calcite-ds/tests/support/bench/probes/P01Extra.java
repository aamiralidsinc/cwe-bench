package bench.probes;

/** An allowed class whose name starts with a denied exact name; used for exact-match tests. */
public class P01Extra {
  static {
    Probes.mark("P01Extra");
  }

  public static int eval(int x) {
    return x + 1;
  }
}
