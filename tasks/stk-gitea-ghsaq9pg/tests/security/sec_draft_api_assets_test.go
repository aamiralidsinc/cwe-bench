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

func TestSec_DraftReleaseAssetsAPI(t *testing.T) {
	defer tests.PrepareTestEnv(t)()

	release := unittest.AssertExistsAndLoadBean(t, &repo_model.Release{ID: 4})
	require.True(t, release.IsDraft, "fixture release 4 must be a draft")
	att := secCreateReleaseAttachment(t, 1, release.ID, 2,
		"a0eebc99-9c0b-4ef8-bb6d-6bb9bd38e002", "draft-assets-sec.txt", secDraftMarker)

	listURL := fmt.Sprintf("/api/v1/repos/user2/repo1/releases/%d/assets", release.ID)
	getURL := fmt.Sprintf("/api/v1/repos/user2/repo1/releases/%d/assets/%d", release.ID, att.ID)

	resp := MakeRequest(t, NewRequest(t, "GET", listURL), NoExpectedStatus)
	secRequireClientError(t, resp, att.Name, att.UUID)

	resp = MakeRequest(t, NewRequest(t, "GET", getURL), NoExpectedStatus)
	secRequireClientError(t, resp, att.Name, att.UUID)

	readerToken := getUserToken(t, "user8", auth_model.AccessTokenScopeReadRepository)
	resp = MakeRequest(t, NewRequest(t, "GET", listURL).AddTokenAuth(readerToken), NoExpectedStatus)
	secRequireClientError(t, resp, att.Name, att.UUID)

	resp = MakeRequest(t, NewRequest(t, "GET", getURL).AddTokenAuth(readerToken), NoExpectedStatus)
	secRequireClientError(t, resp, att.Name, att.UUID)
}
