package gemini_test

import (
	"context"
	"encoding/base64"
	"strings"
	"testing"
	"time"

	"github.com/maximhq/bifrost/core/providers/gemini"
	"github.com/maximhq/bifrost/core/schemas"
)

func hiddenFuncImageReachedNetwork(err error) bool {
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

// Inline image data is converted without any fetch.
func TestFunc_ImageInlineDataWorks(t *testing.T) {
	payload := base64.StdEncoding.EncodeToString([]byte("inline-image-bytes"))
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	resp, err := gemini.ToGeminiImageGenerationResponse(ctx, &schemas.BifrostImageGenerationResponse{
		Data: []schemas.ImageData{{B64JSON: payload}},
	})
	if err != nil {
		t.Fatalf("inline image data must keep converting: %v", err)
	}
	if resp == nil || len(resp.Candidates) == 0 || len(resp.Candidates[0].Content.Parts) == 0 {
		t.Fatalf("inline image conversion returned no content")
	}
	part := resp.Candidates[0].Content.Parts[0]
	if part.InlineData == nil || part.InlineData.Data != payload {
		t.Fatalf("inline image data was not preserved")
	}
}

// Ordinary public image targets are still fetched.
func TestFunc_ImageAllowsOrdinaryPublic(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	_, err := gemini.ToGeminiImageGenerationResponse(ctx, &schemas.BifrostImageGenerationResponse{
		Data: []schemas.ImageData{{URL: "http://8.8.8.8:51999/i.png"}},
	})
	if err == nil {
		return
	}
	if !hiddenFuncImageReachedNetwork(err) {
		t.Fatalf("an ordinary public image target was refused instead of fetched: %v", err)
	}
}

// The address just outside the reserved shared range is a normal public address.
func TestFunc_ImageAllowsPublicNeighbourOfReservedRange(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	_, err := gemini.ToGeminiImageGenerationResponse(ctx, &schemas.BifrostImageGenerationResponse{
		Data: []schemas.ImageData{{URL: "http://100.128.0.1:51999/i.png"}},
	})
	if err == nil {
		return
	}
	if !hiddenFuncImageReachedNetwork(err) {
		t.Fatalf("a public image target was refused instead of fetched: %v", err)
	}
}
