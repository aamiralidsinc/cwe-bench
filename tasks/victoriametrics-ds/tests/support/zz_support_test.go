package actions_test

import (
	"fmt"
	"io"

	"github.com/VictoriaMetrics/VictoriaMetrics/lib/backup/common"
)

// secTestRemote is a test double for a backup remote. It is faithful to the real
// backends: ListParts returns the parts that the backend derived from the object
// names in the remote storage, and ReadFile returns the content of a named file.
type secTestRemote struct {
	parts []common.Part
	files map[string][]byte
}

func (r *secTestRemote) MustStop() {}

func (r *secTestRemote) String() string { return "sec-test-remote" }

func (r *secTestRemote) ListParts() ([]common.Part, error) { return r.parts, nil }

func (r *secTestRemote) DeletePart(common.Part) error { return nil }

func (r *secTestRemote) RemoveEmptyDirs() error { return nil }

func (r *secTestRemote) CopyPart(common.OriginFS, common.Part) error {
	return fmt.Errorf("unexpected server-side copy")
}

func (r *secTestRemote) DownloadPart(p common.Part, w io.Writer) error {
	_, err := w.Write(make([]byte, p.Size))
	return err
}

func (r *secTestRemote) UploadPart(common.Part, io.Reader) error {
	return fmt.Errorf("unexpected upload")
}

func (r *secTestRemote) DeleteFile(string) error { return nil }

func (r *secTestRemote) CreateFile(string, []byte) error { return nil }

func (r *secTestRemote) HasFile(name string) (bool, error) {
	_, ok := r.files[name]
	return ok, nil
}

func (r *secTestRemote) ReadFile(name string) ([]byte, error) {
	data, ok := r.files[name]
	if !ok {
		return nil, fmt.Errorf("cannot read %q from the test remote", name)
	}
	return data, nil
}

// secPart builds a single-part file description for the given remote path.
func secPart(path string, size uint64) common.Part {
	return common.Part{
		Path:       path,
		FileSize:   size,
		Offset:     0,
		Size:       size,
		ActualSize: size,
	}
}
