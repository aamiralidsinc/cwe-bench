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
)

func TestFunc_DraftReleaseVisibleToWriterAPI(t *testing.T) {
	defer tests.PrepareTestEnv(t)()

	release := unittest.AssertExistsAndLoadBean(t, &repo_model.Release{ID: 4})
	att := secCreateReleaseAttachment(t, 1, release.ID, 2,
		"a0eebc99-9c0b-4ef8-bb6d-6bb9bd38f003", "draft-api-func.txt", secDraftMarker)

	token := getUserToken(t, "user2", auth_model.AccessTokenScopeWriteRepository)

	releaseURL := fmt.Sprintf("/api/v1/repos/user2/repo1/releases/%d", release.ID)
	resp := MakeRequest(t, NewRequest(t, "GET", releaseURL).AddTokenAuth(token), NoExpectedStatus)
	secRequireServed(t, resp, release.Title)

	listURL := fmt.Sprintf("/api/v1/repos/user2/repo1/releases/%d/assets", release.ID)
	resp = MakeRequest(t, NewRequest(t, "GET", listURL).AddTokenAuth(token), NoExpectedStatus)
	secRequireServed(t, resp, att.Name)

	getURL := fmt.Sprintf("/api/v1/repos/user2/repo1/releases/%d/assets/%d", release.ID, att.ID)
	resp = MakeRequest(t, NewRequest(t, "GET", getURL).AddTokenAuth(token), NoExpectedStatus)
	secRequireServed(t, resp, att.Name)
}

func TestFunc_PublishedReleaseAssetsReadableAPI(t *testing.T) {
	defer tests.PrepareTestEnv(t)()

	release := unittest.AssertExistsAndLoadBean(t, &repo_model.Release{ID: 1})
	att := unittest.AssertExistsAndLoadBean(t, &repo_model.Attachment{ID: 9})

	releaseURL := fmt.Sprintf("/api/v1/repos/user2/repo1/releases/%d", release.ID)
	resp := MakeRequest(t, NewRequest(t, "GET", releaseURL), NoExpectedStatus)
	secRequireServed(t, resp, release.Title)

	listURL := fmt.Sprintf("/api/v1/repos/user2/repo1/releases/%d/assets", release.ID)
	resp = MakeRequest(t, NewRequest(t, "GET", listURL), NoExpectedStatus)
	secRequireServed(t, resp, att.Name)

	getURL := fmt.Sprintf("/api/v1/repos/user2/repo1/releases/%d/assets/%d", release.ID, att.ID)
	resp = MakeRequest(t, NewRequest(t, "GET", getURL), NoExpectedStatus)
	secRequireServed(t, resp, att.Name)
}
