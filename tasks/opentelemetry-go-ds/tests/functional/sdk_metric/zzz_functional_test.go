package metric_test

import (
	"bytes"
	"context"
	"strings"
	"sync"
	"testing"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/internal/global"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/metric/metricdata"
)

type recordingExporter struct {
	mu sync.Mutex
	rm int
}

func (e *recordingExporter) Temporality(sdkmetric.InstrumentKind) metricdata.Temporality {
	return metricdata.DeltaTemporality
}
func (*recordingExporter) Aggregation(sdkmetric.InstrumentKind) sdkmetric.Aggregation {
	return sdkmetric.AggregationDefault{}
}
func (e *recordingExporter) Export(_ context.Context, rm *metricdata.ResourceMetrics) error {
	e.mu.Lock()
	e.rm += len(rm.ScopeMetrics)
	e.mu.Unlock()
	return nil
}
func (*recordingExporter) ForceFlush(context.Context) error { return nil }
func (*recordingExporter) Shutdown(context.Context) error  { return nil }
func (e *recordingExporter) count() int {
	e.mu.Lock()
	defer e.mu.Unlock()
	return e.rm
}

func TestFunc_MetricProviderReportsAndExports(t *testing.T) {
	var buf bytes.Buffer
	orig := global.GetLogger()
	global.SetLogger(funcr.New(func(_, args string) {
		buf.WriteString(args + "\n")
	}, funcr.Options{Verbosity: 4}))
	t.Cleanup(func() { global.SetLogger(orig) })

	exp := &recordingExporter{}
	reader := sdkmetric.NewPeriodicReader(exp)
	mp := sdkmetric.NewMeterProvider(sdkmetric.WithReader(reader))

	counter, err := mp.Meter("functional").Int64Counter("requests")
	if err != nil {
		t.Fatal(err)
	}
	counter.Add(context.Background(), 1)
	if err := mp.ForceFlush(context.Background()); err != nil {
		t.Fatal(err)
	}
	if err := mp.Shutdown(context.Background()); err != nil {
		t.Fatal(err)
	}

	if exp.count() == 0 {
		t.Fatal("metric flush did not reach the exporter")
	}
	out := buf.String()
	for _, want := range []string{"MeterProvider created", "PeriodicReader"} {
		if !strings.Contains(out, want) {
			t.Fatalf("provider record lost %q: %q", want, out)
		}
	}
}
