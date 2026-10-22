#![recursion_limit = "512"]
//! Hidden security tests: stored conditions and permission expressions must
//! never modify data. All tests go through the public entry points: a
//! Datastore executing a client session's statements, and the signin RPC a
//! record-access client sends.

use surrealdb_core::dbs::Session;
use surrealdb_core::dbs::capabilities::{Capabilities, Targets};
use surrealdb_core::iam::signin::signin;
use surrealdb_core::kvs::Datastore;
use surrealdb_types::{RecordId, Value as PubValue, Variables};

async fn new_ds() -> Datastore {
	let caps = Capabilities::all().with_experimental(Targets::All);
	Datastore::builder()
		.with_auth(true)
		.with_capabilities(caps)
		.build_with_path("memory")
		.await
		.unwrap()
}

/// Run a statement batch and return whether every statement succeeded plus the
/// first error text (if any).
async fn run(ds: &Datastore, sql: &str, s: &Session) -> (bool, String) {
	match ds.execute(sql, s, None).await {
		Ok(rs) => {
			for r in rs {
				if let Err(e) = r.result {
					return (false, format!("{e}"));
				}
			}
			(true, String::new())
		}
		Err(e) => (false, format!("{e}")),
	}
}

async fn setup(ds: &Datastore, owner: &Session, sql: &str) {
	let (ok, e) = run(ds, sql, owner).await;
	assert!(ok, "test setup failed: {e}\nSQL: {sql}");
}

async fn open_db() -> (Datastore, Session, Session) {
	let ds = new_ds().await;
	let _ = run(&ds, "DEFINE NAMESPACE test", &Session::owner()).await;
	let _ = run(&ds, "DEFINE DATABASE test", &Session::owner().with_ns("test")).await;
	let owner = Session::owner().with_ns("test").with_db("test");
	let (ok, e) = run(
		&ds,
		"DEFINE ACCESS user ON DATABASE TYPE RECORD SIGNIN ($rid); CREATE user:test;",
		&owner,
	)
	.await;
	assert!(ok, "access setup failed: {e}");
	let rec = Session::for_record(
		"test",
		"test",
		"user",
		PubValue::RecordId(RecordId::new("user", "test")),
	);
	(ds, owner, rec)
}

async fn count(ds: &Datastore, owner: &Session, table: &str) -> i64 {
	let sql = format!("SELECT * FROM {table}");
	let rs = ds.execute(&sql, owner, None).await.unwrap();
	match &rs[0].result {
		Ok(v) => {
			let text = format!("{v:?}");
			let needle = format!("Table(\"{table}\")");
			text.matches(&needle).count() as i64
		}
		Err(_) => -1,
	}
}

/// A side-effecting helper function: its body creates a marker row.
const LEAK: &str = r#"
DEFINE TABLE audit SCHEMALESS PERMISSIONS FOR select, create, update, delete FULL;
DEFINE FUNCTION fn::leak() { CREATE audit SET marker = true; RETURN true; } PERMISSIONS FULL;
"#;

/// Assert the record user's request produced no marker row. The request should
/// also be refused, but the invariant scored here is the absence of the write.
async fn assert_blocked(ds: &Datastore, owner: &Session, sql: &str, rec: &Session, label: &str) {
	let (ok, err) = run(ds, sql, rec).await;
	assert!(!ok, "{label}: the request was not refused (expected a client error)");
	let n = count(ds, owner, "audit").await;
	assert_eq!(n, 0, "{label}: predicate performed {n} write(s) ({err})");
}

#[tokio::test]
async fn table_update_permission_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, update WHERE fn::leak(); CREATE victim:1 SET v = 1;",
	)
	.await;
	assert_blocked(&ds, &owner, "UPDATE victim:1 SET v = 2;", &rec, "update permission").await;
}

#[tokio::test]
async fn table_delete_permission_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, delete WHERE fn::leak(); CREATE victim:1 SET v = 1;",
	)
	.await;
	assert_blocked(&ds, &owner, "DELETE victim:1;", &rec, "delete permission").await;
}

#[tokio::test]
async fn table_create_permission_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, create WHERE fn::leak();",
	)
	.await;
	assert_blocked(&ds, &owner, "CREATE victim:2 SET v = 1;", &rec, "create permission").await;
}

#[tokio::test]
async fn streaming_select_inside_write_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select WHERE fn::leak(), FOR update FULL; CREATE victim:1 SET v = 1;",
	)
	.await;
	assert_blocked(
		&ds,
		&owner,
		"UPDATE victim:1 SET n = array::len((SELECT VALUE id FROM victim));",
		&rec,
		"streaming select permission",
	)
	.await;
}

