// Build-cache stub. It imports what the real file imports so the image
// pre-compiles those packages. The real file is hidden: tests/test.sh copies
// it over this one from /tests at grading time. Never put test code here.
package main

import (
	_ "encoding/json"
	_ "log"
	_ "os"
)

func main() {}
