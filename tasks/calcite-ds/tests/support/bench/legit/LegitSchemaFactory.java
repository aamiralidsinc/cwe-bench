package bench.legit;

import org.apache.calcite.schema.Schema;
import org.apache.calcite.schema.SchemaFactory;
import org.apache.calcite.schema.SchemaPlus;
import org.apache.calcite.schema.impl.AbstractSchema;

import java.util.Map;

/** Allowed schema factory, used both as a plain class name and through its static field. */
public class LegitSchemaFactory implements SchemaFactory {
  public static final LegitSchemaFactory INSTANCE = new LegitSchemaFactory();

  @Override public Schema create(SchemaPlus parentSchema, String name,
      Map<String, Object> operand) {
    return new AbstractSchema();
  }
}