#[tokio::test]
async fn field_select_permission_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, update FULL;
		 DEFINE FIELD secret ON victim TYPE option<string> PERMISSIONS FOR select WHERE fn::leak();
		 CREATE victim:1 SET secret = 's';",
	)
	.await;
	assert_blocked(&ds, &owner, "UPDATE victim:1 SET n = 1;", &rec, "field select permission").await;
}

#[tokio::test]
async fn field_update_permission_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, update FULL;
		 DEFINE FIELD secret ON victim TYPE option<string> PERMISSIONS FOR update WHERE fn::leak();
		 CREATE victim:1 SET secret = 's';",
	)
	.await;
	assert_blocked(&ds, &owner, "UPDATE victim:1 SET secret = 't';", &rec, "field update permission")
		.await;
}

#[tokio::test]
async fn function_permission_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE FUNCTION fn::g() { RETURN 1; } PERMISSIONS WHERE fn::leak();
		 DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, update FULL;
		 CREATE victim:1 SET n = 0;",
	)
	.await;
	assert_blocked(&ds, &owner, "UPDATE victim:1 SET n = fn::g();", &rec, "function permission").await;
}

#[tokio::test]
async fn param_permission_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE PARAM $secret VALUE 1 PERMISSIONS WHERE fn::leak();
		 DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, update FULL;
		 CREATE victim:1 SET n = 0;",
	)
	.await;
	assert_blocked(&ds, &owner, "UPDATE victim:1 SET n = $secret;", &rec, "param permission").await;
}

#[tokio::test]
async fn api_permission_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		r#"DEFINE API "/guarded" FOR get PERMISSIONS WHERE fn::leak() THEN { { status: 200, body: { } } };"#,
	)
	.await;
	assert_blocked(&ds, &owner, r#"RETURN api::invoke("/guarded");"#, &rec, "api permission").await;
}

#[tokio::test]
async fn event_condition_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE EVENT e ON victim WHEN fn::leak() THEN { RETURN NONE; };",
	)
	.await;
	assert_blocked(&ds, &owner, "CREATE victim:3 SET v = 1;", &rec, "event condition").await;
}

#[tokio::test]
async fn view_condition_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE TABLE v AS SELECT name FROM victim WHERE fn::leak();",
	)
	.await;
	assert_blocked(&ds, &owner, "CREATE victim:4 SET name = 'x';", &rec, "view condition").await;
}

#[tokio::test]
async fn define_rejects_direct_write_shapes() {
	let (ds, owner, _rec) = open_db().await;
	let cases = [
		"DEFINE TABLE bad1 PERMISSIONS FOR select WHERE (CREATE audit) OR true;",
		"DEFINE TABLE bad2 PERMISSIONS FOR select WHERE IF true { CREATE audit; true } ELSE { true };",
		"DEFINE TABLE bad3 PERMISSIONS FOR select WHERE { LET $x = CREATE audit; RETURN true; };",
		"DEFINE TABLE bad4 PERMISSIONS FOR select WHERE { FOR $x IN [1] { CREATE audit; RETURN true; }; RETURN true; };",
	];
	for sql in cases {
		let (ok, _e) = run(&ds, sql, &owner).await;
		assert!(!ok, "definition with a side-effecting predicate was accepted: {sql}");
	}
}

#[tokio::test]
async fn define_rejects_write_in_call_argument() {
	let (ds, owner, _rec) = open_db().await;
	setup(&ds, &owner, "DEFINE FUNCTION fn::is_ok($x: bool) { RETURN true; } PERMISSIONS FULL;").await;
	let (ok, _e) = run(
		&ds,
		"DEFINE TABLE bad5 PERMISSIONS FOR select WHERE fn::is_ok((CREATE audit) OR true);",
		&owner,
	)
	.await;
	assert!(!ok, "definition with a side effect in a call argument was accepted");
}

#[tokio::test]
async fn define_rejects_direct_write_on_every_clause() {
	let (ds, owner, _rec) = open_db().await;
	setup(&ds, &owner, "DEFINE TABLE base SCHEMALESS;").await;
	let cases = [
		"DEFINE FIELD fbad ON base TYPE option<number> PERMISSIONS FOR update WHERE (UPDATE audit SET x = 1) OR true;",
		"DEFINE FUNCTION fn::fbad() { RETURN true; } PERMISSIONS WHERE (DELETE audit) OR true;",
		"DEFINE PARAM $fbad VALUE 1 PERMISSIONS WHERE (CREATE audit) OR true;",
		r#"DEFINE API "/bad" FOR get PERMISSIONS WHERE (CREATE audit) OR true THEN { { status: 200, body: { } } };"#,
		r#"DEFINE BUCKET bbad BACKEND "memory" PERMISSIONS WHERE (CREATE audit) OR true;"#,
	];
	for sql in cases {
		let (ok, _e) = run(&ds, sql, &owner).await;
		assert!(!ok, "definition with a side-effecting predicate was accepted: {sql}");
	}
}

