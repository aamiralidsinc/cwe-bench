"""Requesting a thumbnail for an image whose declared dimensions are enormous
must not cause the server to allocate memory proportional to those dimensions.
A tiny file declaring a 9000x9000 (81 MP) image is a decompression bomb; the
thumbnail request for it must be refused, not processed."""
import cr


def test_pixel_bomb_thumbnail_refused():
    token = cr.ensure_admin()
    uri = "cloudreve://my/%s.png" % cr.uniq("bomb")
    up = cr.upload(token, uri, cr.pixel_bomb_png(9000, 9000))
    assert cr.j(up).get("code") == 0, "upload failed: %r" % up
    res = cr.thumb(token, uri)
    assert res.get("code") not in (0, None), \
        "oversized-dimension image was processed for a thumbnail: %r" % res
