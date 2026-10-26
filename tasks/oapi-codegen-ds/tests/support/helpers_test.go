package vtesting

import (
	"encoding/json"
	"go/ast"
	"go/parser"
	"go/token"
	"strconv"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"

	"github.com/oapi-codegen/oapi-codegen/v2/pkg/codegen"
)

// injectSentinel is the identifier a specification tries to smuggle in as
// real generated Go code. It must never appear as an identifier in the
// generated file: legitimate escaping keeps it inside a string literal or a
// comment, where it is data, not code.
const injectSentinel = "OapiCodegenInjectedPwned"

func baseSpec() map[string]any {
	return map[string]any{
		"openapi": "3.0.3",
		"info":    map[string]any{"title": "Sample API", "version": "1.0.0"},
		"paths":   map[string]any{},
	}
}

func modelsOnly() codegen.Configuration {
	return codegen.Configuration{
		PackageName:   "api",
		Generate:      codegen.GenerateOptions{Models: true},
		OutputOptions: codegen.OutputOptions{SkipPrune: true},
	}
}

func serverURLs() codegen.Configuration {
	return codegen.Configuration{
		PackageName:   "api",
		Generate:      codegen.GenerateOptions{Models: true, ServerURLs: true},
		OutputOptions: codegen.OutputOptions{SkipPrune: true},
	}
}

func clientAndModels() codegen.Configuration {
	return codegen.Configuration{
		PackageName:   "api",
		Generate:      codegen.GenerateOptions{Models: true, Client: true},
		OutputOptions: codegen.OutputOptions{SkipPrune: true},
	}
}

// generate drives the library entry point the command-line tool uses.
func generate(t *testing.T, spec map[string]any, opts codegen.Configuration) (string, error) {
	t.Helper()
	raw, err := json.Marshal(spec)
	if err != nil {
		t.Fatalf("could not encode the test specification: %v", err)
	}
	doc, err := openapi3.NewLoader().LoadFromData(raw)
	if err != nil {
		t.Fatalf("could not load the test specification: %v", err)
	}
	return codegen.Generate(doc, opts)
}

func parseGenerated(t *testing.T, src string) *ast.File {
	t.Helper()
	f, err := parser.ParseFile(token.NewFileSet(), "generated.go", src, parser.ParseComments)
	if err != nil {
		t.Fatalf("generated output is not a valid Go file: %v", err)
	}
	return f
}

// assertNoInjection requires that generating src either refuses the document
// (an error) or yields a valid Go file in which the sentinel is not an
// identifier anywhere. A refusal is a clean outcome; a file that parses but
// declares the sentinel is the injected-code outcome the property forbids.
func assertNoInjection(t *testing.T, spec map[string]any, opts codegen.Configuration) {
	t.Helper()
	out, err := generate(t, spec, opts)
	if err != nil {
		return
	}
	f := parseGenerated(t, out)
	bad := false
	ast.Inspect(f, func(n ast.Node) bool {
		if id, ok := n.(*ast.Ident); ok && id.Name == injectSentinel {
			bad = true
		}
		return true
	})
	if bad {
		t.Fatalf("specification text became a generated Go identifier %q:\n%s", injectSentinel, out)
	}
}

// constValues decodes every string constant declared at file scope in the
// generated source, keyed by the constant's name.
func constValues(t *testing.T, f *ast.File) map[string]string {
	t.Helper()
	out := map[string]string{}
	for _, decl := range f.Decls {
		gd, ok := decl.(*ast.GenDecl)
		if !ok || gd.Tok != token.CONST {
			continue
		}
		for _, spec := range gd.Specs {
			vs, ok := spec.(*ast.ValueSpec)
			if !ok {
				continue
			}
			for i, name := range vs.Names {
				if i >= len(vs.Values) {
					continue
				}
				lit, ok := vs.Values[i].(*ast.BasicLit)
				if !ok || lit.Kind != token.STRING {
					continue
				}
				val, err := strconv.Unquote(lit.Value)
				if err != nil {
					continue
				}
				out[name.Name] = val
			}
		}
	}
	return out
}
