package metric_test

import (
	"bytes"
	"context"
	"strings"
	"testing"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/internal/global"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/metric/metricdata"
)

const (
	secretPassword = "pw-8f3a1c"
	secretToken    = "tok-5d92be"
	secretEndpoint = "user:" + secretPassword + "@collector.internal:4318?token=" + secretToken
)

type endpointExporter struct{}

func (endpointExporter) Temporality(sdkmetric.InstrumentKind) metricdata.Temporality {
	return metricdata.DeltaTemporality
}
func (endpointExporter) Aggregation(sdkmetric.InstrumentKind) sdkmetric.Aggregation {
	return sdkmetric.AggregationDefault{}
}
func (endpointExporter) Export(context.Context, *metricdata.ResourceMetrics) error { return nil }
func (endpointExporter) ForceFlush(context.Context) error                         { return nil }
func (endpointExporter) Shutdown(context.Context) error                           { return nil }
func (endpointExporter) MarshalLog() any {
	return struct{ Endpoint string }{Endpoint: secretEndpoint}
}

func TestSec_MetricProviderExporterEndpoint(t *testing.T) {
	var buf bytes.Buffer
	orig := global.GetLogger()
	global.SetLogger(funcr.New(func(_, args string) {
		buf.WriteString(args + "\n")
	}, funcr.Options{Verbosity: 4}))
	t.Cleanup(func() { global.SetLogger(orig) })

	reader := sdkmetric.NewPeriodicReader(endpointExporter{})
	mp := sdkmetric.NewMeterProvider(sdkmetric.WithReader(reader))
	t.Cleanup(func() { _ = mp.Shutdown(context.Background()) })

	logged := buf.String()
	if strings.Contains(logged, secretPassword) || strings.Contains(logged, secretToken) {
		t.Fatalf("diagnostic output carried exporter endpoint credentials: %q", logged)
	}
}
