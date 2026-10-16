// Build-cache stub. It imports what the real file imports so the image
// pre-compiles those packages. The real file is hidden: tests/test.sh copies
// it over this one from /tests at grading time. Never put test code here.
package functional

import (
	_ "net/http"
	_ "os"
	_ "rclones3harness/s3test"
	_ "strings"
	_ "testing"
)
