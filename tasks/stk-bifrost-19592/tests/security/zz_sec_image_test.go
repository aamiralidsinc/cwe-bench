package gemini_test

import (
	"context"
	"strings"
	"testing"
	"time"

	"github.com/maximhq/bifrost/core/providers/gemini"
	"github.com/maximhq/bifrost/core/schemas"
)

// hiddenImageReachedNetwork reports whether the conversion error shows the
// image fetch actually reached the network instead of being refused.
func hiddenImageReachedNetwork(err error) bool {
	if err == nil {
		return false
	}
	msg := strings.ToLower(err.Error())
	for _, marker := range []string{
		"network is unreachable", "no route to host", "connection refused",
		"connection reset", "connection closed", "broken pipe", "i/o timeout", "timed out",
		"empty reply", "unexpected eof", "eof",
	} {
		if strings.Contains(msg, marker) {
			return true
		}
	}
	return false
}

func hiddenImageMustRefuse(t *testing.T, imageURL string) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	_, err := gemini.ToGeminiImageGenerationResponse(ctx, &schemas.BifrostImageGenerationResponse{
		Data: []schemas.ImageData{{URL: imageURL}},
	})
	if err == nil {
		t.Fatalf("%q was downloaded; an image URL must not reach this destination", imageURL)
	}
	if hiddenImageReachedNetwork(err) {
		t.Fatalf("%q was not refused before connecting (reached the network: %v)", imageURL, err)
	}
}

// The shared carrier-grade NAT range is reserved and must not be a fetch target.
func TestSec_ImageCGNATRange(t *testing.T) {
	hiddenImageMustRefuse(t, "http://100.64.0.1:51999/i.png")
}

func TestSec_ImageCGNATRangeHigh(t *testing.T) {
	hiddenImageMustRefuse(t, "http://100.127.255.255:51999/i.png")
}
