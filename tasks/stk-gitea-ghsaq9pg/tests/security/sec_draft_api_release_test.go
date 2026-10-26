// Copyright 2026 The Gitea Authors. All rights reserved.
// SPDX-License-Identifier: MIT

package integration

import (
	"fmt"
	"testing"

	auth_model "code.gitea.io/gitea/models/auth"
	repo_model "code.gitea.io/gitea/models/repo"
	"code.gitea.io/gitea/models/unittest"
	"code.gitea.io/gitea/tests"

	"github.com/stretchr/testify/require"
)

func TestSec_DraftReleaseMetadataAPI(t *testing.T) {
	defer tests.PrepareTestEnv(t)()

	release := unittest.AssertExistsAndLoadBean(t, &repo_model.Release{ID: 4})
	require.True(t, release.IsDraft, "fixture release 4 must be a draft")
	urlStr := fmt.Sprintf("/api/v1/repos/user2/repo1/releases/%d", release.ID)

	resp := MakeRequest(t, NewRequest(t, "GET", urlStr), NoExpectedStatus)
	secRequireClientError(t, resp, release.Title, release.TagName)

	readerToken := getUserToken(t, "user8", auth_model.AccessTokenScopeReadRepository)
	resp = MakeRequest(t, NewRequest(t, "GET", urlStr).AddTokenAuth(readerToken), NoExpectedStatus)
	secRequireClientError(t, resp, release.Title, release.TagName)
}
