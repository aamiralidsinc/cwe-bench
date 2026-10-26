package hiddentests

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"sync"
	"testing"

	"github.com/go-chi/chi/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/oklog/ulid/v2"
	"github.com/stretchr/testify/require"

	"github.com/frain-dev/convoy"
	"github.com/frain-dev/convoy/api/handlers"
	"github.com/frain-dev/convoy/api/types"
	"github.com/frain-dev/convoy/auth"
	"github.com/frain-dev/convoy/config"
	"github.com/frain-dev/convoy/database"
	"github.com/frain-dev/convoy/database/hooks"
	"github.com/frain-dev/convoy/database/postgres"
	"github.com/frain-dev/convoy/datastore"
	"github.com/frain-dev/convoy/internal/endpoints"
	"github.com/frain-dev/convoy/internal/organisations"
	"github.com/frain-dev/convoy/internal/pkg/keys"
	"github.com/frain-dev/convoy/internal/pkg/license/noop"
	"github.com/frain-dev/convoy/internal/projects"
	"github.com/frain-dev/convoy/internal/sources"
	"github.com/frain-dev/convoy/internal/users"
	log "github.com/frain-dev/convoy/pkg/logger"
)

const (
	secretA = "TENANT-A-VERIFIER-SECRET-MARKER"
	secretB = "TENANT-B-VERIFIER-SECRET-MARKER"
)

var (
	pgHost     = envOr("CONVOY_TEST_PG_HOST", "127.0.0.1")
	pgPort     = envOr("CONVOY_TEST_PG_PORT", "5432")
	pgUser     = envOr("CONVOY_TEST_PG_USER", "convoy")
	pgPassword = envOr("CONVOY_TEST_PG_PASSWORD", "convoy")
	tmplDB     = envOr("CONVOY_TEST_PG_TEMPLATE", "convoy_tmpl")
	setupOnce  sync.Once
)

