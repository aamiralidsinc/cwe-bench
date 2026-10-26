package hiddentests

import (
	"context"
	"strings"
	"testing"

	"github.com/stretchr/testify/require"

	"github.com/frain-dev/convoy/internal/sources"
)

func requireClientError(t *testing.T, code int, body string) {
	t.Helper()
	require.GreaterOrEqual(t, code, 400, "expected a client error, got %d: %s", code, body)
	require.Less(t, code, 500, "expected a client error, got %d: %s", code, body)
}

// A source in another project must not be readable through the project-scoped source endpoint.
func TestSecSourceGet_ForeignProjectDenied(t *testing.T) {
	f := newFixture(t, datastoreIncoming())
	code, body := f.getSource(f.projA.UID, f.srcB.UID)
	requireClientError(t, code, body)
	require.NotContains(t, body, secretB, "the foreign source and its credentials must not be returned")
}

// Changing a source through another project must be refused with no persisted effect.
func TestSecSourceUpdate_ForeignProjectDeniedNoChange(t *testing.T) {
	f := newFixture(t, datastoreIncoming())
	code, body := f.putSource(f.projA.UID, f.srcB.UID, jsonBody("name", "cross-project-rename-marker", "type", "http"))
	requireClientError(t, code, body)
	require.NotContains(t, body, secretB)

	projectID, name, secret := f.sourceRow(f.srcB.UID)
	require.Equal(t, f.projB.UID, projectID, "the foreign source must stay in its own project")
	require.NotEqual(t, "cross-project-rename-marker", name, "the foreign source must not be renamed")
	require.Equal(t, secretB, secret, "the foreign source credentials must not be changed")
}

// The project-scoped lookup API must not return another project's source or credentials.
func TestSecSourceLookup_ForeignProjectDenied(t *testing.T) {
	f := newFixture(t, datastoreIncoming())
	got, err := sources.New(f.logger, f.db).FindSourceByID(context.Background(), f.projA.UID, f.srcB.UID)
	require.Error(t, err)
	require.Nil(t, got)
}

// An incoming subscription must not be created against another project's source.
func TestSecSubscriptionCreate_IncomingForeignSourceDenied(t *testing.T) {
	f := newFixture(t, datastoreIncoming())
	code, body := f.createSubscription(f.projA.UID, jsonBody(
		"name", "incoming-foreign-source-marker", "endpoint_id", f.epA.UID, "source_id", f.srcB.UID))
	requireClientError(t, code, body)
	require.Equal(t, 0, f.subscriptionsBySource(f.projA.UID, f.srcB.UID))
}

var _ = strings.Contains
