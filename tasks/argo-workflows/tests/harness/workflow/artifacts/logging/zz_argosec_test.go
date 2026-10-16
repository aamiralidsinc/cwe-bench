package logging

// Injected security/functional tests (artifact-driver credential exposure).
// The artifact logging wrapper must not emit the wrapped driver's configuration
// (which carries repository credentials) into the log stream. It must still
// delegate every operation to the wrapped driver.

import (
	"bytes"
	"context"
	"io"
	"strings"
	"testing"

	wfv1 "github.com/argoproj/argo-workflows/v4/pkg/apis/workflow/v1alpha1"
	ulog "github.com/argoproj/argo-workflows/v4/util/logging"
)

// zzSecret is a distinctive credential value that must never reach the logs.
const zzSecret = "SUPERSECRETcred12345"

// zzLeakyDriver is a fake artifact driver carrying a secret in an exported
// field (as the real S3/HTTP/OSS drivers carry access keys and passwords).
type zzLeakyDriver struct {
	Endpoint  string
	AccessKey string
	SecretKey string // credential: must not be logged
	calls     map[string]bool
}

func zzNewLeakyDriver() *zzLeakyDriver {
	return &zzLeakyDriver{
		Endpoint:  "https://objectstore.example.com",
		AccessKey: "AKIAEXAMPLE",
		SecretKey: zzSecret,
		calls:     map[string]bool{},
	}
}

func (d *zzLeakyDriver) Load(ctx context.Context, _ *wfv1.Artifact, _ string) error {
	d.calls["Load"] = true
	return nil
}

func (d *zzLeakyDriver) OpenStream(ctx context.Context, _ *wfv1.Artifact) (io.ReadCloser, error) {
	d.calls["OpenStream"] = true
	return io.NopCloser(strings.NewReader("data")), nil
}

func (d *zzLeakyDriver) Save(ctx context.Context, _ string, _ *wfv1.Artifact) error {
	d.calls["Save"] = true
	return nil
}

func (d *zzLeakyDriver) Delete(ctx context.Context, _ *wfv1.Artifact) error {
	d.calls["Delete"] = true
	return nil
}

func (d *zzLeakyDriver) ListObjects(ctx context.Context, _ *wfv1.Artifact) ([]string, error) {
	d.calls["ListObjects"] = true
	return []string{"a"}, nil
}

func (d *zzLeakyDriver) IsDirectory(ctx context.Context, _ *wfv1.Artifact) (bool, error) {
	d.calls["IsDirectory"] = true
	return false, nil
}

// zzLoggingCtx returns a context carrying a buffer-backed JSON logger, plus the
// buffer so the test can inspect everything that was logged.
func zzLoggingCtx(t *testing.T) (context.Context, *bytes.Buffer) {
	t.Helper()
	buf := &bytes.Buffer{}
	logger := ulog.NewSlogLoggerCustom(ulog.Debug, ulog.JSON, buf)
	return ulog.WithLogger(context.Background(), logger), buf
}

func zzArt() *wfv1.Artifact { return &wfv1.Artifact{Name: "my-artifact"} }

func TestSecZZArtifactLoadNoCredLeak(t *testing.T) {
	ctx, buf := zzLoggingCtx(t)
	_ = New(zzNewLeakyDriver()).Load(ctx, zzArt(), "/tmp/x")
	if strings.Contains(buf.String(), zzSecret) {
		t.Fatalf("credential leaked into logs: %s", buf.String())
	}
}

func TestSecZZArtifactSaveNoCredLeak(t *testing.T) {
	ctx, buf := zzLoggingCtx(t)
	_ = New(zzNewLeakyDriver()).Save(ctx, "/tmp/x", zzArt())
	if strings.Contains(buf.String(), zzSecret) {
		t.Fatalf("credential leaked into logs: %s", buf.String())
	}
}

func TestSecZZArtifactOpenStreamNoCredLeak(t *testing.T) {
	ctx, buf := zzLoggingCtx(t)
	_, _ = New(zzNewLeakyDriver()).OpenStream(ctx, zzArt())
	if strings.Contains(buf.String(), zzSecret) {
		t.Fatalf("credential leaked into logs: %s", buf.String())
	}
}

func TestSecZZArtifactDeleteNoCredLeak(t *testing.T) {
	ctx, buf := zzLoggingCtx(t)
	_ = New(zzNewLeakyDriver()).Delete(ctx, zzArt())
	if strings.Contains(buf.String(), zzSecret) {
		t.Fatalf("credential leaked into logs: %s", buf.String())
	}
}

func TestSecZZArtifactListObjectsNoCredLeak(t *testing.T) {
	ctx, buf := zzLoggingCtx(t)
	_, _ = New(zzNewLeakyDriver()).ListObjects(ctx, zzArt())
	if strings.Contains(buf.String(), zzSecret) {
		t.Fatalf("credential leaked into logs: %s", buf.String())
	}
}

func TestSecZZArtifactIsDirectoryNoCredLeak(t *testing.T) {
	ctx, buf := zzLoggingCtx(t)
	_, _ = New(zzNewLeakyDriver()).IsDirectory(ctx, zzArt())
	if strings.Contains(buf.String(), zzSecret) {
		t.Fatalf("credential leaked into logs: %s", buf.String())
	}
}

// Functional: the wrapper must still delegate every call to the real driver and
// return its result, so logging redaction does not disable artifact handling.
func TestFuncZZArtifactDelegates(t *testing.T) {
	ctx, _ := zzLoggingCtx(t)
	d := zzNewLeakyDriver()
	w := New(d)
	if err := w.Load(ctx, zzArt(), "/tmp/x"); err != nil {
		t.Fatalf("Load: %v", err)
	}
	if err := w.Save(ctx, "/tmp/x", zzArt()); err != nil {
		t.Fatalf("Save: %v", err)
	}
	if _, err := w.OpenStream(ctx, zzArt()); err != nil {
		t.Fatalf("OpenStream: %v", err)
	}
	if err := w.Delete(ctx, zzArt()); err != nil {
		t.Fatalf("Delete: %v", err)
	}
	if _, err := w.ListObjects(ctx, zzArt()); err != nil {
		t.Fatalf("ListObjects: %v", err)
	}
	for _, m := range []string{"Load", "Save", "OpenStream", "Delete", "ListObjects"} {
		if !d.calls[m] {
			t.Fatalf("wrapper did not delegate %s to the underlying driver", m)
		}
	}
}
