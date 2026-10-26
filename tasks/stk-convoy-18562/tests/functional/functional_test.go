package hiddentests

import (
	"context"
	"testing"

	"github.com/stretchr/testify/require"

	"github.com/frain-dev/convoy/datastore"
	"github.com/frain-dev/convoy/internal/sources"
)

// Reading a source through its own project keeps working and still returns its verifier.
func TestFuncSourceGet_OwnProject(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	code, body := f.getSource(f.projA.UID, f.srcA.UID)
	require.Equal(t, 200, code, body)
	require.Contains(t, body, secretA)
	require.Contains(t, body, f.srcA.UID)
}

// Updating a source in its own project keeps working and persists the change.
func TestFuncSourceUpdate_OwnProject(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	code, body := f.putSource(f.projA.UID, f.srcA.UID, jsonBody("name", "own-source-renamed", "type", "http"))
	require.Equal(t, 202, code, body)
	projectID, name, secret := f.sourceRow(f.srcA.UID)
	require.Equal(t, f.projA.UID, projectID)
	require.Equal(t, "own-source-renamed", name)
	require.Equal(t, secretA, secret, "an update without a verifier keeps the stored verifier")
}

// Deleting through another project is refused and changes nothing; deleting in the owning project works.
func TestFuncSourceDelete_ForeignRefusedOwnDeleted(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	code, body := f.deleteSource(f.projA.UID, f.srcB.UID)
	requireClientError(t, code, body)
	require.True(t, f.sourceExists(f.srcB.UID), "a refused delete must not remove the source")

	code, body = f.deleteSource(f.projA.UID, f.srcA.UID)
	require.Equal(t, 200, code, body)
	require.False(t, f.sourceExists(f.srcA.UID))
}

// The public ingestion lookup by mask id stays project-agnostic and returns the verifier.
func TestFuncSourceMaskLookup_ProjectAgnostic(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	svc := sources.New(f.logger, f.db)
	for _, src := range []*datastore.Source{f.srcA, f.srcB} {
		got, err := svc.FindSourceByMaskID(context.Background(), src.MaskID)
		require.NoError(t, err, "a source must resolve by its mask id regardless of project")
		require.Equal(t, src.UID, got.UID)
		require.Equal(t, src.ProjectID, got.ProjectID)
		require.NotNil(t, got.Verifier)
		require.NotEmpty(t, got.Verifier.HMac.Secret)
	}
}

// The project-scoped lookup still finds a source in the caller's own project.
func TestFuncSourceLookup_OwnProject(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	got, err := sources.New(f.logger, f.db).FindSourceByID(context.Background(), f.projA.UID, f.srcA.UID)
	require.NoError(t, err)
	require.Equal(t, f.srcA.UID, got.UID)
}

// An outgoing subscription may still name a source that belongs to its project.
func TestFuncSubscriptionCreate_OutgoingOwnSourceAccepted(t *testing.T) {
	f := newFixture(t, datastore.OutgoingProject)
	code, body := f.createSubscription(f.projA.UID, jsonBody(
		"name", "outgoing-own-source", "endpoint_id", f.epA.UID, "source_id", f.srcA.UID))
	require.Equal(t, 201, code, body)
	require.Equal(t, 1, f.subscriptionsBySource(f.projA.UID, f.srcA.UID))
}

// Updating only the source of a subscription to another source in the same project keeps working.
func TestFuncSubscriptionUpdate_OwnSourceAccepted(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	other := addSource(t, f.db, f.logger, f.projA, "source-a2", "SECOND-OWN-VERIFIER-MARKER")
	code, body := f.createSubscription(f.projA.UID, jsonBody(
		"name", "own-source-update", "endpoint_id", f.epA.UID, "source_id", f.srcA.UID))
	require.Equal(t, 201, code, body)
	created := f.lastSubscription()

	code, body = f.updateSubscription(f.projA.UID, created.UID, jsonBody("source_id", other.UID))
	require.Equal(t, 202, code, body)
	_, sourceID := f.subscriptionRow(created.UID)
	require.Equal(t, other.UID, sourceID)
}

// A subscription in the same project still renders its source metadata, including the verifier.
func TestFuncSubscriptionRead_SameProjectSourceRendered(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	sub := f.seedSubscription(f.projA.UID, f.srcA.UID, f.epA.UID)
	code, body := f.getSubscription(f.projA.UID, sub.UID)
	require.Equal(t, 200, code, body)
	require.Contains(t, body, secretA)
	require.Contains(t, body, f.srcA.UID)
}

// A subscription with no source still renders with empty source metadata.
func TestFuncSubscriptionRead_NoSourceRendered(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	sub := f.seedSubscription(f.projA.UID, "", f.epA.UID)
	code, body := f.getSubscription(f.projA.UID, sub.UID)
	require.Equal(t, 200, code, body)
	require.Contains(t, body, `"source_metadata":null`)
}
