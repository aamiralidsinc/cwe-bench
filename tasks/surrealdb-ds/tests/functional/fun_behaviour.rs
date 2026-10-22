#![recursion_limit = "512"]
//! Hidden functional tests: legitimate stored conditions, permission clauses,
//! triggers, views, APIs and schema expressions keep working, including the
//! writes they are allowed to perform.

use surrealdb_core::dbs::Session;
use surrealdb_core::dbs::capabilities::{Capabilities, Targets};
use surrealdb_core::iam::signin::signin;
use surrealdb_core::iam::signup::signup;
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
			text.matches(&format!("Table(\"{table}\")")).count() as i64
		}
		Err(_) => -1,
	}
}

#[tokio::test]
async fn read_only_permission_predicates_keep_working() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE visible SCHEMALESS PERMISSIONS FOR select FULL;
		 DEFINE FUNCTION fn::is_ok() { RETURN true; } PERMISSIONS FULL;
		 DEFINE TABLE docs SCHEMALESS PERMISSIONS FOR select, create FULL;
		 CREATE docs:1 SET published = true;
		 CREATE visible:1 SET ref = docs:1;
		 CREATE docs:2 SET published = false;
		 ALTER TABLE docs PERMISSIONS FOR select WHERE fn::is_ok() AND published = true AND id IN (SELECT VALUE ref FROM visible);",
	)
	.await;
	let (ok, e) = run(&ds, "SELECT * FROM docs;", &rec).await;
	assert!(ok, "read-only predicate failed for a record user: {e}");
	let rs = ds.execute("SELECT * FROM docs", &rec, None).await.unwrap();
	match &rs[0].result {
		Ok(v) => {
			let text = format!("{v:?}");
			assert!(text.contains("docs:1") || text.contains("key: Number(1)"), "missing visible row: {text}");
			assert!(!text.contains("key: Number(2)"), "unpublished row leaked: {text}");
		}
		Err(e) => panic!("select failed: {e}"),
	}
}

#[tokio::test]
async fn event_action_still_writes() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE audit SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE EVENT e ON victim WHEN true THEN { CREATE audit SET marker = 'event'; };",
	)
	.await;
	let (ok, e) = run(&ds, "CREATE victim:1 SET v = 1;", &rec).await;
	assert!(ok, "record create failed: {e}");
	assert_eq!(count(&ds, &owner, "audit").await, 1, "event action did not run");
}

#[tokio::test]
async fn event_condition_can_read_and_call_helpers() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE audit SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE FUNCTION fn::is_ok() { RETURN true; } PERMISSIONS FULL;
		 DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE EVENT e ON victim WHEN fn::is_ok() AND v = 1 THEN { CREATE audit SET marker = 'ok'; };",
	)
	.await;
	let (ok, e) = run(&ds, "CREATE victim:1 SET v = 1;", &rec).await;
	assert!(ok, "record create failed: {e}");
	assert_eq!(count(&ds, &owner, "audit").await, 1, "read-only event condition did not run");
}

#[tokio::test]
async fn materialized_view_still_refreshes() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE src SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE TABLE v AS SELECT name FROM src WHERE name != NONE;",
	)
	.await;
	let (ok, e) = run(&ds, "CREATE src:1 SET name = 'y';", &rec).await;
	assert!(ok, "record create failed: {e}");
	assert_eq!(count(&ds, &owner, "v").await, 1, "view was not refreshed");
}

#[tokio::test]
async fn api_handler_body_still_writes() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE audit SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE FUNCTION fn::is_ok() { RETURN true; } PERMISSIONS FULL;",
	)
	.await;
	setup(
		&ds,
		&owner,
		r#"DEFINE API "/work" FOR get PERMISSIONS WHERE fn::is_ok() THEN {
			CREATE audit SET marker = 'handler';
			{ status: 200, body: { ok: true } }
		};"#,
	)
	.await;
	let (ok, e) = run(&ds, r#"RETURN api::invoke("/work");"#, &rec).await;
	assert!(ok, "api invocation failed: {e}");
	assert_eq!(count(&ds, &owner, "audit").await, 1, "api handler did not run its write");
}