#[tokio::test]
async fn alter_table_rejects_side_effecting_permission() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, update WHERE published = true; CREATE victim:1 SET published = false;",
	)
	.await;
	let (ok, _e) = run(
		&ds,
		"ALTER TABLE victim PERMISSIONS FOR select, update WHERE (CREATE audit) OR true;",
		&owner,
	)
	.await;
	assert!(!ok, "ALTER TABLE accepted a side-effecting permission predicate");
	// The rejected ALTER must not change the stored predicate: a record user
	// still cannot see the unpublished row.
	let (ok, e) = run(&ds, "SELECT * FROM victim;", &rec).await;
	assert!(ok, "select after rejected ALTER failed: {e}");
	let rs = ds.execute("SELECT * FROM victim", &rec, None).await.unwrap();
	match &rs[0].result {
		Ok(v) => assert!(
			!format!("{v:?}").contains("published"),
			"rejected ALTER changed the predicate: {v:?}"
		),
		Err(e) => panic!("select after rejected ALTER failed: {e}"),
	}
}

#[tokio::test]
async fn alter_field_function_param_bucket_reject_side_effect() {
	let (ds, owner, _rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE base SCHEMALESS; DEFINE FIELD f ON base TYPE option<number> PERMISSIONS FULL;
		 DEFINE FUNCTION fn::a() { RETURN true; } PERMISSIONS FULL;
		 DEFINE PARAM $p VALUE 1 PERMISSIONS FULL;
		 DEFINE BUCKET b BACKEND \"memory\" PERMISSIONS FULL;",
	)
	.await;
	let cases = [
		"ALTER FIELD f ON base PERMISSIONS FOR update WHERE (CREATE audit) OR true;",
		"ALTER FUNCTION fn::a() { RETURN true; } PERMISSIONS WHERE (CREATE audit) OR true;",
		"ALTER PARAM $p PERMISSIONS WHERE (CREATE audit) OR true;",
		"ALTER BUCKET b PERMISSIONS WHERE (CREATE audit) OR true;",
	];
	for sql in cases {
		let (ok, _e) = run(&ds, sql, &owner).await;
		assert!(!ok, "ALTER accepted a side-effecting permission predicate: {sql}");
	}
}

#[tokio::test]
async fn assert_clause_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE guarded SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE TABLE audit_guard SCHEMALESS PERMISSIONS FOR select FULL;
		 DEFINE FUNCTION fn::leak_guard() { CREATE audit_guard SET marker = true; RETURN true; } PERMISSIONS FULL;",
	)
	.await;
	// Either the store request is refused, or the write is refused when the
	// clause is evaluated. Both satisfy the invariant.
	if stored(
		&ds,
		&owner,
		"DEFINE FIELD n ON guarded TYPE option<number> ASSERT (fn::leak_guard()) OR true;",
	)
	.await
	{
		let (ok, _e) = run(&ds, "CREATE guarded:1 SET n = 1;", &rec).await;
		assert!(!ok, "ASSERT clause write was not refused");
	}
	let n = count(&ds, &owner, "audit_guard").await;
	assert_eq!(n, 0, "ASSERT clause performed {n} write(s)");
}

#[tokio::test]
async fn value_clause_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE guarded SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE TABLE audit_guard SCHEMALESS PERMISSIONS FOR select FULL;
		 DEFINE FUNCTION fn::leak_guard() { CREATE audit_guard SET marker = true; RETURN true; } PERMISSIONS FULL;",
	)
	.await;
	if stored(&ds, &owner, "DEFINE FIELD v ON guarded TYPE option<bool> VALUE (fn::leak_guard());").await
	{
		let (ok, _e) = run(&ds, "CREATE guarded:2 SET v = true;", &rec).await;
		assert!(!ok, "VALUE clause write was not refused");
	}
	let n = count(&ds, &owner, "audit_guard").await;
	assert_eq!(n, 0, "VALUE clause performed {n} write(s)");
}

/// A side-effecting helper used by the schema-expression and access-clause
/// routes: its body creates a marker row in a second table.
const GUARD_LEAK: &str = r#"
DEFINE TABLE audit_guard SCHEMALESS PERMISSIONS FOR select, create FULL;
DEFINE FUNCTION fn::leak_guard() { CREATE audit_guard SET marker = true; RETURN 7; } PERMISSIONS FULL;
"#;

async fn assert_no_guard_write(ds: &Datastore, owner: &Session, label: &str) {
	let n = count(ds, owner, "audit_guard").await;
	assert_eq!(n, 0, "{label}: the stored expression performed {n} write(s)");
}

