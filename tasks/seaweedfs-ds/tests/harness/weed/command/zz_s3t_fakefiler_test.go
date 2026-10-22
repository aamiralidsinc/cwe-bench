package command

// In-memory filer for the hidden tests: a real gRPC SeaweedFiler service on a
// loopback port, so the product reaches it exactly as it reaches a filer.

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"path"
	"sort"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/seaweedfs/seaweedfs/weed/pb"
	"github.com/seaweedfs/seaweedfs/weed/pb/filer_pb"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"
)

const zzNotFound = "filer: no entry is found in filer store"

type zzFiler struct {
	filer_pb.UnimplementedSeaweedFilerServer
	mu      sync.Mutex
	entries map[string]*filer_pb.Entry // full path -> entry
	addr    pb.ServerAddress
	srv     *grpc.Server
}

func zzStartFiler(t *testing.T) *zzFiler {
	t.Helper()
	lis, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	f := &zzFiler{entries: map[string]*filer_pb.Entry{}}
	f.entries["/buckets"] = &filer_pb.Entry{Name: "buckets", IsDirectory: true, Attributes: &filer_pb.FuseAttributes{}}
	f.srv = grpc.NewServer()
	filer_pb.RegisterSeaweedFilerServer(f.srv, f)
	go f.srv.Serve(lis)
	port := lis.Addr().(*net.TCPAddr).Port
	// host:httpPort.grpcPort -> the gRPC address is host:grpcPort
	f.addr = pb.ServerAddress(fmt.Sprintf("127.0.0.1:%d.%d", port+1, port))
	t.Cleanup(f.srv.Stop)
	return f
}

func zzDialOption() grpc.DialOption {
	return grpc.WithTransportCredentials(insecure.NewCredentials())
}

func zzJoin(dir, name string) string {
	if dir == "" {
		dir = "/"
	}
	return path.Join(dir, name)
}

func (f *zzFiler) LookupDirectoryEntry(ctx context.Context, req *filer_pb.LookupDirectoryEntryRequest) (*filer_pb.LookupDirectoryEntryResponse, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	e, ok := f.entries[zzJoin(req.Directory, req.Name)]
	if !ok {
		return nil, status.Error(codes.NotFound, zzNotFound)
	}
	return &filer_pb.LookupDirectoryEntryResponse{Entry: proto.Clone(e).(*filer_pb.Entry)}, nil
}

func (f *zzFiler) ListEntries(req *filer_pb.ListEntriesRequest, stream filer_pb.SeaweedFiler_ListEntriesServer) error {
	f.mu.Lock()
	dir := path.Clean("/" + req.Directory)
	var names []string
	for p := range f.entries {
		if p != "/" && path.Dir(p) == dir {
			names = append(names, path.Base(p))
		}
	}
	sort.Strings(names)
	var out []*filer_pb.Entry
	for _, n := range names {
		if req.Prefix != "" && !strings.HasPrefix(n, req.Prefix) {
			continue
		}
		if req.StartFromFileName != "" {
			if n < req.StartFromFileName || (n == req.StartFromFileName && !req.InclusiveStartFrom) {
				continue
			}
		}
		out = append(out, proto.Clone(f.entries[zzJoin(dir, n)]).(*filer_pb.Entry))
		if req.Limit > 0 && uint32(len(out)) >= req.Limit {
			break
		}
	}
	f.mu.Unlock()
	for _, e := range out {
		if err := stream.Send(&filer_pb.ListEntriesResponse{Entry: e}); err != nil {
			return err
		}
	}
	return nil
}

func (f *zzFiler) ensureParentsLocked(dir string) {
	dir = path.Clean("/" + dir)
	for dir != "/" {
		if _, ok := f.entries[dir]; ok {
			return
		}
		f.entries[dir] = &filer_pb.Entry{Name: path.Base(dir), IsDirectory: true, Attributes: &filer_pb.FuseAttributes{}}
		dir = path.Dir(dir)
	}
}

func (f *zzFiler) CreateEntry(ctx context.Context, req *filer_pb.CreateEntryRequest) (*filer_pb.CreateEntryResponse, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	p := zzJoin(req.Directory, req.Entry.Name)
	if _, ok := f.entries[p]; ok && req.OExcl {
		return &filer_pb.CreateEntryResponse{Error: "entry already exists", ErrorCode: filer_pb.FilerError_ENTRY_ALREADY_EXISTS}, nil
	}
	f.ensureParentsLocked(req.Directory)
	f.entries[p] = proto.Clone(req.Entry).(*filer_pb.Entry)
	return &filer_pb.CreateEntryResponse{}, nil
}

