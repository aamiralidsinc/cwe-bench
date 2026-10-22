package executor

// Functional suite: legitimate action execution must keep working exactly as
// today, including the coupled behaviours next to each command sink.

import (
	"testing"

	config "github.com/OliveTin/OliveTin/internal/config"
)

// A normal action with a declared argument still templates its value into the
// command.
func TestFunc_DeclaredArgumentRuns(t *testing.T) {
	out := otTempFile(t, "out")
	act := &config.Action{
		Title: "Greet",
		Shell: "printf '%s' {{ target }} > " + out,
		Arguments: []config.ActionArgument{
			{Name: "target", Type: "ascii"},
		},
	}

	runOTAction(t, act, otUser("alice"), map[string]string{"target": "hello"})

	if got := otReadFile(t, out); got != "hello" {
		t.Fatalf("declared argument did not reach the command: got %q", got)
	}
}

// An ordinary email-style username must stay valid and reach the command.
func TestFunc_EmailUsernameIntoCommand(t *testing.T) {
	out := otTempFile(t, "out")
	act := &config.Action{Title: "AuditMain", Shell: "printf '%s' {{ ot_username }} > " + out}

	runOTAction(t, act, otUser("alice@example.com"), nil)

	if got := otReadFile(t, out); got != "alice@example.com" {
		t.Fatalf("email username did not reach the command: got %q", got)
	}
}

// Plus-addressing in a username must stay valid.
func TestFunc_PlusAddressingUsernameIntoCommand(t *testing.T) {
	out := otTempFile(t, "out")
	act := &config.Action{Title: "AuditMain", Shell: "printf '%s' {{ ot_username }} > " + out}

	runOTAction(t, act, otUser("alice+tag@example.com"), nil)

	if got := otReadFile(t, out); got != "alice+tag@example.com" {
		t.Fatalf("plus-addressing username did not reach the command: got %q", got)
	}
}

// The username must still be delivered to the command environment.
func TestFunc_UsernameInEnvironment(t *testing.T) {
	out := otTempFile(t, "out")
	act := &config.Action{Title: "EnvUser", Shell: `printf '%s' "$OT_USERNAME" > ` + out}

	runOTAction(t, act, otUser("alice@example.com"), nil)

	if got := otReadFile(t, out); got != "alice@example.com" {
		t.Fatalf("username not delivered to the environment: got %q", got)
	}
}

// The execution tracking id must still be delivered to the command environment.
func TestFunc_TrackingIdInEnvironment(t *testing.T) {
	out := otTempFile(t, "out")
	act := &config.Action{Title: "EnvTrack", Shell: `printf '%s' "$OT_EXECUTIONTRACKINGID" > ` + out}

	runOTAction(t, act, otUser("alice"), nil)

	if got := otReadFile(t, out); got == "" {
		t.Fatalf("execution tracking id not delivered to the environment")
	}
}

// The post-completion command must still run and receive the username.
func TestFunc_PostCompletionReceivesUsername(t *testing.T) {
	out := otTempFile(t, "out")
	act := &config.Action{
		Title:               "AuditAfter",
		Shell:               "echo main",
		ShellAfterCompleted: "printf '%s' {{ ot_username }} > " + out,
	}

	runOTAction(t, act, otUser("alice@example.com"), nil)

	if got := otReadFile(t, out); got != "alice@example.com" {
		t.Fatalf("post-completion command did not receive the username: got %q", got)
	}
}
