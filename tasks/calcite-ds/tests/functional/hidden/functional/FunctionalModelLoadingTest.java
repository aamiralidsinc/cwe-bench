package hidden.functional;

import hidden.support.Check;
import hidden.support.Models;

import org.apache.calcite.schema.SchemaPlus;

import java.sql.Connection;

/**
 * Legitimate models keep working, including the reference forms the security suite also uses.
 * These run in the same JVM settings as the security suite (a non-empty deployment deny list),
 * so a fix that refuses allowed references fails here.
 */
public class FunctionalModelLoadingTest {

  private static SchemaPlus subSchema(String... model) throws Exception {
    Connection connection = Models.connect(Models.inline(model));
    SchemaPlus root = Models.root(connection);
    Check.notNull(root.getSubSchema("S"), "schema S must be registered");
    return root.getSubSchema("S");
  }

  public void testAllowedFunctionClassLoads() throws Exception {
    SchemaPlus s = subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  functions:",
        "  - name: F",
        "    className: 'bench.legit.LegitUdf'");
    Check.that(!s.getFunctions("F").isEmpty(), "function F must be registered");
  }

  public void testAllowedSchemaFactoryLoads() throws Exception {
    subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: custom",
        "  factory: 'bench.legit.LegitSchemaFactory'");
  }

  public void testAllowedTableFactoryLoads() throws Exception {
    SchemaPlus s = subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  tables:",
        "  - name: T",
        "    type: custom",
        "    factory: 'bench.legit.LegitTableFactory'");
    Check.notNull(s.getTable("T"), "table T must be registered");
  }

  public void testAllowedStaticFieldReferenceLoads() throws Exception {
    subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: custom",
        "  factory: 'bench.legit.LegitSchemaFactory#INSTANCE'");
  }

  public void testAllowedJdbcSchemaLoads() throws Exception {
    SchemaPlus s = subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: jdbc",
        "  jdbcUrl: 'jdbc:hsqldb:mem:fun05'",
        "  jdbcDriver: 'org.hsqldb.jdbc.JDBCDriver'");
    Check.notNull(s, "the JDBC schema must be registered");
  }

  public void testAllowedDialectFactoryLoads() throws Exception {
    subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: jdbc",
        "  jdbcUrl: 'jdbc:hsqldb:mem:fun06'",
        "  jdbcDriver: 'org.hsqldb.jdbc.JDBCDriver'",
        "  sqlDialectFactory: 'org.apache.calcite.sql.SqlDialectFactoryImpl'");
  }

  public void testAllowedStatisticProviderLoads() throws Exception {
    subSchema(
        "version: 1.0",
        "schemas:",
        "- type: jdbc",
        "  name: foodmart",
        "  jdbcUser: FOODMART",
        "  jdbcPassword: FOODMART",
        "  jdbcUrl: 'jdbc:hsqldb:res:foodmart'",
        "  jdbcSchema: foodmart",
        "- name: S",
        "  lattices:",
        "  - name: star",
        "    sql: 'select 1 from \"foodmart\".\"sales_fact_1997\" as \"s\""
            + " join \"foodmart\".\"product\" as \"p\" using (\"product_id\")'",
        "    auto: false",
        "    statisticProvider: 'org.apache.calcite.materialize.Lattices#CACHED_SQL'");
  }

  public void testAllowedReflectiveOperandLoads() throws Exception {
    SchemaPlus s = subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: custom",
        "  factory: 'org.apache.calcite.adapter.java.ReflectiveSchema$Factory'",
        "  operand:",
        "    class: 'bench.legit.ReflectiveTarget'");
    Check.notNull(s.getTable("EMPS"), "the reflective table must be registered");
  }

  public void testAllowedJdbcOperandLoads() throws Exception {
    subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: custom",
        "  factory: 'org.apache.calcite.adapter.jdbc.JdbcSchema$Factory'",
        "  operand:",
        "    jdbcUrl: 'jdbc:hsqldb:mem:fun09'",
        "    jdbcDriver: 'org.hsqldb.jdbc.JDBCDriver'");
  }

  public void testAllowedCloneWrapperLoads() throws Exception {
    subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: custom",
        "  factory: 'org.apache.calcite.adapter.clone.CloneSchema$Factory'",
        "  operand:",
        "    jdbcUrl: 'jdbc:hsqldb:mem:fun10'",
        "    jdbcDriver: 'org.hsqldb.jdbc.JDBCDriver'");
  }

  public void testAllowedMaterializationTableFactoryLoads() throws Exception {
    SchemaPlus s = subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  materializations:",
        "  - view: MV",
        "    sql: 'select 1 as c'",
        "    tableFactory: 'bench.legit.LegitTableFactory'");
    Check.notNull(s.getTable("MV"), "the materialization table must be registered");
  }

  public void testAllowedTypeProviderLoads() throws Exception {
    SchemaPlus s = subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  types:",
        "  - name: T",
        "    className: 'bench.legit.LegitType'");
    Check.notNull(s.getType("T"), "type T must be registered");
  }

  public void testAllowedDataSourceLoads() throws Exception {
    subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: jdbc",
        "  jdbcUrl: 'jdbc:hsqldb:mem:fun13'",
        "  dataSource: 'bench.legit.LegitDataSource'");
  }

  public void testExactDenyEntryDoesNotMatchLongerName() throws Exception {
    Models.clearMarker("P01Extra");
    SchemaPlus s = subSchema(
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  functions:",
        "  - name: F",
        "    className: 'bench.probes.P01Extra'");
    Check.that(!s.getFunctions("F").isEmpty(), "function F must be registered");
    Check.that(Models.marker("P01Extra"),
        "a class whose name merely starts with a denied name must still load");
  }
}
