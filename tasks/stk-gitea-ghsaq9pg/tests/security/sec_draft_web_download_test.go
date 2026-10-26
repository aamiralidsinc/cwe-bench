// Copyright 2026 The Gitea Authors. All rights reserved.
// SPDX-License-Identifier: MIT

package integration

import (
	"testing"

	repo_model "code.gitea.io/gitea/models/repo"
	"code.gitea.io/gitea/models/unittest"
	"code.gitea.io/gitea/tests"

	"github.com/stretchr/testify/require"
)

func TestSec_DraftReleaseAttachmentWebDownload(t *testing.T) {
	defer tests.PrepareTestEnv(t)()

	release := unittest.AssertExistsAndLoadBean(t, &repo_model.Release{ID: 4})
	require.True(t, release.IsDraft, "fixture release 4 must be a draft")
	att := secCreateReleaseAttachment(t, 1, release.ID, 2,
		"a0eebc99-9c0b-4ef8-bb6d-6bb9bd38e001", "draft-web-sec.txt", secDraftMarker)

	urls := []struct {
		name string
		url  string
	}{
		{"global", "/attachments/" + att.UUID},
		{"repository", "/user2/repo1/attachments/" + att.UUID},
		{"repository_release", "/user2/repo1/releases/attachments/" + att.UUID},
	}

	anon := emptyTestSession(t)
	for _, c := range urls {
		t.Run("anonymous_"+c.name, func(t *testing.T) {
			resp := anon.MakeRequest(t, NewRequest(t, "GET", c.url), NoExpectedStatus)
			secRequireBlockedDownload(t, resp, secDraftMarker, att.ID, 0)
		})
	}

	reader := loginUser(t, "user8")
	for _, c := range urls {
		t.Run("reader_"+c.name, func(t *testing.T) {
			resp := reader.MakeRequest(t, NewRequest(t, "GET", c.url), NoExpectedStatus)
			secRequireBlockedDownload(t, resp, secDraftMarker, att.ID, 0)
		})
	}
}
