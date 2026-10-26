"""Viewport capture keeps accepting the absolute path the MCP server supplies."""

from support.harness import outside


def test_absolute_screenshot_path_still_works(product):
    destination = outside(product.root, "captures")
    target = destination / "viewport.png"

    response = product.call(
        "get_viewport_screenshot",
        {"max_size": 100, "filepath": str(target), "format": "png"},
    )

    result = response["result"]
    assert result["success"] is True
    assert result["filepath"] == str(target)
