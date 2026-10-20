<instruction_md>
# Login could change secrets outside the folder named by its access rule

## What was observed

We installed an access rule through the policy API for a userpass login, then called the secrets API as that login. The rule allows create, read, and update under a secrets folder whose name is filled from that login's entity metadata. With the metadata set to a plain team name, writes succeeded only inside that team's folder.

We then stored an asterisk in that same metadata field and repeated the write. The login could create and update secrets in other teams' folders. The asterisk was copied out of the identity record into the path, and the path rule treated it as syntax, so the login was no longer confined to the folder the rule was written for.

## Impact

A person who can influence the identity value this rule reads can widen their own access and change data that belongs to other teams. The same identity record is also used when this server decides which name a caller may receive. A character in that record that the decision treats as syntax must not add a name the operator did not write.

## What must keep working

An ordinary name stored on the identity record must still grant create, read, and update on exactly the folder that name selects.

A wildcard that an operator typed into the access rule itself must still match the paths it matches today. Another path in that same rule that does not read the identity record must keep allowing what it allows today, including when the identity value is one that would widen a path that does read the identity record.

Other decisions that fill an allowed name from this same identity record must still accept one ordinary name. Characters an operator typed into such a decision must keep the meaning they have today.
</instruction_md>
<task_metadata_json>
{
  "entry_point": "Userpass login with an access rule whose secrets folder is filled from entity metadata, then a write on the secrets API",
  "techniques": [
    1,
    2,
    3,
    4,
    5,
    7,
    9,
    12,
    15
  ],
  "trap": {
    "paths": [
      "builtin/logical/pki/cert_util.go",
      "builtin/logical/ssh/path_issue_sign.go"
    ],
    "contract": "An ordinary identity name still grants exactly the folder or name it selects, and a wildcard, glob, or name list the operator typed into the rule still means what it means today."
  },
  "fix_places": [
    "sdk/helper/identitytpl/templating.go",
    "vault/policy/policy.go",
    "vault/policy/policy_store.go",
    "builtin/logical/pki/cert_util.go",
    "builtin/logical/ssh/path_issue_sign.go"
  ],
  "unrelated_files": [
    "builtin/logical/pki/path_roles.go",
    "builtin/logical/ssh/path_roles.go",
    "sdk/framework/identity.go",
    "vault/logical_system.go",
    "vault/logical_system_paths.go"
  ],
  "test_justifications": {
    "test_security_policy_asterisk_metadata": "We then stored an asterisk in that same metadata field and repeated the write.",
    "test_security_policy_plus_metadata": "the path rule treated it as syntax, so the login was no longer confined to the folder the rule was written for.",
    "test_security_policy_slash_metadata": "the path rule treated it as syntax, so the login was no longer confined to the folder the rule was written for.",
    "test_security_policy_group_asterisk": "The asterisk was copied out of the identity record into the path, and the path rule treated it as syntax, so the login was no longer confined to the folder the rule was written for.",
    "test_security_filled_name_glob": "A character in that record that the decision treats as syntax must not add a name the operator did not write.",
    "test_security_filled_uri_glob": "A character in that record that the decision treats as syntax must not add a name the operator did not write.",
    "test_security_filled_name_extra_user": "A character in that record that the decision treats as syntax must not add a name the operator did not write.",
    "test_security_filled_name_extra_host": "A character in that record that the decision treats as syntax must not add a name the operator did not write.",
    "test_functional_ordinary_metadata_folder": "An ordinary name stored on the identity record must still grant create, read, and update on exactly the folder that name selects.",
    "test_functional_operator_typed_wildcard": "A wildcard that an operator typed into the access rule itself must still match the paths it matches today.",
    "test_functional_untouched_path_beside_widening_value": "Another path in that same rule that does not read the identity record must keep allowing what it allows today, including when the identity value is one that would widen a path that does read the identity record.",
    "test_functional_ordinary_filled_certificate_name": "Other decisions that fill an allowed name from this same identity record must still accept one ordinary name.",
    "test_functional_ordinary_filled_ssh_user": "Other decisions that fill an allowed name from this same identity record must still accept one ordinary name.",
    "test_functional_operator_typed_glob": "Characters an operator typed into such a decision must keep the meaning they have today.",
    "test_functional_operator_typed_name_list": "Characters an operator typed into such a decision must keep the meaning they have today."
  }
}
</task_metadata_json>
<check_patches_json>
{
  "shallow": [
    {
      "file": "sdk/helper/identitytpl/templating.go",
      "search": "\t\t\t\ttmplStr, err := performTemplating(strings.TrimSpace(splitPiece[0]), &p)\n\t\t\t\tif err != nil {\n\t\t\t\t\treturn false, \"\", err\n\t\t\t\t}\n\t\t\t\tb.WriteString(tmplStr)\n\t\t\t\tb.WriteString(splitPiece[1])",
      "replace": "\t\t\t\ttmplStr, err := performTemplating(strings.TrimSpace(splitPiece[0]), &p)\n\t\t\t\tif err != nil {\n\t\t\t\t\treturn false, \"\", err\n\t\t\t\t}\n\t\t\t\tif strings.Contains(tmplStr, \"*\") {\n\t\t\t\t\treturn false, \"\", fmt.Errorf(\"template substitution contains forbidden value %q\", \"*\")\n\t\t\t\t}\n\t\t\t\tb.WriteString(tmplStr)\n\t\t\t\tb.WriteString(splitPiece[1])"
    }
  ],
  "removal": [
    {
      "file": "sdk/helper/identitytpl/templating.go",
      "search": "\t\t\t\ttmplStr, err := performTemplating(strings.TrimSpace(splitPiece[0]), &p)\n\t\t\t\tif err != nil {\n\t\t\t\t\treturn false, \"\", err\n\t\t\t\t}\n\t\t\t\tb.WriteString(tmplStr)\n\t\t\t\tb.WriteString(splitPiece[1])",
      "replace": "\t\t\t\t_, err := performTemplating(strings.TrimSpace(splitPiece[0]), &p)\n\t\t\t\tif err != nil {\n\t\t\t\t\treturn false, \"\", err\n\t\t\t\t}\n\t\t\t\treturn false, \"\", errors.New(\"identity substitution is disabled\")"
    }
  ],
  "alternative": [
    {
      "file": "sdk/helper/identitytpl/templating.go",
      "search": "\t\t\t\ttmplStr, err := performTemplating(strings.TrimSpace(splitPiece[0]), &p)\n\t\t\t\tif err != nil {\n\t\t\t\t\treturn false, \"\", err\n\t\t\t\t}\n\t\t\t\tb.WriteString(tmplStr)\n\t\t\t\tb.WriteString(splitPiece[1])",
      "replace": "\t\t\t\ttmplStr, err := performTemplating(strings.TrimSpace(splitPiece[0]), &p)\n\t\t\t\tif err != nil {\n\t\t\t\t\treturn false, \"\", err\n\t\t\t\t}\n\t\t\t\tif p.Mode == ACLTemplating {\n\t\t\t\t\tfor _, blocked := range []string{\"*\", \"+\", \"/\", \",\"} {\n\t\t\t\t\t\tif strings.Contains(tmplStr, blocked) {\n\t\t\t\t\t\t\treturn false, \"\", fmt.Errorf(\"template substitution contains forbidden value %q\", blocked)\n\t\t\t\t\t\t}\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t\tb.WriteString(tmplStr)\n\t\t\t\tb.WriteString(splitPiece[1])"
    }
  ]
}
</check_patches_json>
