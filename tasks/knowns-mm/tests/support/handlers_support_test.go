package handlers

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/howznguyen/knowns/internal/storage"
	"github.com/mark3labs/mcp-go/mcp"
)

// secEnv is one setup per test: a project root under a fresh temp directory and
// a victim file that lives outside every knowledge-base directory.
type secEnv struct {
	t       *testing.T
	base    string
	root    string
	store   *storage.Store
	victim  string
	secret  string
}

const secSecret = "SECRET-MARKER-DO-NOT-LEAK"

func secSetup(t *testing.T) *secEnv {
	t.Helper()
	base := t.TempDir()
	root := filepath.Join(base, ".knowns")
	t.Setenv("HOME", filepath.Join(base, "home"))
	store := storage.NewStore(root)
	if err := store.Init("sec"); err != nil {
		t.Fatalf("store.Init: %v", err)
	}
	return &secEnv{
		t:      t,
		base:   base,
		root:   root,
		store:  store,
		victim: filepath.Join(base, "victim.md"),
		secret: secSecret,
	}
}

// plantVictim writes a file outside every knowledge-base directory.
func (e *secEnv) plantVictim() {
	e.t.Helper()
	content := "---\ntitle: victim\n---\n" + e.secret + "\n"
	if err := os.WriteFile(e.victim, []byte(content), 0o644); err != nil {
		e.t.Fatalf("plant victim: %v", err)
	}
}

func (e *secEnv) victimExists() bool {
	e.t.Helper()
	_, err := os.Stat(e.victim)
	return err == nil
}

func (e *secEnv) readVictim() string {
	e.t.Helper()
	data, err := os.ReadFile(e.victim)
	if err != nil {
		return ""
	}
	return string(data)
}

// secRefused reports whether an MCP tool call was blocked. A blocked call is a
// tool error or a Go error — never a successful result.
func secRefused(res *mcp.CallToolResult, err error) bool {
	if err != nil {
		return true
	}
	return res != nil && res.IsError
}

func secBody(res *mcp.CallToolResult) string {
	if res == nil {
		return ""
	}
	var sb strings.Builder
	for _, c := range res.Content {
		if tc, ok := c.(mcp.TextContent); ok {
			sb.WriteString(tc.Text)
		}
	}
	return sb.String()
}

func secDocCreate(e *secEnv, args map[string]any) (*mcp.CallToolResult, error) {
	return handleDocCreate(func() *storage.Store { return e.store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
}

func secDocGet(e *secEnv, args map[string]any) (*mcp.CallToolResult, error) {
	return handleDocGet(func() *storage.Store { return e.store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
}

func secDocDelete(e *secEnv, args map[string]any) (*mcp.CallToolResult, error) {
	return handleDocDelete(func() *storage.Store { return e.store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
}

func secDocArchive(e *secEnv, args map[string]any) (*mcp.CallToolResult, error) {
	return handleDocArchive(func() *storage.Store { return e.store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
}

func secMemoryGet(e *secEnv, args map[string]any) (*mcp.CallToolResult, error) {
	return handleMemoryGet(func() *storage.Store { return e.store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
}

func secMemoryDelete(e *secEnv, args map[string]any) (*mcp.CallToolResult, error) {
	return handleMemoryDelete(func() *storage.Store { return e.store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
}

func secMemoryPromote(e *secEnv, args map[string]any) (*mcp.CallToolResult, error) {
	return handleMemoryPromote(func() *storage.Store { return e.store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
}

func secMemoryHistory(e *secEnv, args map[string]any) (*mcp.CallToolResult, error) {
	return handleMemoryHistory(func() *storage.Store { return e.store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
}

func secMemoryCheckpoint(e *secEnv, args map[string]any) (*mcp.CallToolResult, error) {
	return handleMemoryCheckpoint(func() *storage.Store { return e.store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
}

func secTemplateCreate(e *secEnv, args map[string]any) (*mcp.CallToolResult, error) {
	return handleTemplateCreate(func() *storage.Store { return e.store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
}

func secTemplateGet(e *secEnv, args map[string]any) (*mcp.CallToolResult, error) {
	return handleTemplateGet(func() *storage.Store { return e.store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
}
