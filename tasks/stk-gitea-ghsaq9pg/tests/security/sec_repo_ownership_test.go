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

func TestSec_AttachmentAuthorizedAgainstOwningRepository(t *testing.T) {
	defer tests.PrepareTestEnv(t)()
	tests.PrepareAttachmentsStorage(t)

	// Fixture attachment 12 belongs to the private repository 2 (release 11).
	att := unittest.AssertExistsAndLoadBean(t, &repo_model.Attachment{ID: 12})
	require.EqualValues(t, 2, att.RepoID)
	base := att.DownloadCount

	urls := []string{
		"/user2/repo1/attachments/" + att.UUID,
		"/user2/repo1/releases/attachments/" + att.UUID,
	}

	anon := emptyTestSession(t)
	for _, url := range urls {
		resp := anon.MakeRequest(t, NewRequest(t, "GET", url), NoExpectedStatus)
		secRequireBlockedDownload(t, resp, secRepoTwoFile, att.ID, base)
	}

	reader := loginUser(t, "user8")
	for _, url := range urls {
		resp := reader.MakeRequest(t, NewRequest(t, "GET", url), NoExpectedStatus)
		secRequireBlockedDownload(t, resp, secRepoTwoFile, att.ID, base)
	}
}
