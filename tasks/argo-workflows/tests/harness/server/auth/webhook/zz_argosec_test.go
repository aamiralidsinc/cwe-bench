package webhook

// Injected security/functional tests (webhook request-body resource limit).
// The unauthenticated webhook entry point buffers the whole request body before
// verifying any signature. An oversized body must be rejected rather than read
// in full, while a normal webhook request must still be processed.

import (
	"bytes"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	kubefake "k8s.io/client-go/kubernetes/fake"

	"github.com/argoproj/argo-workflows/v4/util/logging"
)

func zzWebhookKube() *kubefake.Clientset {
	return kubefake.NewSimpleClientset(
		&corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{Name: "argo-workflows-webhook-clients", Namespace: "my-ns"},
			Data: map[string][]byte{
				"bitbucket": []byte("type: bitbucket\nsecret: sh!"),
			},
		},
		&corev1.ServiceAccount{
			ObjectMeta: metav1.ObjectMeta{Name: "bitbucket", Namespace: "my-ns"},
			Secrets:    []corev1.ObjectReference{{Name: "bitbucket-token"}},
		},
		&corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{Name: "bitbucket-token", Namespace: "my-ns"},
			Data:       map[string][]byte{"token": []byte("my-bitbucket-token")},
		},
	)
}

func zzRunWebhook(t *testing.T, body string, headers map[string]string) *httptest.ResponseRecorder {
	t.Helper()
	ctx := logging.TestContext(t.Context())
	k := zzWebhookKube()
	mw := NewWebhookInterceptor(logging.RequireLoggerFromContext(ctx)).Interceptor(k)
	r := httptest.NewRequest("POST", "/api/v1/events/my-ns/my-disc", bytes.NewBufferString(body))
	r = r.WithContext(ctx)
	for key, v := range headers {
		r.Header.Set(key, v)
	}
	w := httptest.NewRecorder()
	mw(w, r, &zzNopHandler{})
	return w
}

type zzNopHandler struct{}

func (zzNopHandler) ServeHTTP(http.ResponseWriter, *http.Request) {}

// zzBigBody streams n bytes of 'a' without allocating them, and counts how many
// bytes the server actually read.
type zzBigBody struct{ n, read int64 }

func (b *zzBigBody) Read(p []byte) (int, error) {
	if b.read >= b.n {
		return 0, io.EOF
	}
	k := int64(len(p))
	if rem := b.n - b.read; k > rem {
		k = rem
	}
	for i := int64(0); i < k; i++ {
		p[i] = 'a'
	}
	b.read += k
	return int(k), nil
}

// Security: a body far larger than any legitimate webhook (GitHub's own cap is
// 25 MB) must be refused up front: any 4xx response, and the interceptor must
// not have read the body in full. The exact limit and status are the fix's choice.
func TestSecZZWebhookRejectsOversizedBody(t *testing.T) {
	const size = 128 * 1024 * 1024 // 128 MiB
	ctx := logging.TestContext(t.Context())
	k := zzWebhookKube()
	mw := NewWebhookInterceptor(logging.RequireLoggerFromContext(ctx)).Interceptor(k)
	body := &zzBigBody{n: size}
	r := httptest.NewRequest("POST", "/api/v1/events/my-ns/my-disc", body)
	r.ContentLength = size // as a real client sending this body declares it
	r = r.WithContext(ctx)
	w := httptest.NewRecorder()
	mw(w, r, &zzNopHandler{})
	if w.Code < 400 || w.Code > 499 {
		t.Fatalf("oversized webhook body was not refused: status=%d", w.Code)
	}
	if body.read >= size {
		t.Fatalf("oversized webhook body was read in full (%d bytes) before being refused", body.read)
	}
}

// Functional: a normally sized, correctly signed webhook request is processed
// and the matching service-account bearer token is attached.
func TestFuncZZWebhookNormalRequestProcessed(t *testing.T) {
	ctx := logging.TestContext(t.Context())
	k := zzWebhookKube()
	mw := NewWebhookInterceptor(logging.RequireLoggerFromContext(ctx)).Interceptor(k)
	r := httptest.NewRequest("POST", "/api/v1/events/my-ns/my-disc", bytes.NewBufferString("{}"))
	r = r.WithContext(ctx)
	r.Header.Set("X-Event-Key", "repo:push")
	r.Header.Set("X-Hook-UUID", "sh!")
	w := httptest.NewRecorder()
	mw(w, r, &zzNopHandler{})
	if w.Code == http.StatusForbidden {
		t.Fatalf("normal webhook request was rejected: status=%d", w.Code)
	}
	if got := r.Header["Authorization"]; len(got) != 1 || got[0] != "Bearer my-bitbucket-token" {
		t.Fatalf("expected bitbucket bearer token to be attached, got %v", got)
	}
}

// Functional: a normal small body that matches no webhook client is passed
// through to the next handler (not rejected).
func TestFuncZZWebhookSmallBodyPassedThrough(t *testing.T) {
	w := zzRunWebhook(t, "{}", nil)
	if w.Code == http.StatusForbidden {
		t.Fatalf("normal small webhook body was rejected: status=%d", w.Code)
	}
}