#[tokio::test]
async fn field_permissions_still_filter_and_revert() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE doc SCHEMALESS PERMISSIONS FOR select, update FULL;
		 DEFINE FIELD secret ON doc TYPE option<string> PERMISSIONS FOR select NONE, FOR update NONE;
		 DEFINE FIELD plain ON doc TYPE option<string> PERMISSIONS FULL;
		 CREATE doc:1 SET secret = 'hidden', plain = 'visible';",
	)
	.await;
	let (ok, e) = run(&ds, "UPDATE doc:1 SET secret = 'changed', plain = 'changed';", &rec).await;
	assert!(ok, "record update failed: {e}");
	let rs = ds.execute("SELECT * FROM doc", &owner, None).await.unwrap();
	match &rs[0].result {
		Ok(v) => {
			let text = format!("{v:?}");
			assert!(text.contains("hidden"), "field update permission did not revert: {text}");
			assert!(text.contains("changed") && text.contains("visible") || text.contains("plain"),
				"unexpected field values: {text}");
		}
		Err(e) => panic!("owner select failed: {e}"),
	}
}

#[tokio::test]
async fn assert_and_value_clauses_still_enforce_and_compute() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE doc SCHEMALESS PERMISSIONS FOR select, create, update FULL;
		 DEFINE FIELD doubled ON doc TYPE int VALUE $value * 2 PERMISSIONS FULL;
		 DEFINE FIELD positive ON doc TYPE int ASSERT $value > 0 PERMISSIONS FULL;",
	)
	.await;
	let (ok, e) = run(&ds, "CREATE doc:1 SET doubled = 3, positive = 5;", &rec).await;
	assert!(ok, "valid create rejected: {e}");
	let (bad, _e) = run(&ds, "CREATE doc:2 SET doubled = 1, positive = -1;", &rec).await;
	assert!(!bad, "ASSERT did not reject a negative value");
	let rs = ds.execute("SELECT * FROM doc", &owner, None).await.unwrap();
	match &rs[0].result {
		Ok(v) => {
			let text = format!("{v:?}");
			assert!(text.contains("Number(Int(6))") || text.contains("Int(6)"), "VALUE did not compute: {text}");
		}
		Err(e) => panic!("owner select failed: {e}"),
	}
}

#[tokio::test]
async fn alter_with_read_only_permissions_works() {
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
		"ALTER TABLE base PERMISSIONS FOR select WHERE published = true;",
		"ALTER FIELD f ON base PERMISSIONS FOR update WHERE $value > 0;",
		"ALTER FUNCTION fn::a() { RETURN true; } PERMISSIONS WHERE $auth.id != NONE;",
		"ALTER PARAM $p PERMISSIONS WHERE $auth.id != NONE;",
		"ALTER BUCKET b PERMISSIONS WHERE $action = \"put\";",
	];
	for sql in cases {
		let (ok, e) = run(&ds, sql, &owner).await;
		assert!(ok, "read-only ALTER rejected: {e}\nSQL: {sql}");
	}
}

#[tokio::test]
async fn function_and_param_permissions_still_allow_reads() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE FUNCTION fn::g() { RETURN 2; } PERMISSIONS WHERE true;
		 DEFINE PARAM $p VALUE 3 PERMISSIONS WHERE true;
		 DEFINE TABLE doc SCHEMALESS PERMISSIONS FOR select, update FULL;
		 CREATE doc:1 SET n = 0;",
	)
	.await;
	let (ok, e) = run(&ds, "UPDATE doc:1 SET n = fn::g() + $p;", &rec).await;
	assert!(ok, "read-only function/param permissions failed: {e}");
	let rs = ds.execute("SELECT * FROM doc", &owner, None).await.unwrap();
	match &rs[0].result {
		Ok(v) => assert!(format!("{v:?}").contains("Int(5)"), "computed value missing: {v:?}"),
		Err(e) => panic!("owner select failed: {e}"),
	}
}