/// Store a definition and report whether it was accepted. Refusing the store
/// request is also a valid fix (an expression able to reach a write must not
/// be stored), so callers treat `false` as the blocked outcome.
async fn stored(ds: &Datastore, owner: &Session, sql: &str) -> bool {
	run(ds, sql, owner).await.0
}

// A function's stored PERMISSIONS predicate is evaluated by the execution
// plan when the call is not part of a document-write pipeline. A write reached
// from that predicate (through a helper body) must still be refused.
#[tokio::test]
async fn streaming_function_permission_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE FUNCTION fn::g() { RETURN 1; } PERMISSIONS WHERE fn::leak();",
	)
	.await;
	assert_blocked(&ds, &owner, "RETURN fn::g();", &rec, "streaming function permission").await;
}

// The same predicate is evaluated when the call appears in a projection.
#[tokio::test]
async fn streaming_select_function_permission_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, LEAK).await;
	setup(
		&ds,
		&owner,
		"DEFINE FUNCTION fn::g() { RETURN 1; } PERMISSIONS WHERE fn::leak();
		 DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select FULL;
		 CREATE victim:1 SET n = 0;",
	)
	.await;
	assert_blocked(
		&ds,
		&owner,
		"SELECT VALUE fn::g() FROM victim;",
		&rec,
		"streaming select function permission",
	)
	.await;
}

// A computed field is a stored schema expression: evaluating it during a
// write must not change data.
#[tokio::test]
async fn computed_field_cannot_write_on_create() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, GUARD_LEAK).await;
	setup(&ds, &owner, "DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, create FULL;").await;
	if stored(&ds, &owner, "DEFINE FIELD c ON victim COMPUTED (fn::leak_guard());").await {
		let (ok, err) = run(&ds, "CREATE victim:1 SET x = 1;", &rec).await;
		assert!(!ok, "computed field write was not refused (it succeeded): {err}");
	}
	assert_no_guard_write(&ds, &owner, "computed field on create").await;
}

// The same stored computed field evaluated by a projection inside a write.
#[tokio::test]
async fn computed_field_cannot_write_in_write_expression() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, GUARD_LEAK).await;
	setup(&ds, &owner, "DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, update FULL;").await;
	if stored(&ds, &owner, "DEFINE FIELD c ON victim COMPUTED (fn::leak_guard());").await {
		setup(&ds, &owner, "CREATE victim:1 SET x = 1 RETURN NONE;").await;
		let (ok, err) = run(
			&ds,
			"UPDATE victim:1 SET n = array::len((SELECT VALUE c FROM victim));",
			&rec,
		)
		.await;
		assert!(!ok, "computed field write in a write expression was not refused: {err}");
	}
	assert_no_guard_write(&ds, &owner, "computed field in a write expression").await;
}

// A field DEFAULT expression is a stored schema expression too.
#[tokio::test]
async fn default_clause_cannot_write() {
	let (ds, owner, rec) = open_db().await;
	setup(&ds, &owner, GUARD_LEAK).await;
	setup(&ds, &owner, "DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, create FULL;").await;
	if stored(&ds, &owner, "DEFINE FIELD d ON victim TYPE int DEFAULT (fn::leak_guard());").await {
		let (ok, err) = run(&ds, "CREATE victim:1 SET x = 1;", &rec).await;
		assert!(!ok, "DEFAULT clause write was not refused (it succeeded): {err}");
	}
	assert_no_guard_write(&ds, &owner, "DEFAULT clause").await;
}

// A record access method's stored SIGNIN clause is evaluated before the
// client's session exists; a write reached from it must be refused.
#[tokio::test]
async fn signin_clause_cannot_write() {
	let (ds, owner, _rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE audit SCHEMALESS PERMISSIONS FOR select, create FULL;",
	)
	.await;
	// Refusing to store the side-effecting access clause is also a valid fix.
	if stored(
		&ds,
		&owner,
		"DEFINE ACCESS evil ON DATABASE TYPE RECORD
			SIGNIN ((CREATE audit SET marker = 'signin') OR $rid)
			WITH JWT ALGORITHM HS512 KEY 'secret' DURATION FOR TOKEN 15m;",
	)
	.await
	{
		let mut session = Session::owner();
		let mut vars = Variables::new();
		vars.insert("NS", "test");
		vars.insert("DB", "test");
		vars.insert("AC", "evil");
		vars.insert("rid", PubValue::RecordId(RecordId::new("user", "test")));
		let res = signin(&ds, &mut session, vars).await;
		assert!(res.is_err(), "the signin request was not refused");
	}
	assert_eq!(
		count(&ds, &owner, "audit").await,
		0,
		"SIGNIN clause performed a write"
	);
}
