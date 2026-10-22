package executor

// Security suite: no request-supplied or identity-derived value may reach the
// action's executed command or its environment without a declared safety check.
// Each test drives the real executor and proves that a harmless but unmistakable
// side effect (creating a marker file via a shell metacharacter payload) does
// NOT happen. They fail on the vulnerable code and pass on a correct fix.

import (
	"testing"

	authpublic "github.com/OliveTin/OliveTin/internal/auth/authpublic"
	config "github.com/OliveTin/OliveTin/internal/config"
)

// The invoking user's name is identity-derived (trusted header / token / OAuth2)
// and must be checked before it is placed into the command OliveTin runs.
func TestSec_UsernameIntoCommand(t *testing.T) {
	marker := otTempFile(t, "pwn_user")
	act := &config.Action{Title: "AuditMain", Shell: "echo run-by {{ ot_username }}"}

	runOTAction(t, act, otUser("x$(touch "+marker+")"), nil)

	if otFileExists(marker) {
		t.Fatalf("username payload reached the executed command (marker created)")
	}
}

// An undeclared, client-supplied argument whose name carries the system
// (reserved) prefix must not survive the argument allowlist and reach the
// command environment.
func TestSec_ClientReservedArgIntoEnvironment(t *testing.T) {
	marker := otTempFile(t, "pwn_env")
	act := &config.Action{Title: "EnvConsumer", Shell: `sh -c "$OT_INJECTED"`}

	runOTAction(t, act, otUser("alice"), map[string]string{
		"ot_injected": "touch " + marker,
	})

	if otFileExists(marker) {
		t.Fatalf("undeclared reserved-prefix argument polluted the command environment")
	}
}

// Group membership is another identity-derived value available to actions; like
// the username it must not reach the executed command unchecked (shell path).
func TestSec_UserGroupsIntoCommand(t *testing.T) {
	marker := otTempFile(t, "pwn_groups")
	act := &config.Action{Title: "AuditGroups", Shell: "echo groups {{ userGroups }}"}

	user := &authpublic.AuthenticatedUser{
		Username:      "alice",
		UsergroupLine: "z$(touch " + marker + ")",
	}
	runOTAction(t, act, user, nil)

	if otFileExists(marker) {
		t.Fatalf("group payload reached the executed command (marker created)")
	}
}

// The same identity-derived group value must not reach the environment of an
// action run without a shell either; an action's command can read that
// environment.
func TestSec_UserGroupsIntoEnvironment(t *testing.T) {
	marker := otTempFile(t, "pwn_groups_env")
	act := &config.Action{Title: "EnvGroups", Exec: []string{"sh", "-c", "$USERGROUPS"}}

	user := &authpublic.AuthenticatedUser{
		Username:      "alice",
		UsergroupLine: "touch " + marker,
	}
	runOTAction(t, act, user, nil)

	if otFileExists(marker) {
		t.Fatalf("group payload reached the command environment (marker created)")
	}
}