func envOr(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func dsn(db string) string {
	return fmt.Sprintf("postgres://%s:%s@%s:%s/%s?sslmode=disable", pgUser, pgPassword, pgHost, pgPort, db)
}

func TestMain(m *testing.M) {
	_ = os.Setenv("CONVOY_JWT_SECRET", "test-access-secret")
	_ = os.Setenv("CONVOY_JWT_REFRESH_SECRET", "test-refresh-secret")
	if err := config.LoadConfig(""); err != nil {
		fmt.Fprintf(os.Stderr, "load config: %v\n", err)
		os.Exit(1)
	}
	setupOnce.Do(func() {
		h := hooks.Init()
		h.RegisterHook(datastore.EndpointCreated, func(ctx context.Context, data interface{}, changelog interface{}) {})
		km, err := keys.NewLocalKeyManager("test")
		if err != nil {
			fmt.Fprintf(os.Stderr, "key manager: %v\n", err)
			os.Exit(1)
		}
		if km.IsSet() {
			if _, err := km.GetCurrentKeyFromCache(); err != nil {
				fmt.Fprintf(os.Stderr, "key cache: %v\n", err)
				os.Exit(1)
			}
		}
		if err := keys.Set(km); err != nil {
			fmt.Fprintf(os.Stderr, "set keys: %v\n", err)
			os.Exit(1)
		}
	})
	os.Exit(m.Run())
}

func newTestDB(t *testing.T) database.Database {
	t.Helper()
	ctx := context.Background()
	admin, err := pgxpool.New(ctx, dsn("postgres"))
	require.NoError(t, err)
	name := "convoy_hidden_" + strings.ToLower(ulid.Make().String())
	_, err = admin.Exec(ctx, "CREATE DATABASE "+name+" WITH TEMPLATE "+tmplDB)
	require.NoError(t, err)
	admin.Close()

	pool, err := pgxpool.New(ctx, dsn(name))
	require.NoError(t, err)
	db := postgres.NewFromConnection(pool)
	t.Cleanup(func() {
		pool.Close()
		a, err := pgxpool.New(context.Background(), dsn("postgres"))
		if err != nil {
			return
		}
		defer a.Close()
		_, _ = a.Exec(context.Background(), "DROP DATABASE IF EXISTS "+name+" WITH (FORCE)")
	})
	return db
}

type fixture struct {
	t      *testing.T
	db     database.Database
	logger log.Logger
	app    *handlers.Handler
	projA  *datastore.Project
	projB  *datastore.Project
	srcA   *datastore.Source
	srcB   *datastore.Source
	epA    *datastore.Endpoint
}

func uid() string { return ulid.Make().String() }

func newFixture(t *testing.T, typeA datastore.ProjectType) *fixture {
	t.Helper()
	db := newTestDB(t)
	logger := log.New("hidden", log.LevelError)
	ctx := context.Background()

	userRepo := users.New(logger, db)
	u := &datastore.User{UID: uid(), FirstName: "Hidden", LastName: "Test", Email: uid() + "@example.test"}
	require.NoError(t, userRepo.CreateUser(ctx, u))

	orgRepo := organisations.New(logger, db)
	org := &datastore.Organisation{UID: uid(), OwnerID: u.UID, Name: "org-" + uid()}
	require.NoError(t, orgRepo.CreateOrganisation(ctx, org))

	projRepo := projects.New(logger, db)
	cfgA := datastore.DefaultProjectConfig
	cfgB := datastore.DefaultProjectConfig
	projA := &datastore.Project{UID: uid(), Name: "project-a-" + uid(), Type: typeA, OrganisationID: org.UID, Config: &cfgA}
	projB := &datastore.Project{UID: uid(), Name: "project-b-" + uid(), Type: datastore.IncomingProject, OrganisationID: org.UID, Config: &cfgB}
	require.NoError(t, projRepo.CreateProject(ctx, projA))
	require.NoError(t, projRepo.CreateProject(ctx, projB))

	srcA := addSource(t, db, logger, projA, "source-a", secretA)
	srcB := addSource(t, db, logger, projB, "source-b", secretB)

	epA := &datastore.Endpoint{
		UID: uid(), ProjectID: projA.UID, Name: "endpoint-a", Url: "https://example.test/hook",
		Status: datastore.ActiveEndpointStatus, Secrets: []datastore.Secret{{UID: uid(), Value: "ep-secret"}}, HttpTimeout: 30,
	}
	require.NoError(t, endpoints.New(logger, db).CreateEndpoint(ctx, epA, projA.UID))

	app := &handlers.Handler{A: &types.APIOptions{DB: db, Logger: logger, Licenser: noop.NewLicenser()}}
	return &fixture{t: t, db: db, logger: logger, app: app, projA: projA, projB: projB, srcA: srcA, srcB: srcB, epA: epA}
}

func addSource(t *testing.T, db database.Database, logger log.Logger, p *datastore.Project, name, secret string) *datastore.Source {
	t.Helper()
	src := &datastore.Source{
		UID: uid(), ProjectID: p.UID, MaskID: uid(), Name: name, Type: datastore.HTTPSource,
		Verifier: &datastore.VerifierConfig{Type: datastore.HMacVerifier, HMac: &datastore.HMac{
			Header: "X-Signature", Hash: "SHA256", Secret: secret, Encoding: datastore.Base64Encoding,
		}},
	}
	require.NoError(t, sources.New(logger, db).CreateSource(context.Background(), src))
	return src
}

// request builds an HTTP request authenticated as a project API key for projectID, with chi
// URL parameters pre-populated, exactly as the router and auth middleware would.
func (f *fixture) request(method, target, projectID, body string, params map[string]string) *http.Request {
	rctx := chi.NewRouteContext()
	for k, v := range params {
		rctx.URLParams.Add(k, v)
	}
	ctx := context.WithValue(context.Background(), chi.RouteCtxKey, rctx)
	ctx = context.WithValue(ctx, convoy.PageableCtx, datastore.Pageable{PerPage: 50, Direction: datastore.Next, NextCursor: datastore.DefaultCursor})
	ctx = context.WithValue(ctx, convoy.AuthUserCtx, &auth.AuthenticatedUser{
		Credential: auth.Credential{Type: auth.CredentialTypeAPIKey},
		APIKey:     &datastore.APIKey{Role: auth.Role{Project: projectID}},
	})
	var r *http.Request
	if body == "" {
		r = httptest.NewRequest(method, target, nil)
	} else {
		r = httptest.NewRequest(method, target, strings.NewReader(body))
		r.Header.Set("Content-Type", "application/json")
	}
	return r.WithContext(ctx)
}

func (f *fixture) serve(h http.HandlerFunc, r *http.Request) (int, string) {
	w := httptest.NewRecorder()
	h(w, r)
	return w.Code, w.Body.String()
}

func (f *fixture) getSource(projectID, sourceID string) (int, string) {
	return f.serve(f.app.GetSource, f.request(http.MethodGet, "/v1/projects/"+projectID+"/sources/"+sourceID, projectID, "",
		map[string]string{"projectID": projectID, "sourceID": sourceID}))
}

func (f *fixture) putSource(projectID, sourceID, body string) (int, string) {
	return f.serve(f.app.UpdateSource, f.request(http.MethodPut, "/v1/projects/"+projectID+"/sources/"+sourceID, projectID, body,
		map[string]string{"projectID": projectID, "sourceID": sourceID}))
}

func (f *fixture) deleteSource(projectID, sourceID string) (int, string) {
	return f.serve(f.app.DeleteSource, f.request(http.MethodDelete, "/v1/projects/"+projectID+"/sources/"+sourceID, projectID, "",
		map[string]string{"projectID": projectID, "sourceID": sourceID}))
}

func (f *fixture) createSubscription(projectID, body string) (int, string) {
	return f.serve(f.app.CreateSubscription, f.request(http.MethodPost, "/v1/projects/"+projectID+"/subscriptions", projectID, body,
		map[string]string{"projectID": projectID}))
}

func (f *fixture) updateSubscription(projectID, subID, body string) (int, string) {
	return f.serve(f.app.UpdateSubscription, f.request(http.MethodPut, "/v1/projects/"+projectID+"/subscriptions/"+subID, projectID, body,
		map[string]string{"projectID": projectID, "subscriptionID": subID}))
}

func (f *fixture) getSubscription(projectID, subID string) (int, string) {
	return f.serve(f.app.GetSubscription, f.request(http.MethodGet, "/v1/projects/"+projectID+"/subscriptions/"+subID, projectID, "",
		map[string]string{"projectID": projectID, "subscriptionID": subID}))
}

func (f *fixture) listSubscriptions(projectID string) (int, string) {
	return f.serve(f.app.GetSubscriptions, f.request(http.MethodGet, "/v1/projects/"+projectID+"/subscriptions", projectID, "",
		map[string]string{"projectID": projectID}))
}

func (f *fixture) sourceRow(sourceID string) (projectID, name, secret string) {
	f.t.Helper()
	err := f.db.GetConn().QueryRow(context.Background(), `
		SELECT s.project_id, s.name, COALESCE(sv.hmac_secret, '')
		FROM convoy.sources s
		LEFT JOIN convoy.source_verifiers sv ON sv.id = s.source_verifier_id
		WHERE s.id = $1`, sourceID).Scan(&projectID, &name, &secret)
	require.NoError(f.t, err)
	return
}

func (f *fixture) sourceExists(sourceID string) bool {
	f.t.Helper()
	var n int
	err := f.db.GetConn().QueryRow(context.Background(),
		`SELECT count(*) FROM convoy.sources WHERE id = $1 AND deleted_at IS NULL`, sourceID).Scan(&n)
	require.NoError(f.t, err)
	return n > 0
}

func (f *fixture) subscriptionRow(subID string) (projectID, sourceID string) {
	f.t.Helper()
	err := f.db.GetConn().QueryRow(context.Background(),
		`SELECT project_id, COALESCE(source_id, '') FROM convoy.subscriptions WHERE id = $1`, subID).Scan(&projectID, &sourceID)
	require.NoError(f.t, err)
	return
}

func (f *fixture) subscriptionsBySource(projectID, sourceID string) int {
	f.t.Helper()
	var n int
	err := f.db.GetConn().QueryRow(context.Background(),
		`SELECT count(*) FROM convoy.subscriptions WHERE project_id = $1 AND source_id = $2 AND deleted_at IS NULL`,
		projectID, sourceID).Scan(&n)
	require.NoError(f.t, err)
	return n
}

func (f *fixture) seedSubscription(projectID, sourceID, endpointID string) *datastore.Subscription {
	f.t.Helper()
	sub := &datastore.Subscription{UID: uid(), ProjectID: projectID, Name: "seed-sub-" + uid(),
		Type: datastore.SubscriptionTypeAPI, SourceID: sourceID, EndpointID: endpointID}
	// Persist the row directly: the read path must be tested against data that is already stored,
	// independently of whatever checks a fix adds on the write path.
	_, err := f.db.GetConn().Exec(context.Background(), `
		INSERT INTO convoy.subscriptions
			(id, name, type, project_id, endpoint_id, device_id, source_id,
			 alert_config_count, alert_config_threshold, retry_config_type, retry_config_duration,
			 retry_config_retry_count, filter_config_event_types,
			 filter_config_filter_headers, filter_config_filter_body,
			 rate_limit_config_count, rate_limit_config_duration)
		VALUES ($1, $2, 'api', $3, NULLIF($4, ''), NULL, NULLIF($5, ''), 0, '', '', 0, 0,
			ARRAY['*'], '{}', '{}', 0, 0)`,
		sub.UID, sub.Name, projectID, endpointID, sourceID)
	require.NoError(f.t, err)
	return sub
}

func jsonBody(kv ...string) string {
	var b strings.Builder
	b.WriteString("{")
	for i := 0; i+1 < len(kv); i += 2 {
		if i > 0 {
			b.WriteString(",")
		}
		fmt.Fprintf(&b, "\"%s\":\"%s\"", kv[i], kv[i+1])
	}
	b.WriteString("}")
	return b.String()
}
