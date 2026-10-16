// Build-cache stub. It imports what the real file imports so the image
// pre-compiles those packages. The real file is hidden: tests/test.sh copies
// it over this one from /tests at grading time. Never put test code here.
package s3test

import (
	_ "bytes"
	_ "context"
	_ "crypto/sha256"
	_ "encoding/hex"
	_ "fmt"
	_ "github.com/aws/aws-sdk-go-v2/aws"
	_ "github.com/aws/aws-sdk-go-v2/aws/signer/v4"
	_ "io"
	_ "net"
	_ "net/http"
	_ "os"
	_ "os/exec"
	_ "sync/atomic"
	_ "testing"
	_ "time"
)
