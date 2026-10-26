package hidden.security;

import hidden.support.Check;
import hidden.support.Models;

import java.sql.Connection;

/**
 * Every case drives the real entry point: a JDBC connection whose model names a class that the
 * deployment has put on its deny list. The class records that it was initialized; the test fails
 * if the connection is not refused, or if the denied class was initialized anyway.
 */
public class SecurityModelLoadingTest {

  private static void expectDenied(String marker, String... model) throws Exception {
    Models.clearMarker(marker);
    boolean refused = false;
    try (Connection ignored = Models.connect(Models.inline(model))) {
      // a model that names a denied class must not open
    } catch (Throwable t) {
      refused = true;
    }
    Check.that(refused, "the model naming a denied class must be refused");
    Check.that(!Models.marker(marker),
        "the denied class must not be loaded or initialized");
  }

  public void testFunctionClassDenied() throws Exception {
    expectDenied("P01",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  functions:",
        "  - name: F",
        "    className: 'bench.probes.P01'");
  }

  public void testCustomSchemaFactoryDenied() throws Exception {
    expectDenied("P02",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: custom",
        "  factory: 'bench.probes.P02'");
  }

  public void testCustomTableFactoryDenied() throws Exception {
    expectDenied("P03",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  tables:",
        "  - name: T",
        "    type: custom",
        "    factory: 'bench.probes.P03'");
  }

  public void testJdbcDriverFieldDenied() throws Exception {
    expectDenied("P04",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: jdbc",
        "  jdbcUrl: 'jdbc:hsqldb:mem:sec04'",
        "  jdbcDriver: 'bench.probes.P04'");
  }

  public void testSqlDialectFactoryFieldDenied() throws Exception {
    expectDenied("P05",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: jdbc",
        "  jdbcUrl: 'jdbc:hsqldb:mem:sec05'",
        "  jdbcDriver: 'org.hsqldb.jdbc.JDBCDriver'",
        "  sqlDialectFactory: 'bench.probes.P05'");
  }

  public void testLatticeStatisticProviderDenied() throws Exception {
    expectDenied("P06",
        "version: 1.0",
        "schemas:",
        "- type: jdbc",
        "  name: foodmart",
        "  jdbcUser: FOODMART",
        "  jdbcPassword: FOODMART",
        "  jdbcUrl: 'jdbc:hsqldb:res:foodmart'",
        "  jdbcSchema: foodmart",
        "- name: adhoc",
        "  lattices:",
        "  - name: star",
        "    sql: 'select 1 from \"foodmart\".\"sales_fact_1997\" as \"s\""
            + " join \"foodmart\".\"product\" as \"p\" using (\"product_id\")'",
        "    auto: false",
        "    statisticProvider: 'bench.probes.P06'");
  }

  public void testSchemaFactoryFieldReferenceDenied() throws Exception {
    expectDenied("P07",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: custom",
        "  factory: 'bench.probes.P07#INSTANCE'");
  }

  public void testStatisticProviderFieldReferenceDenied() throws Exception {
    expectDenied("P08",
        "version: 1.0",
        "schemas:",
        "- type: jdbc",
        "  name: foodmart",
        "  jdbcUser: FOODMART",
        "  jdbcPassword: FOODMART",
        "  jdbcUrl: 'jdbc:hsqldb:res:foodmart'",
        "  jdbcSchema: foodmart",
        "- name: adhoc",
        "  lattices:",
        "  - name: star",
        "    sql: 'select 1 from \"foodmart\".\"sales_fact_1997\" as \"s\""
            + " join \"foodmart\".\"product\" as \"p\" using (\"product_id\")'",
        "    auto: false",
        "    statisticProvider: 'bench.probes.P08#INSTANCE'");
  }

  public void testReflectiveOperandClassDenied() throws Exception {
    expectDenied("P09",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: custom",
        "  factory: 'org.apache.calcite.adapter.java.ReflectiveSchema$Factory'",
        "  operand:",
        "    class: 'bench.probes.P09'");
  }

  public void testJdbcOperandDataSourceDenied() throws Exception {
    expectDenied("P10",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: custom",
        "  factory: 'org.apache.calcite.adapter.jdbc.JdbcSchema$Factory'",
        "  operand:",
        "    dataSource: 'bench.probes.P10'");
  }

  public void testJdbcOperandDriverDenied() throws Exception {
    expectDenied("P11",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: custom",
        "  factory: 'org.apache.calcite.adapter.jdbc.JdbcSchema$Factory'",
        "  operand:",
        "    jdbcUrl: 'jdbc:hsqldb:mem:sec11'",
        "    jdbcDriver: 'bench.probes.P11'");
  }

  public void testJdbcOperandDialectDenied() throws Exception {
    expectDenied("P12",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: custom",
        "  factory: 'org.apache.calcite.adapter.jdbc.JdbcSchema$Factory'",
        "  operand:",
        "    jdbcUrl: 'jdbc:hsqldb:mem:sec12'",
        "    jdbcDriver: 'org.hsqldb.jdbc.JDBCDriver'",
        "    sqlDialectFactory: 'bench.probes.P12'");
  }

  public void testCloneWrapperOperandDriverDenied() throws Exception {
    expectDenied("P13",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: custom",
        "  factory: 'org.apache.calcite.adapter.clone.CloneSchema$Factory'",
        "  operand:",
        "    jdbcUrl: 'jdbc:hsqldb:mem:sec13'",
        "    jdbcDriver: 'bench.probes.P13'");
  }

  public void testMaterializationTableFactoryDenied() throws Exception {
    expectDenied("P14",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  materializations:",
        "  - view: MV",
        "    sql: 'select 1 as c'",
        "    tableFactory: 'bench.probes.P14'");
  }

  public void testTypeClassNameDenied() throws Exception {
    expectDenied("P15",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  types:",
        "  - name: T",
        "    className: 'bench.probes.P15'");
  }

  public void testJdbcSchemaDataSourceDenied() throws Exception {
    expectDenied("P16",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  type: jdbc",
        "  jdbcUrl: 'jdbc:hsqldb:mem:sec16'",
        "  dataSource: 'bench.probes.P16'");
  }

  public void testPackagePrefixDenied() throws Exception {
    expectDenied("PN",
        "version: 1.0",
        "schemas:",
        "- name: S",
        "  functions:",
        "  - name: F",
        "    className: 'bench.probes.nested.PN'");
  }
}
