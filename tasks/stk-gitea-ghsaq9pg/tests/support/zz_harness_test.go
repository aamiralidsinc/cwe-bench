// Copyright 2026 The Gitea Authors. All rights reserved.
// SPDX-License-Identifier: MIT

package integration

import (
	"net/http/httptest"
	"strings"
	"testing"

	"code.gitea.io/gitea/models/db"
	repo_model "code.gitea.io/gitea/models/repo"
	"code.gitea.io/gitea/models/unittest"
	"code.gitea.io/gitea/modules/storage"

	"github.com/stretchr/testify/require"
)

// Shared fixtures for the hidden suites. The tests drive the product through its
// HTTP entry points; records they need to exist are created here directly.

const (
	secDraftMarker  = "SEC_DRAFT_ATTACHMENT_MARKER_7f3a"
	secLegacyMarker = "SEC_LEGACY_ATTACHMENT_MARKER_91c2"
	secRepoTwoFile  = "This is a release README"
)

// secCreateReleaseAttachment stores a release-linked attachment record and its bytes.
func secCreateReleaseAttachment(t *testing.T, repoID, releaseID, uploaderID int64, uuid, name, content string) *repo_model.Attachment {
	t.Helper()
	att := &repo_model.Attachment{
		UUID:       uuid,
		RepoID:     repoID,
		ReleaseID:  releaseID,
		UploaderID: uploaderID,
		Name:       name,
	}
	require.NoError(t, db.Insert(t.Context(), att))
	_, err := storage.Attachments.Save(repo_model.AttachmentRelativePath(uuid), strings.NewReader(content), -1)
	require.NoError(t, err)
	return att
}

// secStoreFile writes bytes for an attachment that already exists in the fixtures.
func secStoreFile(t *testing.T, uuid, content string) {
	t.Helper()
	_, err := storage.Attachments.Save(repo_model.AttachmentRelativePath(uuid), strings.NewReader(content), -1)
	require.NoError(t, err)
}

// secRequireBlockedDownload asserts a download was refused with a client error, returned
// no file bytes and changed no state.
func secRequireBlockedDownload(t *testing.T, resp *httptest.ResponseRecorder, marker string, attachmentID, wantCount int64) {
	t.Helper()
	if resp.Code < 400 || resp.Code >= 500 {
		t.Fatalf("a refused download must answer with a client error, got %d", resp.Code)
	}
	if strings.Contains(resp.Body.String(), marker) {
		t.Fatalf("a refused download returned the file content")
	}
	att := unittest.AssertExistsAndLoadBean(t, &repo_model.Attachment{ID: attachmentID})
	if att.DownloadCount != wantCount {
		t.Fatalf("a refused download changed the download counter: got %d, want %d", att.DownloadCount, wantCount)
	}
}

// secRequireClientError asserts a metadata request was refused with a client error and
// that the response carried none of the protected values.
func secRequireClientError(t *testing.T, resp *httptest.ResponseRecorder, forbidden ...string) {
	t.Helper()
	if resp.Code < 400 || resp.Code >= 500 {
		t.Fatalf("a refused request must answer with a client error, got %d", resp.Code)
	}
	body := resp.Body.String()
	for _, value := range forbidden {
		if value != "" && strings.Contains(body, value) {
			t.Fatalf("a refused response carried protected data (%q)", value)
		}
	}
}

// secRequireServed asserts a download was served.
func secRequireServed(t *testing.T, resp *httptest.ResponseRecorder, marker string) {
	t.Helper()
	if resp.Code != 200 {
		t.Fatalf("a legitimate download must be served, got %d", resp.Code)
	}
	if marker != "" && !strings.Contains(resp.Body.String(), marker) {
		t.Fatalf("a legitimate download did not return the file content")
	}
}
