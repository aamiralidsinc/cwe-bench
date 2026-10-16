"""The collaborative editor must keep working for legitimate use: a valid
access token grants access, and a put-relative with a bare file name creates a
sibling in the source file's own directory."""
import cr


def test_valid_token_grants_file_info():
    token = cr.ensure_admin()
    uri = "cloudreve://my/%s.txt" % cr.uniq("doc")
    fid = cr.j(cr.upload(token, uri, b"content"))["data"]["id"]
    access = cr.viewer_session(token, uri)
    res = cr.wopi_check(fid, access)
    assert res.get("code") == 200, "valid editor token rejected: %r" % res.get("code")


def test_put_relative_bare_name_creates_sibling():
    token = cr.ensure_admin()
    folder = "cloudreve://my/%s" % cr.uniq("box")
    cr.mkfolder(token, folder)
    doc = folder + "/doc.txt"
    fid = cr.j(cr.upload(token, doc, b"hi"))["data"]["id"]
    access = cr.viewer_session(token, doc)
    name = cr.uniq("saved") + ".txt"
    res = cr.wopi_put_relative(fid, access, name, data=b"ok")
    assert res.get("code") == 200, "legitimate put-relative failed: %r" % res.get("code")
    assert (folder + "/" + name) in cr.listing(token, folder), \
        "legitimate put-relative did not create the sibling file"
