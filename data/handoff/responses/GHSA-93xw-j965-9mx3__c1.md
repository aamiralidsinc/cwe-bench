<instruction_md>
# A file outside the working directory was published on an issue

## What we observed

We asked this server to attach a local file to a Jira issue. The path we supplied did not stay inside the directory the process was using as its working directory. The server read that file anyway and uploaded its contents onto the issue. We saw the same publication when the path climbed out through a parent directory, and when the name we gave was a link that sits inside the working directory but points at a file outside it. We had not asked to publish that outside file.

## Impact

A caller who can name a local file can have this server read a file that sits outside the working directory and send those contents onward. In our case the contents showed up on the issue. Files elsewhere on the host, including credentials, are exposed that way.

## What must keep working

Attaching a file that already lives in the working directory must still succeed, and that file's own contents must still be what gets sent. Naming that same file by a full path that points inside the working directory must still succeed. A path that steps into a subfolder and then back out before the file name must still succeed. Typing a page's text directly must still publish that text. Pointing a page at a file that already lives in the working directory must still publish that file's text, including when the path is a full path inside the working directory or steps into a subfolder and back.
</instruction_md>
<task_metadata_json>
{
  "entry_point": "Attaching a caller-chosen local file to a Jira issue",
  "techniques": [
    1,
    2,
    5,
    7,
    9,
    12
  ],
  "trap": {
    "paths": [
      "src/mcp_atlassian/confluence/attachments.py",
      "src/mcp_atlassian/servers/confluence.py"
    ],
    "contract": "A file already in the working directory is still attached and its contents are sent, including a full path inside that directory and a path that steps into a subfolder and back; a page pointed at such a file still publishes that file's text, and text typed for a page is still published."
  },
  "fix_places": [
    "src/mcp_atlassian/jira/attachments.py",
    "src/mcp_atlassian/confluence/attachments.py",
    "src/mcp_atlassian/servers/confluence.py"
  ],
  "unrelated_files": [
    "src/mcp_atlassian/confluence/client.py",
    "src/mcp_atlassian/confluence/search.py",
    "src/mcp_atlassian/jira/client.py",
    "src/mcp_atlassian/jira/search.py",
    "src/mcp_atlassian/servers/dependencies.py",
    "src/mcp_atlassian/servers/main.py",
    "src/mcp_atlassian/utils/oauth.py",
    "src/mcp_atlassian/utils/oauth_setup.py",
    "src/mcp_atlassian/utils/ssl.py",
    "src/mcp_atlassian/utils/ssrf_adapter.py",
    "src/mcp_atlassian/utils/urls.py"
  ],
  "test_justifications": {
    "test_security_issue_absolute_outside": "The path we supplied did not stay inside the directory the process was using as its working directory. The server read that file anyway and uploaded its contents onto the issue.",
    "test_security_issue_parent_escape": "We saw the same publication when the path climbed out through a parent directory",
    "test_security_parallel_absolute_outside": "A caller who can name a local file can have this server read a file that sits outside the working directory and send those contents onward.",
    "test_security_parallel_link_outside": "when the name we gave was a link that sits inside the working directory but points at a file outside it.",
    "test_security_page_absolute_outside": "A caller who can name a local file can have this server read a file that sits outside the working directory and send those contents onward.",
    "test_security_page_link_outside": "when the name we gave was a link that sits inside the working directory but points at a file outside it.",
    "test_functional_attach_file_in_workdir": "Attaching a file that already lives in the working directory must still succeed, and that file's own contents must still be what gets sent.",
    "test_functional_attach_full_path_inside": "Naming that same file by a full path that points inside the working directory must still succeed.",
    "test_functional_attach_step_back": "A path that steps into a subfolder and then back out before the file name must still succeed.",
    "test_functional_parallel_attach_step_back": "A path that steps into a subfolder and then back out before the file name must still succeed.",
    "test_functional_page_typed_text": "Typing a page's text directly must still publish that text.",
    "test_functional_page_file_full_path_inside": "Pointing a page at a file that already lives in the working directory must still publish that file's text, including when the path is a full path inside the working directory or steps into a subfolder and back."
  }
}
</task_metadata_json>
<check_patches_json>
{
  "shallow": [
    {
      "file": "src/mcp_atlassian/jira/attachments.py",
      "search": "            # Convert to absolute path if relative\n            if not os.path.isabs(file_path):\n                file_path = os.path.abspath(file_path)\n\n            # Check if file exists\n            if not os.path.exists(file_path):\n                logger.error(f\"File not found: {file_path}\")\n                return {\"success\": False, \"error\": f\"File not found: {file_path}\"}\n\n            logger.info(f\"Uploading attachment from {file_path} to issue {issue_key}\")\n",
      "replace": "            file_path = str(validate_safe_path(file_path))\n\n            # Check if file exists\n            if not os.path.exists(file_path):\n                logger.error(f\"File not found: {file_path}\")\n                return {\"success\": False, \"error\": f\"File not found: {file_path}\"}\n\n            logger.info(f\"Uploading attachment from {file_path} to issue {issue_key}\")\n"
    }
  ],
  "removal": [
    {
      "file": "src/mcp_atlassian/jira/attachments.py",
      "search": "        if not file_path:\n            logger.error(\"No file path provided for attachment upload\")\n            return {\"success\": False, \"error\": \"No file path provided\"}\n\n        try:\n            # Convert to absolute path if relative\n            if not os.path.isabs(file_path):\n                file_path = os.path.abspath(file_path)\n",
      "replace": "        if not file_path:\n            logger.error(\"No file path provided for attachment upload\")\n            return {\"success\": False, \"error\": \"No file path provided\"}\n\n        return {\"success\": False, \"error\": \"Attachment upload is disabled\"}\n\n        try:\n            # Convert to absolute path if relative\n            if not os.path.isabs(file_path):\n                file_path = os.path.abspath(file_path)\n"
    }
  ],
  "alternative": [
    {
      "file": "src/mcp_atlassian/jira/attachments.py",
      "search": "            # Convert to absolute path if relative\n            if not os.path.isabs(file_path):\n                file_path = os.path.abspath(file_path)\n\n            # Check if file exists\n            if not os.path.exists(file_path):\n                logger.error(f\"File not found: {file_path}\")\n                return {\"success\": False, \"error\": f\"File not found: {file_path}\"}\n\n            logger.info(f\"Uploading attachment from {file_path} to issue {issue_key}\")\n",
      "replace": "            base = Path.cwd().resolve()\n            candidate = Path(file_path).expanduser()\n            if not candidate.is_absolute():\n                candidate = base / candidate\n            resolved = candidate.resolve()\n            if not resolved.is_relative_to(base):\n                return {\"success\": False, \"error\": \"Refusing a path outside the working directory\"}\n            file_path = str(resolved)\n\n            # Check if file exists\n            if not os.path.exists(file_path):\n                logger.error(f\"File not found: {file_path}\")\n                return {\"success\": False, \"error\": f\"File not found: {file_path}\"}\n\n            logger.info(f\"Uploading attachment from {file_path} to issue {issue_key}\")\n"
    },
    {
      "file": "src/mcp_atlassian/confluence/attachments.py",
      "search": "            # Convert to absolute path if relative\n            if not os.path.isabs(file_path):\n                file_path = os.path.abspath(file_path)\n\n            # Check if file exists\n",
      "replace": "            base = Path.cwd().resolve()\n            candidate = Path(file_path).expanduser()\n            if not candidate.is_absolute():\n                candidate = base / candidate\n            resolved = candidate.resolve()\n            if not resolved.is_relative_to(base):\n                return {\"success\": False, \"error\": \"Refusing a path outside the working directory\"}\n            file_path = str(resolved)\n\n            # Check if file exists\n"
    },
    {
      "file": "src/mcp_atlassian/servers/confluence.py",
      "search": "    path = Path(content_file).expanduser()\n    if not path.is_file():\n        msg = f\"content_file does not exist or is not a regular file: {path}\"\n        raise ValueError(msg)\n    return path.read_text(encoding=\"utf-8\")\n",
      "replace": "    path = Path(content_file).expanduser()\n    base = Path.cwd().resolve()\n    candidate = path if path.is_absolute() else base / path\n    resolved = candidate.resolve()\n    if not resolved.is_relative_to(base):\n        raise ValueError(\"Refusing a path outside the working directory\")\n    path = resolved\n    if not path.is_file():\n        msg = f\"content_file does not exist or is not a regular file: {path}\"\n        raise ValueError(msg)\n    return path.read_text(encoding=\"utf-8\")\n"
    }
  ]
}
</check_patches_json>