#[tokio::test]
async fn bucket_read_only_permissions_still_work() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		r#"DEFINE BUCKET b BACKEND "memory" PERMISSIONS WHERE $action = "put" OR $action = "get";"#,
	)
	.await;
	let (ok, e) = run(&ds, r#"file::put(f"b:/k", "value");"#, &rec).await;
	assert!(ok, "bucket put failed: {e}");
	let (ok, e) = run(&ds, r#"RETURN file::get(f"b:/k");"#, &rec).await;
	assert!(ok, "bucket get failed: {e}");
}

#[tokio::test]
async fn direct_record_access_still_works() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE doc SCHEMALESS PERMISSIONS FOR select, create, update, delete FULL;
		 CREATE doc:1 SET v = 1;",
	)
	.await;
	let (ok, e) = run(&ds, "CREATE doc:2 SET v = 2;", &rec).await;
	assert!(ok, "record create failed: {e}");
	let (ok, e) = run(&ds, "UPDATE doc:2 SET v = 3;", &rec).await;
	assert!(ok, "record update failed: {e}");
	let (ok, e) = run(&ds, "DELETE doc:2;", &rec).await;
	assert!(ok, "record delete failed: {e}");
	let (ok, e) = run(&ds, "SELECT * FROM doc;", &rec).await;
	assert!(ok, "record select failed: {e}");
}

#[tokio::test]
async fn owner_can_define_and_use_side_effecting_event_body() {
	let (ds, owner, _rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE audit SCHEMALESS PERMISSIONS FULL;
		 DEFINE TABLE doc SCHEMALESS PERMISSIONS FULL;
		 DEFINE EVENT e ON doc WHEN true THEN { CREATE audit SET marker = 'owner'; };",
	)
	.await;
	let (ok, e) = run(&ds, "CREATE doc:1 SET v = 1;", &owner).await;
	assert!(ok, "owner create failed: {e}");
	assert_eq!(count(&ds, &owner, "audit").await, 1, "owner event body did not write");
}

// A function's stored permission predicate keeps working on the execution
// plan: read-only predicates (including nested helper calls) allow the call,
// and a false predicate still denies it.
#[tokio::test]
async fn streaming_function_permission_still_gates_and_reads() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE FUNCTION fn::is_ok() { RETURN true; } PERMISSIONS FULL;
		 DEFINE FUNCTION fn::g() { RETURN 2; } PERMISSIONS WHERE fn::is_ok();
		 DEFINE FUNCTION fn::no() { RETURN 3; } PERMISSIONS WHERE false;
		 DEFINE TABLE victim SCHEMALESS PERMISSIONS FOR select FULL;
		 CREATE victim:1 SET n = 0;",
	)
	.await;
	let (ok, e) = run(&ds, "RETURN fn::g();", &rec).await;
	assert!(ok, "read-only function permission failed: {e}");
	let (ok, e) = run(&ds, "SELECT VALUE fn::g() FROM victim;", &rec).await;
	assert!(ok, "read-only function permission failed in a projection: {e}");
	let (denied, _e) = run(&ds, "RETURN fn::no();", &rec).await;
	assert!(!denied, "a false function permission predicate was not enforced");
}

// The body of the function being called is not the stored predicate: when the
// predicate passes, the body keeps the caller's context and its writes run.
#[tokio::test]
async fn function_body_writes_outside_permission_still_work() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE audit SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE FUNCTION fn::writer() { CREATE audit SET marker = 'body'; RETURN true; } PERMISSIONS FULL;",
	)
	.await;
	let (ok, e) = run(&ds, "RETURN fn::writer();", &rec).await;
	assert!(ok, "a function body write failed: {e}");
	assert_eq!(count(&ds, &owner, "audit").await, 1, "the function body did not write");
}

