"""Every documented install source form keeps working."""

import support


def test_ssc_install_sends_the_documented_command():
    support.reset_capture()
    support.clean_state()
    from stata_mcp.api import ado_package_install

    message = ado_package_install("outreg2")
    assert "Installation State: True" in message, message
    assert "ssc install outreg2, replace" in support.lines()


def test_github_install_accepts_user_repo_and_looks_up_its_help():
    support.reset_capture()
    support.clean_state()
    from stata_mcp.api import ado_package_install

    message = ado_package_install("SepineTam/TexIV", source="github")
    assert "Installation State: True" in message, message
    sent = support.lines()
    assert "github install SepineTam/TexIV, replace" in sent
    assert "help SepineTam/TexIV" in sent


def test_net_install_accepts_a_source_url():
    support.reset_capture()
    support.clean_state()
    from stata_mcp.api import ado_package_install

    message = ado_package_install(
        "custompkg", source="net", package_source_from="https://example.com/stata/"
    )
    assert "Installation State: True" in message, message
    assert (
        "net install custompkg, replace from(https://example.com/stata/)" in support.lines()
    )


def test_mcp_tool_install_keeps_the_same_behaviour():
    support.reset_capture()
    support.clean_state()
    from stata_mcp import mcp_servers

    message = mcp_servers.ado_package_install("outreg2", source="ssc")
    assert "Installation State: True" in message, message
    assert "ssc install outreg2, replace" in support.lines()
