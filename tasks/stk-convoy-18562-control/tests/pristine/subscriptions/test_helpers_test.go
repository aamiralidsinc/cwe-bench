package subscriptions

import (
	"context"
	"fmt"
	"os"
	"strings"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/oklog/ulid/v2"
	"github.com/stretchr/testify/require"
	"gopkg.in/guregu/null.v4"

	"github.com/frain-dev/convoy/config"
	"github.com/frain-dev/convoy/database"
	"github.com/frain-dev/convoy/database/hooks"
	"github.com/frain-dev/convoy/database/postgres"
	"github.com/frain-dev/convoy/datastore"
	"github.com/frain-dev/convoy/internal/endpoints"
	"github.com/frain-dev/convoy/internal/organisations"
	"github.com/frain-dev/convoy/internal/pkg/keys"
	"github.com/frain-dev/convoy/internal/projects"
	"github.com/frain-dev/convoy/internal/sources"
	"github.com/frain-dev/convoy/internal/users"
	log "github.com/frain-dev/convoy/pkg/logger"
)

func TestMain(m *testing.M) { localTestMain(m) }

// setupTestDB initializes a test database connection with encryption key manager
func setupTestDB(t *testing.T) (database.Database, context.Context, *Service) {
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

	logger := log.New("convoy", log.LevelInfo)
	service := New(logger, db)

	return db, ctx, service
}

// seedUser creates a test user
func seedUser(t *testing.T, db database.Database) *datastore.User {
	t.Helper()

	uid := ulid.Make().String()
	user := &datastore.User{
		UID:       uid,
		FirstName: "Test",
		LastName:  "User",
		Email:     fmt.Sprintf("test-%s@user.com", uid),
	}

	userRepo := users.New(log.New("convoy", log.LevelError), db)
	err := userRepo.CreateUser(context.Background(), user)
	require.NoError(t, err)

	return user
}

// seedOrganisation creates a test organisation
func seedOrganisation(t *testing.T, db database.Database, user *datastore.User) *datastore.Organisation {
	t.Helper()

	org := &datastore.Organisation{
		UID:            ulid.Make().String(),
		Name:           "Test Org",
		OwnerID:        user.UID,
		CustomDomain:   null.NewString("", false),
		AssignedDomain: null.NewString("test.convoy.io", true),
	}

	logger := log.New("convoy", log.LevelInfo)
	orgRepo := organisations.New(logger, db)
	err := orgRepo.CreateOrganisation(context.Background(), org)
	require.NoError(t, err)

	return org
}

// seedProject creates a test project
func seedProject(t *testing.T, db database.Database, org *datastore.Organisation) *datastore.Project {
	t.Helper()

	projectConfig := datastore.DefaultProjectConfig
	project := &datastore.Project{
		UID:            ulid.Make().String(),
		Name:           "Test Project",
		OrganisationID: org.UID,
		Type:           datastore.OutgoingProject,
		Config:         &projectConfig,
	}

	logger := log.New("convoy", log.LevelInfo)
	projectRepo := projects.New(logger, db)
	err := projectRepo.CreateProject(context.Background(), project)
	require.NoError(t, err)

	return project
}

// seedEndpoint creates a test endpoint
func seedEndpoint(t *testing.T, db database.Database, project *datastore.Project) *datastore.Endpoint {
	t.Helper()

	endpoint := &datastore.Endpoint{
		UID:         ulid.Make().String(),
		ProjectID:   project.UID,
		Name:        "Test Endpoint",
		Url:         "https://api.example.com/webhook",
		Status:      datastore.ActiveEndpointStatus,
		Secrets:     []datastore.Secret{{UID: ulid.Make().String(), Value: "secret"}},
		HttpTimeout: 30,
	}

	endpointRepo := endpoints.New(log.New("convoy", log.LevelInfo), db)
	err := endpointRepo.CreateEndpoint(context.Background(), endpoint, project.UID)
	require.NoError(t, err)

	return endpoint
}

// seedSource creates a test source
func seedSource(t *testing.T, db database.Database, project *datastore.Project) *datastore.Source {
	t.Helper()

	source := &datastore.Source{
		UID:       ulid.Make().String(),
		ProjectID: project.UID,
		Name:      "Test Source",
		Type:      datastore.HTTPSource,
		MaskID:    ulid.Make().String(),
		Verifier: &datastore.VerifierConfig{
			Type: datastore.HMacVerifier,
			HMac: &datastore.HMac{
				Header:   "X-Webhook-Signature",
				Hash:     "SHA256",
				Secret:   "test-secret",
				Encoding: datastore.HexEncoding,
			},
		},
	}

	logger := log.New("convoy", log.LevelInfo)
	sourceRepo := sources.New(logger, db)
	err := sourceRepo.CreateSource(context.Background(), source)
	require.NoError(t, err)

	return source
}

