package hiddentests

import (
	"context"
	"strings"
	"testing"

	"github.com/stretchr/testify/require"

	"github.com/frain-dev/convoy/datastore"
	"github.com/frain-dev/convoy/internal/sources"
)

func requireClientError(t *testing.T, code int, body string) {
	t.Helper()
	require.GreaterOrEqual(t, code, 400, "expected a client error, got %d: %s", code, body)
	require.Less(t, code, 500, "expected a client error, got %d: %s", code, body)
}

// A source in another project must not be readable through the project-scoped source endpoint.
func TestSecSourceGet_ForeignProjectDenied(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	code, body := f.getSource(f.projA.UID, f.srcB.UID)
	requireClientError(t, code, body)
	require.NotContains(t, body, secretB, "the foreign source and its verifier must not be returned")
}

// Changing a source through another project must be refused with no persisted effect.
func TestSecSourceUpdate_ForeignProjectDeniedNoChange(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	code, body := f.putSource(f.projA.UID, f.srcB.UID, jsonBody("name", "cross-project-rename-marker", "type", "http"))
	requireClientError(t, code, body)
	require.NotContains(t, body, secretB)

	projectID, name, secret := f.sourceRow(f.srcB.UID)
	require.Equal(t, f.projB.UID, projectID, "the foreign source must stay in its own project")
	require.NotEqual(t, "cross-project-rename-marker", name, "the foreign source must not be renamed")
	require.Equal(t, secretB, secret, "the foreign source verifier must not be changed")
}

// The project-scoped lookup API must not return another project's source or verifier.
func TestSecSourceLookup_ForeignProjectDenied(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	got, err := sources.New(f.logger, f.db).FindSourceByID(context.Background(), f.projA.UID, f.srcB.UID)
	require.Error(t, err)
	require.Nil(t, got)
}

// The write API must not move or overwrite a source that belongs to another project.
func TestSecSourceWrite_ForeignProjectDeniedNoChange(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	foreign := *f.srcB
	foreign.Name = "service-write-marker"
	foreign.Verifier = &datastore.VerifierConfig{Type: datastore.HMacVerifier, HMac: &datastore.HMac{
		Header: "X-Signature", Hash: "SHA256", Secret: "attacker-verifier-marker", Encoding: datastore.Base64Encoding,
	}}
	err := sources.New(f.logger, f.db).UpdateSource(context.Background(), f.projA.UID, &foreign)
	require.Error(t, err)

	projectID, name, secret := f.sourceRow(f.srcB.UID)
	require.Equal(t, f.projB.UID, projectID, "the foreign source must not move between projects")
	require.NotEqual(t, "service-write-marker", name)
	require.Equal(t, secretB, secret)
}

// An incoming subscription must not be created against another project's source.
func TestSecSubscriptionCreate_IncomingForeignSourceDenied(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	code, body := f.createSubscription(f.projA.UID, jsonBody(
		"name", "incoming-foreign-source-marker", "endpoint_id", f.epA.UID, "source_id", f.srcB.UID))
	requireClientError(t, code, body)
	require.Equal(t, 0, f.subscriptionsBySource(f.projA.UID, f.srcB.UID))
}

// An outgoing subscription must not store a reference to another project's source.
func TestSecSubscriptionCreate_OutgoingForeignSourceDenied(t *testing.T) {
	f := newFixture(t, datastore.OutgoingProject)
	code, body := f.createSubscription(f.projA.UID, jsonBody(
		"name", "outgoing-foreign-source-marker", "endpoint_id", f.epA.UID, "source_id", f.srcB.UID))
	requireClientError(t, code, body)
	require.Equal(t, 0, f.subscriptionsBySource(f.projA.UID, f.srcB.UID))
}

// Updating only the source of an existing subscription must not attach another project's source.
func TestSecSubscriptionUpdate_ForeignSourceDeniedNoChange(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	code, body := f.createSubscription(f.projA.UID, jsonBody(
		"name", "own-sub-marker", "endpoint_id", f.epA.UID, "source_id", f.srcA.UID))
	require.Equal(t, 201, code, body)
	created := f.lastSubscription()
	require.Equal(t, f.srcA.UID, created.SourceID)

	code, body = f.updateSubscription(f.projA.UID, created.UID, jsonBody("source_id", f.srcB.UID))
	requireClientError(t, code, body)

	_, sourceID := f.subscriptionRow(created.UID)
	require.Equal(t, f.srcA.UID, sourceID, "the subscription must keep its own project's source")
}

// Reading one project's subscription must not surface another project's source record or verifier.
func TestSecSubscriptionGet_ForeignSourceMetadataSuppressed(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	sub := f.seedSubscription(f.projA.UID, f.srcB.UID, f.epA.UID)

	code, body := f.getSubscription(f.projA.UID, sub.UID)
	require.NotContains(t, body, secretB, "another project's source verifier must not be rendered")
	if code == 200 {
		require.NotContains(t, body, f.srcB.UID)
	}
}

// Listing subscriptions must not surface another project's source record or verifier.
func TestSecSubscriptionList_ForeignSourceMetadataSuppressed(t *testing.T) {
	f := newFixture(t, datastore.IncomingProject)
	f.seedSubscription(f.projA.UID, f.srcB.UID, f.epA.UID)

	code, body := f.listSubscriptions(f.projA.UID)
	require.Equal(t, 200, code, body)
	require.NotContains(t, body, secretB, "another project's source verifier must not be rendered")
}

// lastSubscription returns the most recently created subscription in project A.
func (f *fixture) lastSubscription() *datastore.Subscription {
	f.t.Helper()
	var sub datastore.Subscription
	err := f.db.GetConn().QueryRow(context.Background(),
		`SELECT id, project_id, COALESCE(source_id, ''), COALESCE(endpoint_id, '')
		 FROM convoy.subscriptions WHERE project_id = $1 AND deleted_at IS NULL
		 ORDER BY created_at DESC LIMIT 1`, f.projA.UID).
		Scan(&sub.UID, &sub.ProjectID, &sub.SourceID, &sub.EndpointID)
	require.NoError(f.t, err)
	return &sub
}

var _ = strings.Contains
