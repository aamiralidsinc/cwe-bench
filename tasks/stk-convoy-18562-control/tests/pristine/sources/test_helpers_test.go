package sources

import (
	"context"
	"fmt"
	"os"
	"strings"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/oklog/ulid/v2"
	"github.com/stretchr/testify/require"

	"github.com/frain-dev/convoy/config"
	"github.com/frain-dev/convoy/database"
	"github.com/frain-dev/convoy/database/hooks"
	"github.com/frain-dev/convoy/database/postgres"
	"github.com/frain-dev/convoy/datastore"
	"github.com/frain-dev/convoy/internal/organisations"
	"github.com/frain-dev/convoy/internal/pkg/keys"
	"github.com/frain-dev/convoy/internal/projects"
	"github.com/frain-dev/convoy/internal/users"
	log "github.com/frain-dev/convoy/pkg/logger"
)

func TestMain(m *testing.M) { localTestMain(m) }

func setupTestDB(t *testing.T) (database.Database, context.Context) {
	t.Helper()

	ctx := context.Background()

	err := config.LoadConfig("")
	require.NoError(t, err)

	conn := cloneTestDB(t)

	dbHooks := hooks.Init()
	dbHooks.RegisterHook(datastore.EndpointCreated, func(ctx context.Context, data interface{}, changelog interface{}) {})

	db := postgres.NewFromConnection(conn)

	// Load config again and ensure it's set properly
	err = config.LoadConfig("")
	require.NoError(t, err)

	_, err = config.Get()
	require.NoError(t, err)

	// Initialize KeyManager
	km, err := keys.NewLocalKeyManager("test")
	require.NoError(t, err)

	if km.IsSet() {
		_, err = km.GetCurrentKeyFromCache()
		require.NoError(t, err)
	}

	err = keys.Set(km)
	require.NoError(t, err)

	return db, ctx
}

func seedTestData(t *testing.T, db database.Database) *datastore.Project {
	t.Helper()

	logger := log.New("convoy", log.LevelInfo)
	ctx := context.Background()

	// Create user
	userRepo := users.New(logger, db)
	user := &datastore.User{
		UID:       ulid.Make().String(),
		FirstName: "Test",
		LastName:  "User",
		Email:     fmt.Sprintf("test-%s@example.com", ulid.Make().String()),
	}
	err := userRepo.CreateUser(ctx, user)
	require.NoError(t, err)

	// Create organisation
	orgRepo := organisations.New(logger, db)
	org := &datastore.Organisation{
		UID:     ulid.Make().String(),
		OwnerID: user.UID,
		Name:    fmt.Sprintf("TestOrg-%s", ulid.Make().String()),
	}
	err = orgRepo.CreateOrganisation(ctx, org)
	require.NoError(t, err)

	// Create project
	projectRepo := projects.New(log.New("convoy", log.LevelInfo), db)
	projectConfig := datastore.DefaultProjectConfig
	project := &datastore.Project{
		UID:            ulid.Make().String(),
		Name:           fmt.Sprintf("TestProject-%s", ulid.Make().String()),
		Type:           datastore.OutgoingProject,
		OrganisationID: org.UID,
		Config:         &projectConfig,
	}
	err = projectRepo.CreateProject(ctx, project)
	require.NoError(t, err)

	return project
}

func createSourceService(t *testing.T, db database.Database) *Service {
	t.Helper()

	return New(log.New("convoy", log.LevelInfo), db)
}

// SeedSource creates a test source
func SeedSource(t *testing.T, db database.Database, project *datastore.Project, verifierType datastore.VerifierType) *datastore.Source {
	t.Helper()

	source := &datastore.Source{
		UID:       ulid.Make().String(),
		Name:      fmt.Sprintf("TestSource-%s", ulid.Make().String()),
		Type:      datastore.HTTPSource,
		MaskID:    ulid.Make().String(),
		Provider:  datastore.GithubSourceProvider,
		ProjectID: project.UID,
	}

	// Add verifier based on type
	switch verifierType {
	case datastore.APIKeyVerifier:
		source.Verifier = &datastore.VerifierConfig{
			Type: datastore.APIKeyVerifier,
			ApiKey: &datastore.ApiKey{
				HeaderName:  "X-API-Key",
				HeaderValue: "test-api-key",
			},
		}
	case datastore.BasicAuthVerifier:
		source.Verifier = &datastore.VerifierConfig{
			Type: datastore.BasicAuthVerifier,
			BasicAuth: &datastore.BasicAuth{
				UserName: "testuser",
				Password: "testpass",
			},
		}
	case datastore.HMacVerifier:
		source.Verifier = &datastore.VerifierConfig{
			Type: datastore.HMacVerifier,
			HMac: &datastore.HMac{
				Hash:     "SHA256",
				Header:   "X-Webhook-Signature",
				Secret:   "test-secret",
				Encoding: datastore.Base64Encoding,
			},
		}
	default:
		source.Verifier = &datastore.VerifierConfig{
			Type: datastore.NoopVerifier,
		}
	}

	service := createSourceService(t, db)
	err := service.CreateSource(context.Background(), source)
	require.NoError(t, err)

	return source
}

// cloneTestDB creates a fresh database from the migrated template and drops it when the
// test ends. The template ships with the image; nothing is downloaded.
func cloneTestDB(t *testing.T) *pgxpool.Pool {
	t.Helper()
	ctx := context.Background()
	admin, err := pgxpool.New(ctx, pgDSN("postgres"))
	require.NoError(t, err)
	name := "convoy_proj_" + strings.ToLower(ulid.Make().String())
	_, err = admin.Exec(ctx, "CREATE DATABASE "+name+" WITH TEMPLATE "+tmplName())
	require.NoError(t, err)
	admin.Close()

	pool, err := pgxpool.New(ctx, pgDSN(name))
	require.NoError(t, err)
	t.Cleanup(func() {
		pool.Close()
		a, err := pgxpool.New(context.Background(), pgDSN("postgres"))
		if err != nil {
			return
		}
		defer a.Close()
		_, _ = a.Exec(context.Background(), "DROP DATABASE IF EXISTS "+name+" WITH (FORCE)")
	})
	return pool
}

func envOr(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func pgDSN(db string) string {
	return fmt.Sprintf("postgres://%s:%s@%s:%s/%s?sslmode=disable",
		envOr("CONVOY_TEST_PG_USER", "convoy"), envOr("CONVOY_TEST_PG_PASSWORD", "convoy"),
		envOr("CONVOY_TEST_PG_HOST", "127.0.0.1"), envOr("CONVOY_TEST_PG_PORT", "5432"), db)
}

func tmplName() string { return envOr("CONVOY_TEST_PG_TEMPLATE", "convoy_tmpl") }

func localTestMain(m *testing.M) {
	_ = os.Setenv("CONVOY_JWT_SECRET", "test-access-secret")
	_ = os.Setenv("CONVOY_JWT_REFRESH_SECRET", "test-refresh-secret")
	if err := config.LoadConfig(""); err != nil {
		fmt.Fprintf(os.Stderr, "load config: %v\n", err)
		os.Exit(1)
	}
	dbHooks := hooks.Init()
	dbHooks.RegisterHook(datastore.EndpointCreated, func(ctx context.Context, data interface{}, changelog interface{}) {})
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
	os.Exit(m.Run())
}