// Computed fields still compute, and they are evaluated with the caller's
// permissions: a computed field cannot become a way to read a restricted
// table.
#[tokio::test]
async fn computed_field_still_computes_and_keeps_permissions() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE secret SCHEMALESS PERMISSIONS FOR select NONE;
		 CREATE secret:1 SET name = 'classified';
		 DEFINE TABLE doc SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE FIELD doubled ON doc TYPE int COMPUTED (x * 2);
		 DEFINE FIELD peek ON doc TYPE option<array<string>>
			COMPUTED (SELECT VALUE name FROM secret:1 LIMIT 1);",
	)
	.await;
	let (ok, e) = run(&ds, "CREATE doc:1 SET x = 3;", &rec).await;
	assert!(ok, "create with computed fields failed: {e}");
	let rs = ds.execute("SELECT * FROM doc", &rec, None).await.unwrap();
	match &rs[0].result {
		Ok(v) => {
			let text = format!("{v:?}");
			assert!(
				text.contains("Int(6)") || text.contains("Number(Int(6))"),
				"computed field did not compute: {text}"
			);
			assert!(
				!text.contains("classified"),
				"a computed field bypassed the caller's permissions: {text}"
			);
		}
		Err(e) => panic!("record select failed: {e}"),
	}
}

// DEFAULT and VALUE expressions still apply for legitimate writers.
#[tokio::test]
async fn default_and_value_clauses_still_compute() {
	let (ds, owner, rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE TABLE doc SCHEMALESS PERMISSIONS FOR select, create FULL;
		 DEFINE FIELD d ON doc TYPE int DEFAULT 5;
		 DEFINE FIELD v ON doc TYPE int VALUE $value * 2;",
	)
	.await;
	let (ok, e) = run(&ds, "CREATE doc:1 SET v = 3;", &rec).await;
	assert!(ok, "create with DEFAULT/VALUE failed: {e}");
	let rs = ds.execute("SELECT * FROM doc", &owner, None).await.unwrap();
	match &rs[0].result {
		Ok(v) => {
			let text = format!("{v:?}");
			assert!(
				text.contains("Int(5)") || text.contains("Number(Int(5))"),
				"DEFAULT was not applied: {text}"
			);
			assert!(
				text.contains("Int(6)") || text.contains("Number(Int(6))"),
				"VALUE was not computed: {text}"
			);
		}
		Err(e) => panic!("owner select failed: {e}"),
	}
}

// Read-only access clauses keep working: SIGNUP is allowed to create the
// account record (that is its own work), and a read-only SIGNIN issues a
// token.
#[tokio::test]
async fn read_only_signin_and_signup_still_work() {
	let (ds, owner, _rec) = open_db().await;
	setup(
		&ds,
		&owner,
		"DEFINE ACCESS member ON DATABASE TYPE RECORD
			SIGNUP (CREATE user SET name = $name) SIGNIN ($rid)
			WITH JWT ALGORITHM HS512 KEY 'secret' DURATION FOR TOKEN 15m;",
	)
	.await;
	let mut session = Session::owner();
	let mut vars = Variables::new();
	vars.insert("NS", "test");
	vars.insert("DB", "test");
	vars.insert("AC", "member");
	vars.insert("name", "alice");
	let res = signup(&ds, &mut session, vars).await;
	assert!(res.is_ok(), "read-only SIGNUP failed: {:?}", res.err().map(|e| e.to_string()));
	let rs = ds.execute("SELECT * FROM user", &owner, None).await.unwrap();
	match &rs[0].result {
		Ok(v) => assert!(format!("{v:?}").contains("alice"), "SIGNUP did not create the account"),
		Err(e) => panic!("owner select failed: {e}"),
	}
	let mut session = Session::owner();
	let mut vars = Variables::new();
	vars.insert("NS", "test");
	vars.insert("DB", "test");
	vars.insert("AC", "member");
	vars.insert("rid", PubValue::RecordId(RecordId::new("user", "test")));
	let res = signin(&ds, &mut session, vars).await;
	assert!(res.is_ok(), "read-only SIGNIN failed: {:?}", res.err().map(|e| e.to_string()));
}
