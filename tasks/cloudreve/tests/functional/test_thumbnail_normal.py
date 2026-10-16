"""Thumbnails for normal, reasonably sized images must still be generated."""
import cr


def test_normal_image_thumbnail_generated():
    token = cr.ensure_admin()
    uri = "cloudreve://my/%s.png" % cr.uniq("pic")
    up = cr.j(cr.upload(token, uri, cr.pixel_bomb_png(64, 48)))
    assert up.get("code") == 0, "upload failed: %r" % up
    res = cr.thumb(token, uri)
    assert res.get("code") == 0, "thumbnail not generated for a normal image: %r" % res
    assert res.get("data", {}).get("url"), "no thumbnail url returned: %r" % res


def test_camera_size_image_thumbnail_generated():
    """An ordinary 24-megapixel camera-sized image (6000x4000) is a normal image,
    not an implausible one, and must still thumbnail."""
    token = cr.ensure_admin()
    uri = "cloudreve://my/%s.png" % cr.uniq("photo")
    up = cr.j(cr.upload(token, uri, cr.photo_like_png(6000, 4000)))
    assert up.get("code") == 0, "upload failed: %r" % up
    res = cr.thumb(token, uri)
    assert res.get("code") == 0, "thumbnail not generated for a 6000x4000 image: %r" % res
    assert res.get("data", {}).get("url"), "no thumbnail url returned: %r" % res
