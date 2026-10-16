"""The editor "save as / put relative" operation takes a suggested target file
name. That value is a bare file name and must not be able to traverse out of
the source file's own directory. A suggested target containing path separators
and ".." must not create a file outside that directory."""
import cr


def _escape_attempt(prefix):
    """Put-relative from my/<box>/doc.txt with target <prefix><name>; return the
    escaped name and the account root listing afterwards."""
    token = cr.ensure_admin()
    folder = "cloudreve://my/%s" % cr.uniq("box")
    cr.mkfolder(token, folder)
    doc = folder + "/doc.txt"
    fid = cr.j(cr.upload(token, doc, b"hi"))["data"]["id"]
    access = cr.viewer_session(token, doc)
    escaped_name = cr.uniq("pwned") + ".txt"
    cr.wopi_put_relative(fid, access, prefix + escaped_name, data=b"OWNED")
    return escaped_name, cr.listing(token, "cloudreve://my")


def test_putrelative_absolute_target_cannot_escape_source_directory():
    # A rooted target whose ".." climbs out once the leading separator is dropped.
    escaped_name, siblings = _escape_attempt("/../")
    outside = "cloudreve://my/" + escaped_name
    assert outside not in siblings, \
        "put-relative with an absolute-style target escaped and wrote %s" % outside


def test_putrelative_cannot_escape_source_directory():
    token = cr.ensure_admin()
    folder = "cloudreve://my/%s" % cr.uniq("box")
    cr.mkfolder(token, folder)
    doc = folder + "/doc.txt"
    fid = cr.j(cr.upload(token, doc, b"hi"))["data"]["id"]
    access = cr.viewer_session(token, doc)
    escaped_name = cr.uniq("pwned") + ".txt"
    # From the source dir, "a/../../<name>" normalises to one level above it.
    cr.wopi_put_relative(fid, access, "a/../../" + escaped_name, data=b"OWNED")
    outside = "cloudreve://my/" + escaped_name
    siblings = cr.listing(token, "cloudreve://my")
    assert outside not in siblings, \
        "put-relative escaped the source directory and wrote %s" % outside
