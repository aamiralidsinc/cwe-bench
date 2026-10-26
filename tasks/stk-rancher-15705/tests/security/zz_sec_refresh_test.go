package providerrefresh

import (
	"fmt"
	"testing"

	apiv3 "github.com/rancher/rancher/pkg/apis/management.cattle.io/v3"
	"github.com/rancher/rancher/pkg/auth/accessor"
	"github.com/rancher/rancher/pkg/auth/providers"
	"github.com/rancher/rancher/pkg/auth/providers/common"
	"github.com/rancher/rancher/pkg/auth/tokens"
	exttokens "github.com/rancher/rancher/pkg/ext/stores/tokens"
	"github.com/rancher/rancher/pkg/generated/norman/management.cattle.io/v3/fakes"
	"github.com/rancher/wrangler/v3/pkg/generic/fake"
	"go.uber.org/mock/gomock"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
)

type zzRefreshProvider struct {
	common.AuthProvider
	groups []apiv3.Principal
	err    error
}

func (p *zzRefreshProvider) IsDisabledProvider() (bool, error) { return false, nil }

func (p *zzRefreshProvider) RefetchGroupPrincipals(string, string) ([]apiv3.Principal, error) {
	return p.groups, p.err
}

func (p *zzRefreshProvider) CanAccessWithGroupProviders(string, []apiv3.Principal) (bool, error) {
	return true, nil
}

func (p *zzRefreshProvider) GetPrincipal(principalID string, _ accessor.TokenAccessor) (apiv3.Principal, error) {
	return apiv3.Principal{
		ObjectMeta: metav1.ObjectMeta{Name: principalID},
		Provider:   "githubapp",
		LoginName:  "test-user",
	}, nil
}

func (p *zzRefreshProvider) GetUserExtraAttributes(apiv3.Principal) map[string][]string { return nil }

func zzStalePrincipal() apiv3.Principal {
	return apiv3.Principal{
		ObjectMeta:    metav1.ObjectMeta{Name: "githubapp_team://45678"},
		LoginName:     "admin-team",
		Provider:      "githubapp",
		PrincipalType: "group",
	}
}

// zzRefreshFixture builds the refresher and the stored user attribute.
func zzRefreshFixture(t *testing.T, p common.AuthProvider) (*refresher, *apiv3.UserAttribute, *bool) {
	t.Helper()
	const providerName = "githubapp"
	prevNames, prevProv := providers.ProviderNames, providers.Providers
	t.Cleanup(func() {
		providers.ProviderNames, providers.Providers = prevNames, prevProv
	})
	providers.ProviderNames = map[string]bool{providerName: true}
	providers.Providers = map[string]common.AuthProvider{providerName: p}

	user := &apiv3.User{
		ObjectMeta:   metav1.ObjectMeta{Name: "user-abcde"},
		PrincipalIDs: []string{"githubapp_user://12345"},
	}
	attribs := &apiv3.UserAttribute{
		ObjectMeta: metav1.ObjectMeta{Name: "user-abcde"},
		GroupPrincipals: map[string]apiv3.Principals{
			providerName: {Items: []apiv3.Principal{zzStalePrincipal()}},
		},
		ExtraByProvider: map[string]map[string][]string{},
	}
	loginToken := &apiv3.Token{
		UserID:       "user-abcde",
		IsDerived:    false,
		AuthProvider: providerName,
		UserPrincipal: apiv3.Principal{
			ObjectMeta: metav1.ObjectMeta{Name: "githubapp_user://12345"},
			Provider:   providerName,
		},
	}

	ctrl := gomock.NewController(t)
	secrets := fake.NewMockControllerInterface[*corev1.Secret, *corev1.SecretList](ctrl)
	scache := fake.NewMockCacheInterface[*corev1.Secret](ctrl)
	users := fake.NewMockNonNamespacedControllerInterface[*apiv3.User, *apiv3.UserList](ctrl)
	users.EXPECT().Cache().Return(nil).AnyTimes()
	secrets.EXPECT().Cache().Return(scache).AnyTimes()
	scache.EXPECT().List("cattle-tokens", gomock.Any()).Return([]*corev1.Secret{}, nil).AnyTimes()
	tokenClient := fake.NewMockNonNamespacedClientInterface[*apiv3.Token, *apiv3.TokenList](ctrl)

	deleteCalled := false
	r := &refresher{
		tokenLister: &fakes.TokenListerMock{
			ListFunc: func(_ string, _ labels.Selector) ([]*apiv3.Token, error) {
				return []*apiv3.Token{loginToken}, nil
			},
		},
		userLister: &fakes.UserListerMock{
			GetFunc: func(_, _ string) (*apiv3.User, error) { return user, nil },
		},
		tokens: &fakes.TokenInterfaceMock{
			DeleteFunc: func(_ string, _ *metav1.DeleteOptions) error {
				deleteCalled = true
				return nil
			},
		},
		tokenMGR: tokens.NewMockedManager(tokenClient),
		extTokenStore: exttokens.NewSystem(nil, nil, secrets, users, nil, nil,
			exttokens.NewTimeHandler(),
			exttokens.NewHashHandler(),
			exttokens.NewAuthHandler()),
	}
	return r, attribs, &deleteCalled
}

// A refresh that cannot confirm the user's current memberships must not leave the
// previously stored (possibly over-inclusive) principals in force.
func TestSec_FailedRefreshDropsStaleTeams(t *testing.T) {
	r, attribs, _ := zzRefreshFixture(t, &zzRefreshProvider{err: fmt.Errorf("connection refused")})
	got, err := r.refreshAttributes(attribs)
	if err != nil {
		t.Fatalf("a transient provider error must not fail the refresh: %v", err)
	}
	if got == nil {
		t.Fatal("refresh returned no attribute")
	}
	if items := got.GroupPrincipals["githubapp"].Items; len(items) != 0 {
		t.Fatalf("a failed refresh left %d previously stored group principals in force: %+v", len(items), items)
	}
}
