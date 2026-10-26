package bench.legit;

import org.apache.calcite.rel.type.RelDataType;
import org.apache.calcite.rel.type.RelDataTypeFactory;
import org.apache.calcite.schema.SchemaPlus;
import org.apache.calcite.schema.Table;
import org.apache.calcite.schema.TableFactory;
import org.apache.calcite.schema.impl.AbstractTable;
import org.apache.calcite.sql.type.SqlTypeName;

import org.checkerframework.checker.nullness.qual.Nullable;

import java.util.Map;

/** Allowed table factory. */
public class LegitTableFactory implements TableFactory<Table> {
  @Override public Table create(SchemaPlus schema, String name,
      Map<String, Object> operand, @Nullable RelDataType rowType) {
    return new AbstractTable() {
      @Override public RelDataType getRowType(RelDataTypeFactory typeFactory) {
        return typeFactory.builder()
            .add("C", SqlTypeName.INTEGER)
            .build();
      }
    };
  }
}
