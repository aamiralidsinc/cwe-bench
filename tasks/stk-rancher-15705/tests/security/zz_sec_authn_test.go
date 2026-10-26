package requests

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	apiv3 "github.com/rancher/rancher/pkg/apis/management.cattle.io/v3"
	"github.com/rancher/rancher/pkg/auth/providers"
	"github.com/rancher/rancher/pkg/auth/providers/common"
	"github.com/rancher/rancher/pkg/clusterrouter"
	mgmtFakes "github.com/rancher/rancher/pkg/generated/norman/management.cattle.io/v3/fakes"
	"github.com/rancher/wrangler/v3/pkg/generic/fake"
	"go.uber.org/mock/gomock"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	k8stypes "k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/tools/cache"
)

type zzAuthProvider struct {
	common.AuthProvider
	name string
}

func (p *zzAuthProvider) GetName() string                   { return p.name }
func (p *zzAuthProvider) IsDisabledProvider() (bool, error) { return false, nil }
func (p *zzAuthProvider) GetUserExtraAttributes(pr apiv3.Principal) map[string][]string {
	return map[string][]string{
		common.UserAttributePrincipalID: {pr.Name},
		common.UserAttributeUserName:    {pr.LoginName},
	}
}

type zzAuthFixture struct {
	auth *tokenAuthenticator
}

// zzNewAuthFixture builds the real request authenticator with a token cache that contains
// the supplied token. It returns the authenticator; the request carries the token.
func zzNewAuthFixture(t *testing.T, token *apiv3.Token, user *apiv3.User, attribs *apiv3.UserAttribute) *zzAuthFixture {
	t.Helper()
	prevProviders := providers.Providers
	t.Cleanup(func() { providers.Providers = prevProviders })
	providers.Providers = map[string]common.AuthProvider{"githubapp": &zzAuthProvider{name: "githubapp"}}

	indexer := cache.NewIndexer(cache.MetaNamespaceKeyFunc, cache.Indexers{cache.NamespaceIndex: cache.MetaNamespaceIndexFunc})
	if err := indexer.AddIndexers(cache.Indexers{tokenKeyIndex: tokenKeyIndexer}); err != nil {
		t.Fatalf("adding indexer: %v", err)
	}
	if err := indexer.Add(token); err != nil {
		t.Fatalf("indexing token: %v", err)
	}

	ctrl := gomock.NewController(t)
	tokenClient := fake.NewMockNonNamespacedClientInterface[*apiv3.Token, *apiv3.TokenList](ctrl)
	tokenClient.EXPECT().Get(token.Name, metav1.GetOptions{}).Return(token, nil).AnyTimes()
	tokenClient.EXPECT().Patch(token.Name, k8stypes.JSONPatchType, gomock.Any()).Return(nil, nil).AnyTimes()

	a := &tokenAuthenticator{
		ctx:          context.Background(),
		tokenIndexer: indexer,
		tokenClient:  tokenClient,
		userAttributeLister: &mgmtFakes.UserAttributeListerMock{
			GetFunc: func(_, _ string) (*apiv3.UserAttribute, error) {
				return attribs, nil
			},
		},
		userLister: &mgmtFakes.UserListerMock{
			GetFunc: func(_, _ string) (*apiv3.User, error) { return user, nil },
		},
		clusterRouter: clusterrouter.GetClusterID,
		refreshUser:   func(string, bool) {},
		now:           time.Now,
	}
	return &zzAuthFixture{auth: a}
}

func zzAuthToken(name, provider string, groups []apiv3.Principal) *apiv3.Token {
	return &apiv3.Token{
		ObjectMeta:   metav1.ObjectMeta{Name: name, CreationTimestamp: metav1.NewTime(time.Now())},
		Token:        "jnb9tksmnctvgbn92ngbkptblcjwg4pmfp98wqj29wk5kv85ktg59s",
		AuthProvider: provider,
		TTLMillis:    57600000,
		UserID:       "u-abcdef",
		UserPrincipal: apiv3.Principal{
			ObjectMeta:    metav1.ObjectMeta{Name: "githubapp_user://12345"},
			Me:            true,
			PrincipalType: "user",
			Provider:      "githubapp",
			LoginName:     "test-user",
		},
		GroupPrincipals: groups,
	}
}

func zzAuthUser() *apiv3.User {
	return &apiv3.User{
		ObjectMeta:   metav1.ObjectMeta{Name: "u-abcdef"},
		Username:     "test-user",
		PrincipalIDs: []string{"githubapp_user://12345"},
	}
}

func zzAuthAttribs(groups map[string]apiv3.Principals) *apiv3.UserAttribute {
	return &apiv3.UserAttribute{
		ObjectMeta:      metav1.ObjectMeta{Name: "u-abcdef"},
		GroupPrincipals: groups,
		ExtraByProvider: map[string]map[string][]string{
			"githubapp": {
				common.UserAttributePrincipalID: {"githubapp_user://12345"},
				common.UserAttributeUserName:    {"test-user"},
			},
		},
	}
}

func zzAuthenticate(t *testing.T, f *zzAuthFixture, token *apiv3.Token) *AuthenticatorResponse {
	t.Helper()
	req := httptest.NewRequest(http.MethodGet, "/v1/namespaces", nil)
	req.Header.Set("Authorization", "Bearer "+token.Name+":"+token.Token)
	resp, err := f.auth.Authenticate(req)
	if err != nil {
		t.Fatalf("authenticate: %v", err)
	}
	if resp == nil {
		t.Fatal("authenticate returned no response")
	}
	return resp
}

// When the current membership data has no entry for the token's provider, a group
// principal persisted on the token must not grant access.
func TestSec_TokenFallbackDoesNotGrantStaleTeams(t *testing.T) {
	stale := apiv3.Principal{
		ObjectMeta:    metav1.ObjectMeta{Name: "githubapp_team://45678"},
		LoginName:     "admin-team",
		Provider:      "githubapp",
		PrincipalType: "group",
	}
	token := zzAuthToken("token-stale", "githubapp", []apiv3.Principal{stale})
	f := zzNewAuthFixture(t, token, zzAuthUser(), zzAuthAttribs(map[string]apiv3.Principals{}))
	resp := zzAuthenticate(t, f, token)

	for _, g := range resp.Groups {
		if g == stale.Name {
			t.Fatalf("access was granted from a team membership the provider does not confirm")
		}
	}
}