// seedDevice creates a test device
func seedDevice(t *testing.T, db database.Database, project *datastore.Project) *datastore.Device {
	t.Helper()

	device := &datastore.Device{
		UID:       ulid.Make().String(),
		ProjectID: project.UID,
		HostName:  "test-device.example.com",
		Status:    datastore.DeviceStatusOnline,
	}

	// Create device directly via SQL since there's no dedicated repository
	// Note: endpoint_id was removed from devices table in migration 1679836136.sql
	query := `INSERT INTO convoy.devices (id, project_id, host_name, status, last_seen_at, created_at, updated_at)
              VALUES ($1, $2, $3, $4, NOW(), NOW(), NOW())`

	_, err := db.GetConn().Exec(context.Background(), query,
		device.UID, device.ProjectID, device.HostName, device.Status)
	require.NoError(t, err)

	return device
}

// seedTestData creates all test fixtures
func seedTestData(t *testing.T, db database.Database) (*datastore.Project, *datastore.Endpoint, *datastore.Source, *datastore.Device) {
	t.Helper()

	user := seedUser(t, db)
	org := seedOrganisation(t, db, user)
	project := seedProject(t, db, org)
	endpoint := seedEndpoint(t, db, project)
	source := seedSource(t, db, project)
	device := seedDevice(t, db, project)

	return project, endpoint, source, device
}

// createTestSubscription creates a test subscription with default configurations
func createTestSubscription(project *datastore.Project, endpoint *datastore.Endpoint, source *datastore.Source) *datastore.Subscription {
	return &datastore.Subscription{
		UID:        ulid.Make().String(),
		Name:       "Test Subscription",
		Type:       datastore.SubscriptionTypeAPI,
		ProjectID:  project.UID,
		EndpointID: endpoint.UID,
		SourceID:   source.UID,
		FilterConfig: &datastore.FilterConfiguration{
			EventTypes: []string{"user.created", "user.updated"},
			Filter: datastore.FilterSchema{
				Headers:     datastore.M{"X-Company-ID": "123"},
				Body:        datastore.M{"event": "user"},
				RawHeaders:  datastore.M{"X-Company-ID": "123"},
				RawBody:     datastore.M{"event": "user"},
				IsFlattened: true,
			},
		},
		AlertConfig: &datastore.AlertConfiguration{
			Count:     10,
			Threshold: "1h",
		},
		RetryConfig: &datastore.RetryConfiguration{
			Type:       datastore.LinearStrategyProvider,
			Duration:   60,
			RetryCount: 3,
		},
		RateLimitConfig: &datastore.RateLimitConfiguration{
			Count:    100,
			Duration: 60,
		},
		DeliveryMode: datastore.AtLeastOnceDeliveryMode,
	}
}

// createTestCLISubscription creates a CLI subscription for testing
func createTestCLISubscription(project *datastore.Project, device *datastore.Device) *datastore.Subscription {
	return &datastore.Subscription{
		UID:       ulid.Make().String(),
		Name:      "Test CLI Subscription",
		Type:      datastore.SubscriptionTypeCLI,
		ProjectID: project.UID,
		DeviceID:  device.UID,
		FilterConfig: &datastore.FilterConfiguration{
			EventTypes: []string{"*"},
			Filter: datastore.FilterSchema{
				Headers:     datastore.M{},
				Body:        datastore.M{},
				RawHeaders:  datastore.M{},
				RawBody:     datastore.M{},
				IsFlattened: true,
			},
		},
		DeliveryMode: datastore.AtMostOnceDeliveryMode,
	}
}

// assertSubscriptionEqual verifies two subscriptions are equal
func assertSubscriptionEqual(t *testing.T, expected, actual *datastore.Subscription) {
	t.Helper()

	require.Equal(t, expected.UID, actual.UID)
	require.Equal(t, expected.Name, actual.Name)
	require.Equal(t, expected.Type, actual.Type)
	require.Equal(t, expected.ProjectID, actual.ProjectID)
	require.Equal(t, expected.EndpointID, actual.EndpointID)
	require.Equal(t, expected.SourceID, actual.SourceID)
	require.Equal(t, expected.DeviceID, actual.DeviceID)
	require.Equal(t, expected.DeliveryMode, actual.DeliveryMode)

	// Assert configs
	if expected.FilterConfig != nil {
		require.NotNil(t, actual.FilterConfig)
		require.ElementsMatch(t, expected.FilterConfig.EventTypes, actual.FilterConfig.EventTypes)
	}

	if expected.AlertConfig != nil {
		require.NotNil(t, actual.AlertConfig)
		require.Equal(t, expected.AlertConfig.Count, actual.AlertConfig.Count)
		require.Equal(t, expected.AlertConfig.Threshold, actual.AlertConfig.Threshold)
	}

	if expected.RetryConfig != nil {
		require.NotNil(t, actual.RetryConfig)
		require.Equal(t, expected.RetryConfig.Type, actual.RetryConfig.Type)
		require.Equal(t, expected.RetryConfig.Duration, actual.RetryConfig.Duration)
		require.Equal(t, expected.RetryConfig.RetryCount, actual.RetryConfig.RetryCount)
	}

	if expected.RateLimitConfig != nil {
		require.NotNil(t, actual.RateLimitConfig)
		require.Equal(t, expected.RateLimitConfig.Count, actual.RateLimitConfig.Count)
		require.Equal(t, expected.RateLimitConfig.Duration, actual.RateLimitConfig.Duration)
	}
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
