package bench.legit;

import org.apache.calcite.rel.type.RelDataType;
import org.apache.calcite.rel.type.RelDataTypeFactory;
import org.apache.calcite.rel.type.RelProtoDataType;
import org.apache.calcite.sql.type.SqlTypeName;

/** Allowed custom type provider. */
public class LegitType implements RelProtoDataType {
  @Override public RelDataType apply(RelDataTypeFactory typeFactory) {
    return typeFactory.createSqlType(SqlTypeName.INTEGER);
  }
}
