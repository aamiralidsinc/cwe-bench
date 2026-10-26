// Copyright 2026 The Gitea Authors. All rights reserved.
// SPDX-License-Identifier: MIT

package integration

import (
	"testing"

	"code.gitea.io/gitea/models/db"
	repo_model "code.gitea.io/gitea/models/repo"
	"code.gitea.io/gitea/models/unittest"
	"code.gitea.io/gitea/tests"

	"github.com/stretchr/testify/require"
)

func TestFunc_PublishedReleaseAssetStaysReadable(t *testing.T) {
	defer tests.PrepareTestEnv(t)()
	tests.PrepareAttachmentsStorage(t)

	att := unittest.AssertExistsAndLoadBean(t, &repo_model.Attachment{ID: 9})
	secStoreFile(t, att.UUID, "PUBLISHED_RELEASE_MARKER_5d10")

	anon := emptyTestSession(t)
	for _, url := range []string{
		"/attachments/" + att.UUID,
		"/user2/repo1/attachments/" + att.UUID,
		"/user2/repo1/releases/attachments/" + att.UUID,
	} {
		resp := anon.MakeRequest(t, NewRequest(t, "GET", url), NoExpectedStatus)
		secRequireServed(t, resp, "PUBLISHED_RELEASE_MARKER_5d10")
	}

	for _, url := range []string{
		"/user2/repo1/releases/download/v1.1/attach1",
		"/user2/repo1/releases/download/latest/attach1",
	} {
		resp := anon.MakeRequest(t, NewRequest(t, "GET", url), NoExpectedStatus)
		secRequireServed(t, resp, "PUBLISHED_RELEASE_MARKER_5d10")
	}
}

func TestFunc_DraftAssetStaysDownloadableByWriter(t *testing.T) {
	defer tests.PrepareTestEnv(t)()

	release := unittest.AssertExistsAndLoadBean(t, &repo_model.Release{ID: 4})
	att := secCreateReleaseAttachment(t, 1, release.ID, 2,
		"a0eebc99-9c0b-4ef8-bb6d-6bb9bd38f001", "draft-func.txt", secDraftMarker)

	owner := loginUser(t, "user2")
	for _, url := range []string{
		"/attachments/" + att.UUID,
		"/user2/repo1/attachments/" + att.UUID,
		"/user2/repo1/releases/attachments/" + att.UUID,
	} {
		resp := owner.MakeRequest(t, NewRequest(t, "GET", url), NoExpectedStatus)
		secRequireServed(t, resp, secDraftMarker)
	}
}

func TestFunc_UnlinkedAttachmentStaysWithUploader(t *testing.T) {
	defer tests.PrepareTestEnv(t)()

	att := unittest.AssertExistsAndLoadBean(t, &repo_model.Attachment{ID: 10})
	secStoreFile(t, att.UUID, "UNLINKED_MARKER_2b7e")

	uploader := loginUser(t, "user8")
	for _, url := range []string{
		"/attachments/" + att.UUID,
		"/user2/repo1/attachments/" + att.UUID,
	} {
		resp := uploader.MakeRequest(t, NewRequest(t, "GET", url), NoExpectedStatus)
		secRequireServed(t, resp, "UNLINKED_MARKER_2b7e")
	}

	other := loginUser(t, "user5")
	resp := other.MakeRequest(t, NewRequest(t, "GET", "/attachments/"+att.UUID), NoExpectedStatus)
	if resp.Code < 400 || resp.Code >= 500 {
		t.Fatalf("an unlinked attachment must stay private to its uploader, got %d", resp.Code)
	}
}

func TestFunc_LegacyAttachmentStaysInOwningRepository(t *testing.T) {
	defer tests.PrepareTestEnv(t)()

	release := unittest.AssertExistsAndLoadBean(t, &repo_model.Release{ID: 1})
	att := &repo_model.Attachment{
		UUID:       "a0eebc99-9c0b-4ef8-bb6d-6bb9bd38f002",
		RepoID:     0, // older records did not record the owning repository
		ReleaseID:  release.ID,
		UploaderID: 2,
		Name:       "legacy-func.txt",
	}
	require.NoError(t, db.Insert(t.Context(), att))
	_, err := db.GetEngine(t.Context()).Exec("UPDATE attachment SET created_unix=? WHERE id=?", 946684800, att.ID)
	require.NoError(t, err)
	secStoreFile(t, att.UUID, secLegacyMarker)

	anon := emptyTestSession(t)
	for _, url := range []string{
		"/attachments/" + att.UUID,
		"/user2/repo1/attachments/" + att.UUID,
		"/user2/repo1/releases/attachments/" + att.UUID,
	} {
		resp := anon.MakeRequest(t, NewRequest(t, "GET", url), NoExpectedStatus)
		secRequireServed(t, resp, secLegacyMarker)
	}
}
