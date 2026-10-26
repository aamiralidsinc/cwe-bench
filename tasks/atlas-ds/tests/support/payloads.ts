export const XSS_IMG = '<img src=x onerror="alert(1)">';
export const XSS_SCRIPT = '<script>alert(2)</script>';
export const XSS_LINK = '<a href="javascript:alert(3)">go</a>';
export const XSS_ALL = XSS_IMG + XSS_SCRIPT + XSS_LINK;
export const RICH = '<p>hello <b>bold</b> <em>it</em> <strong>st</strong> <u>u</u> <a href="https://example.com/a">link</a> <a href="mailto:a@example.com">mail</a></p><ul><li>one</li><li>two</li></ul><h3>head</h3>';