func (f *zzFiler) UpdateEntry(ctx context.Context, req *filer_pb.UpdateEntryRequest) (*filer_pb.UpdateEntryResponse, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	p := zzJoin(req.Directory, req.Entry.Name)
	if _, ok := f.entries[p]; !ok {
		return nil, status.Error(codes.NotFound, zzNotFound)
	}
	f.entries[p] = proto.Clone(req.Entry).(*filer_pb.Entry)
	return &filer_pb.UpdateEntryResponse{}, nil
}

func (f *zzFiler) DeleteEntry(ctx context.Context, req *filer_pb.DeleteEntryRequest) (*filer_pb.DeleteEntryResponse, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	p := zzJoin(req.Directory, req.Name)
	if _, ok := f.entries[p]; !ok {
		return &filer_pb.DeleteEntryResponse{Error: zzNotFound}, nil
	}
	for k := range f.entries {
		if strings.HasPrefix(k, p+"/") {
			if !req.IsRecursive {
				return &filer_pb.DeleteEntryResponse{Error: "fail to delete non-empty folder: " + p}, nil
			}
			delete(f.entries, k)
		}
	}
	delete(f.entries, p)
	return &filer_pb.DeleteEntryResponse{}, nil
}

func (f *zzFiler) GetFilerConfiguration(ctx context.Context, req *filer_pb.GetFilerConfigurationRequest) (*filer_pb.GetFilerConfigurationResponse, error) {
	return &filer_pb.GetFilerConfigurationResponse{DirBuckets: "/buckets"}, nil
}

// --- test-side bookkeeping: seeds and inspects the store without product code ---

func (f *zzFiler) exists(p string) bool {
	f.mu.Lock()
	defer f.mu.Unlock()
	_, ok := f.entries[path.Clean(p)]
	return ok
}

func (f *zzFiler) extended(p, key string) ([]byte, bool) {
	f.mu.Lock()
	defer f.mu.Unlock()
	e, ok := f.entries[path.Clean(p)]
	if !ok || e.Extended == nil {
		return nil, false
	}
	v, ok := e.Extended[key]
	return v, ok
}

func (f *zzFiler) putDir(p string, ext map[string][]byte) {
	f.mu.Lock()
	defer f.mu.Unlock()
	p = path.Clean(p)
	f.ensureParentsLocked(path.Dir(p))
	now := time.Now().Unix()
	f.entries[p] = &filer_pb.Entry{Name: path.Base(p), IsDirectory: true, Extended: ext,
		Attributes: &filer_pb.FuseAttributes{Mtime: now, Crtime: now, FileMode: 0o20000000755}}
}

// seedTableBucket stores a table bucket owned by owner, as the S3 Tables API lays it out:
// a directory under /buckets marked as a table bucket, with JSON metadata and an
// optional bucket policy.
func (f *zzFiler) seedTableBucket(name, owner, policy string) {
	md, _ := json.Marshal(map[string]interface{}{
		"name": name, "createdAt": time.Now().UTC().Format(time.RFC3339Nano), "ownerAccountId": owner,
	})
	ext := map[string][]byte{"s3tables.tableBucket": []byte("true"), "s3tables.metadata": md}
	if policy != "" {
		ext["s3tables.policy"] = []byte(policy)
	}
	f.putDir("/buckets/"+name, ext)
}

// seedNamespace stores a namespace in a table bucket.
func (f *zzFiler) seedNamespace(bucket, ns, owner string) {
	md, _ := json.Marshal(map[string]interface{}{
		"namespace": []string{ns}, "createdAt": time.Now().UTC().Format(time.RFC3339Nano), "ownerAccountId": owner,
	})
	f.putDir("/buckets/"+bucket+"/"+ns, map[string][]byte{"s3tables.metadata": md})
}

func (f *zzFiler) isTableBucket(name string) bool {
	_, ok := f.extended("/buckets/"+name, "s3tables.tableBucket")
	return ok
}

func (f *zzFiler) hasNamespace(bucket, ns string) bool {
	_, ok := f.extended("/buckets/"+bucket+"/"+ns, "s3tables.metadata")
	return ok
}

func (f *zzFiler) bucketOwner(name string) string {
	md, ok := f.extended("/buckets/"+name, "s3tables.metadata")
	if !ok {
		return ""
	}
	var m struct {
		Owner string `json:"ownerAccountId"`
	}
	_ = json.Unmarshal(md, &m)
	return m.Owner
}

func (f *zzFiler) bucketPolicy(name string) string {
	v, _ := f.extended("/buckets/"+name, "s3tables.policy")
	return string(v)
}

// WithFilerClient lets tests hand this filer to APIs that take a FilerClient.
func (f *zzFiler) WithFilerClient(streamingMode bool, fn func(client filer_pb.SeaweedFilerClient) error) error {
	conn, err := grpc.NewClient(f.addr.ToGrpcAddress(), zzDialOption())
	if err != nil {
		return err
	}
	defer conn.Close()
	return fn(filer_pb.NewSeaweedFilerClient(conn))
}
