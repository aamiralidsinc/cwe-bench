<!-- label=GHSA-vrcc-3ch7-hppw hash=1b834ea3fd -->
# SYSTEM
You are a Principal Software Quality Assurance (QA) and Defensive Benchmark Architect on the maintainer side of an evaluation platform. We evaluate whether autonomous AI coding agents can correctly REPAIR real-world vulnerabilities (CVE/GHSA) that have already been fixed upstream in open-source projects.

You are provided with:
1. The historical human fix (the "reference patch")
2. The vulnerable codebase at the pre-patch commit
3. Repository maps, manifests, and test fixtures

Your responsibility is to author:
(1) `instruction.md`: A realistic, fair defect report filed by an enterprise user or security auditor.
(2) `hidden_tests.py`: A black-box pytest regression suite checking security enforcement and functional preservation.
(3) Three validation check-patches (shallow, removal, alternative) to prove the test suite accurately distinguishes good repairs from bad ones.

Operational Principles:
- Purely Defensive: All tests offline, inside an isolated container, using harmless sentinels. Tests only assert that invalid/unauthorized input is safely rejected and legitimate operations execute cleanly.
- Strict Fairness: A task is an exam of model intelligence, NOT a guessing game. Every legitimate use the functional suite tests must be an ordinary use of a FEATURE the report names as "must keep working" (name features, not test values).
- Zero Leakage: The agent must discover the faulty code and every place it lives. Never disclose file names, function names, the hidden place(s), or the scope of the bug ("every provider", "on every route").

# REQUEST
# Defect & Vulnerability Metadata
- OSV ID: GHSA-vrcc-3ch7-hppw
- CVE: CVE-2026-100353
- CWE: CWE-476
- Ecosystem / Package: Go / github.com/getkin/kin-openapi
- Repository: https://github.com/getkin/kin-openapi
- Official Summary: kin-openapi: Incomplete Fix for GHSA-p6wj-qrr4-pgh5: Three Unpatched nil-Items Panic Paths in openapi3filter

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/go.sum b/go.sum
index 9949c5d6c724269fe7b6981b21e9ca2148a0ca22..afadd341fde20fd30cbfac6a1cd97957b9bef5d2 100644
--- a/go.sum
+++ b/go.sum
@@ -23,8 +23,8 @@ github.com/oasdiff/yaml3 v0.0.14 h1:aLJee3hxBK2H5wdXd9iPcIXb93Nty1Ge0pT171eHtkw=
 github.com/oasdiff/yaml3 v0.0.14/go.mod h1:csto2xfDjYccdUn/yw/bPjj/cYTdp6HtFA0J4TWG+gg=
 github.com/pmezard/go-difflib v1.0.0 h1:4DBwDE0NGyQoBHbLQYPwSUPoCMWR5BEzIk/f1lZbAQM=
 github.com/pmezard/go-difflib v1.0.0/go.mod h1:iKH77koFhYxTK1pcRnkKkqfTogsbg7gZNVY4sRDYZ/4=
-github.com/santhosh-tekuri/jsonschema/v6 v6.0.2 h1:KRzFb2m7YtdldCEkzs6KqmJw4nqEVZGK7IN2kJkjTuQ=
-github.com/santhosh-tekuri/jsonschema/v6 v6.0.2/go.mod h1:JXeL+ps8p7/KNMjDQk3TCwPpBy0wYklyWTfbkIzdIFU=
+github.com/santhosh-tekuri/jsonschema/v6 v6.0.3 h1:1EYB5IzjZawrrnELUi78f9fPu57HuXjmddZPjrls/28=
+github.com/santhosh-tekuri/jsonschema/v6 v6.0.3/go.mod h1:JXeL+ps8p7/KNMjDQk3TCwPpBy0wYklyWTfbkIzdIFU=
 github.com/stretchr/testify v1.9.0 h1:HtqpIVDClZ4nwg75+f6Lvsy/wHu+3BoSGCbBAcpTsTg=
 github.com/stretchr/testify v1.9.0/go.mod h1:r2ic/lqez/lEtzL7wO/rwa5dbSLXVDPFyf8C91i36aY=
 golang.org/x/text v0.14.0 h1:ScX5w1eTa3QqT8oi6+ziP7dTV1S2+ALU0bI+0zXKWiQ=
diff --git a/openapi2conv/openapi2_conv.go b/openapi2conv/openapi2_conv.go
index 4181619c8b98761dc37b368c993b7b04bbd665ff..c5466523b1a42ff54d97179df0241a7776cc0cd6 100644
--- a/openapi2conv/openapi2_conv.go
+++ b/openapi2conv/openapi2_conv.go
@@ -5,6 +5,7 @@ import (
 	"errors"
 	"fmt"
 	"maps"
+	"net/http"
 	"net/url"
 	"slices"
 	"strings"
@@ -715,6 +716,9 @@ func FromV3(doc3 *openapi3.T) (*openapi2.T, error) {
 			if operation == nil {
 				continue
 			}
+			if err := checkV2Method(method); err != nil {
+				return nil, fmt.Errorf("path %q: %w", path, err)
+			}
 			doc2Operation, err := FromV3Operation(doc3, operation)
 			if err != nil {
 				return nil, err
@@ -978,11 +982,37 @@ func FromV3SecurityRequirements(requirements openapi3.SecurityRequirements) open
 	return result
 }
 
+// openapi2Methods are the HTTP methods Swagger 2.0's Path Item Object is able
+// to express. Anything else - the OpenAPI 3.2 QUERY field, CONNECT, TRACE, or a
+// custom method held in additionalOperations - has no v2 counterpart.
+var openapi2Methods = map[string]struct{}{
+	http.MethodDelete:  {},
+	http.MethodGet:     {},
+	http.MethodHead:    {},
+	http.MethodOptions: {},
+	http.MethodPatch:   {},
+	http.MethodPost:    {},
+	http.MethodPut:     {},
+}
+
+// checkV2Method reports whether an operation registered under method can be
+// carried over to a Swagger 2.0 document. Calling openapi2's SetOperation with
+// an unsupported method panics, so callers must guard with this first.
+func checkV2Method(method string) error {
+	if _, ok := openapi2Methods[method]; !ok {
+		return fmt.Errorf("unsupported HTTP method %q: it cannot be expressed in OpenAPI 2.0 (Swagger)", method)
+	}
+	return nil
+}
+
 func FromV3PathItem(doc3 *openapi3.T, pathItem *openapi3.PathItem) (*openapi2.PathItem, error) {
 	result := &openapi2.PathItem{
 		Extensions: stripNonExtensions(pathItem.Extensions),
 	}
 	for method, operation := range pathItem.Operations() {
+		if err := checkV2Method(method); err != nil {
+			return nil, err
+		}
 		r, err := FromV3Operation(doc3, operation)
 		if err != nil {
 			return nil, err
diff --git a/openapi3/internalize_refs.go b/openapi3/internalize_refs.go
index fe8b379ebde937b8906771056950e5827b5f0982..3dd99aca7a49f3cb678751dd48c4c26e7c3beff3 100644
--- a/openapi3/internalize_refs.go
+++ b/openapi3/internalize_refs.go
@@ -351,6 +351,13 @@ func (doc *T) derefSchema(s *Schema, refNameResolver RefNameResolver, parentIsEx
 		for _, k := range componentNames(s.Discriminator.Mapping) {
 			mapRef := s.Discriminator.Mapping[k]
 			s2 := (*SchemaRef)(&mapRef)
+			// The mapping value may be a plain schema name rather than a
+			// reference, and a reference the loader could not follow was left
+			// as written. Neither has a resolved path, so neither can be named
+			// by the resolver: leave them exactly as they are.
+			if s2.RefPath() == nil {
+				continue
+			}
 			isExternal := doc.addSchemaToSpec(s2, refNameResolver, parentIsExternal)
 			doc.derefSchema(s2.Value, refNameResolver, isExternal || parentIsExternal)
 			s.Discriminator.Mapping[k] = MappingRef(*s2)
diff --git a/openapi3/loader.go b/openapi3/loader.go
index 2f2480c071394ea504b3e867d1893f052fe967a7..77060068f5c6e00e6ed4611ee6abd0cabe899e36 100644
--- a/openapi3/loader.go
+++ b/openapi3/loader.go
@@ -149,8 +149,26 @@ func (loader *Loader) loadSingleElementFromURI(ref string, rootPath *url.URL, el
 
 // rememberOriginTree retains doc's origin tree for attachOriginToResolved.
 // tree is nil when IncludeOrigin is off or the data took the json path.
+//
+// The tree is kept only for a document a $ref can reach into untyped, which is
+// what attachOriginToResolved exists to re-origin. In practice that means a
+// file of shared fragments, whose top level is the fragment name itself rather
+// than the fields of an OpenAPI Object:
+//
+//	User:            # a $ref to "./schemas.yaml#/User" lands here, untyped
+//	  type: object
+//
+// Anything OpenAPI defines a field for resolves through typed structures and
+// keeps its origins on the way, so its tree could never be read. That includes
+// a referenced document that is itself an OpenAPI Object: a $ref to
+// "#/components/schemas/User" needs no tree. (A top-level x- extension is
+// undefined by the same rule, so a document carrying one keeps its tree too,
+// whether or not anything ever points at it.)
+//
+// Worth the condition: on a 22 MB spec the retained tree was a third of
+// everything the loader held.
 func (loader *Loader) rememberOriginTree(doc *T, tree *originTree) {
-	if tree == nil {
+	if tree == nil || len(doc.Extensions) == 0 {
 		return
 	}
 	if loader.originTrees == nil {
@@ -452,10 +470,12 @@ func (loader *Loader) resolveComponent(doc *T, ref string, path *url.URL, resolv
 			// Special case due to multijson
 			case *SchemaRef:
 				if pathPart == "additionalProperties" {
-					if ap := c.Value.AdditionalProperties.Has; ap != nil {
-						cursor = *ap
-					} else {
-						cursor = c.Value.AdditionalProperties.Schema
+					if s := c.Value; s != nil {
+						if ap := s.AdditionalProperties.Has; ap != nil {
+							cursor = *ap
+						} else {
+							cursor = s.AdditionalProperties.Schema
+						}
 					}
 					attempted = true
 				}
@@ -1116,19 +1136,25 @@ func (loader *Loader) resolveSchemaRef(doc *T, component *SchemaRef, documentPat
 	}
 	// Discriminator mapping refs are a special case since they are not full
 	// ref objects but are plain strings that reference schema objects.
-	// Only resolve refs that look like external references (contain a path).
-	// Plain schema names like "Dog" or internal refs like "#/components/schemas/Dog"
-	// don't need to be resolved by the loader.
+	// Plain schema names like "Dog" are not references and are left alone.
 	if value.Discriminator != nil {
+		inExternalDoc := documentPath != nil && documentPath.Path != "" && documentPath.Path != loader.rootLocation
 		for _, k := range componentNames(value.Discriminator.Mapping) {
 			v := value.Discriminator.Mapping[k]
-			// Only resolve if it looks like an external ref (contains path separator)
-			if strings.Contains(v.Ref, "/") && !strings.HasPrefix(v.Ref, "#") {
-				if err := loader.resolveSchemaRef(doc, (*SchemaRef)(&v), documentPath, visited); err != nil {
-					return err
-				}
-				value.Discriminator.Mapping[k] = v
+			if !strings.Contains(v.Ref, "/") {
+				continue
+			}
+			// A document-local mapping needs resolving only when it lives in
+			// another document, because InternalizeRefs then has to rewrite it
+			// against that document. One in the root document is already
+			// written against the document it will end up in.
+			if strings.HasPrefix(v.Ref, "#") && !inExternalDoc {
+				continue
+			}
+			if err := loader.resolveSchemaRef(doc, (*SchemaRef)(&v), documentPath, visited); err != nil {
+				return err
 			}
+			value.Discriminator.Mapping[k] = v
 		}
 	}
 
diff --git a/openapi3/origin.go b/openapi3/origin.go
index 75e1e70ad19e8f01d106c0d3339facc9b702e93a..1379a7c7607a97b3af503959096f052f9784655f 100644
--- a/openapi3/origin.go
+++ b/openapi3/origin.go
@@ -1,8 +1,9 @@
 package openapi3
 
 import (
+	"encoding/json"
 	"reflect"
-	"sort"
+	"slices"
 	"strings"
 
 	"github.com/oasdiff/yaml"
@@ -12,14 +13,86 @@ var originPtrType = reflect.TypeFor[*Origin]()
 
 // Origin contains the origin of a collection.
 // Key is the location of the collection itself.
-// Fields is a map of the location of each scalar field in the collection.
+// Fields holds the location of each scalar field in the collection.
 // Sequences is a map of the location of each item in sequence-valued fields.
+//
+// Sequences stays a map although Fields is a slice, which is deliberate.
+// FieldLocations drops the map because Location.Name already carries the key,
+// so the map was storing information the value repeated. Here Location.Name
+// holds the *item's* value (an enum member, a required property) while the key
+// is the *field's* name ("enum", "required", "tags"), so a slice would need a
+// wrapper type invented to hold it. The memory argument is also much weaker:
+// only a collection with a sequence-valued field allocates one at all, which
+// measured at 5% of collections on a large spec, and a nil map is free.
 type Origin struct {
 	Key       *Location             `json:"key,omitempty" yaml:"key,omitempty"`
-	Fields    map[string]Location   `json:"fields,omitempty" yaml:"fields,omitempty"`
+	Fields    FieldLocations        `json:"fields,omitempty" yaml:"fields,omitempty"`
 	Sequences map[string][]Location `json:"sequences,omitempty" yaml:"sequences,omitempty"`
 }
 
+// FieldLocations holds the locations of a collection's scalar fields, in the
+// order they appear in the document.
+//
+// It is a slice rather than a map[string]Location because a collection carries
+// only a handful of fields, while a Go map allocates a whole bucket per
+// collection whatever it holds. On a large document that overhead dominated
+// the retained size of a parsed spec. Each Location already carries its Name,
+// so the lookup key costs nothing extra here.
+type FieldLocations []Location
+
+// Get returns the location of the named field, or the zero Location when the
+// field has none. Use Lookup to tell an absent field from a zero location.
+func (f FieldLocations) Get(name string) Location {
+	loc, _ := f.Lookup(name)
+	return loc
+}
+
+// Lookup returns the location of the named field and whether it was found.
+// The scan is linear: collections have few fields, and a linear scan over a
+// contiguous slice beats a map lookup at these sizes.
+//
+// Deliberately a hand-written loop rather than slices.IndexFunc: the closure
+// does not inline, so IndexFunc pays a call per element. Measured on 3/6/12
+// fields it is 5-100% slower on a hit and 2-3x slower on a miss, and misses
+// are the common case here (most fields carry no recorded location).
+func (f FieldLocations) Lookup(name string) (Location, bool) {
+	for i := range f {
+		if f[i].Name == name {
+			return f[i], true
+		}
+	}
+	return Location{}, false
+}
+
+// MarshalJSON keeps the serialized shape a name-keyed object, as it was when
+// this was a map, so the change is invisible to anything reading the output.
+func (f FieldLocations) MarshalJSON() ([]byte, error) {
+	m := make(map[string]Location, len(f))
+	for _, loc := range f {
+		m[loc.Name] = loc
+	}
+	return json.Marshal(m)
+}
+
+// UnmarshalJSON reads the name-keyed object written by MarshalJSON. Entries are
+// sorted by name, since a JSON object carries no order to restore.
+func (f *FieldLocations) UnmarshalJSON(data []byte) error {
+	var m map[string]Location
+	if err := json.Unmarshal(data, &m); err != nil {
+		return err
+	}
+	out := make(FieldLocations, 0, len(m))
+	for name, loc := range m {
+		if loc.Name == "" {
+			loc.Name = name
+		}
+		out = append(out, loc)
+	}
+	slices.SortFunc(out, func(a, b Location) int { return strings.Compare(a.Name, b.Name) })
+	*f = out
+	return nil
+}
+
 // Location is a struct that contains the location of a field.
 type Location struct {
 	File   string `json:"file,omitempty" yaml:"file,omitempty"`
@@ -61,17 +134,17 @@ func originFromSeq(s []any) *Origin {
 	nf := toInt(s[idx])
 	idx++
 	if nf > 0 && idx+nf*3 <= len(s) {
-		o.Fields = make(map[string]Location, nf)
+		o.Fields = make(FieldLocations, 0, nf)
 		for range nf {
 			fname, _ := s[idx].(string)
 			delta := toInt(s[idx+1])
 			col := toInt(s[idx+2])
-			o.Fields[fname] = Location{
+			o.Fields = append(o.Fields, Location{
 				File:   file,
 				Line:   keyLine + delta,
 				Column: col,
 				Name:   fname,
-			}
+			})
 			idx += 3
 		}
 	}
@@ -94,12 +167,12 @@ func originFromSeq(s []any) *Origin {
 			}
 			count := toInt(s[idx])
 			idx++
-			locs := make([]Location, count)
+			locs := make([]Location, 0, count)
 			for j := 0; j < count && idx+2 < len(s); j++ {
 				name, _ := s[idx].(string)
 				delta := toInt(s[idx+1])
 				col := toInt(s[idx+2])
-				locs[j] = Location{File: file, Line: keyLine + delta, Column: col, Name: name}
+				locs = append(locs, Location{File: file, Line: keyLine + delta, Column: col, Name: name})
 				idx += 3
 			}
 			o.Sequences[sname] = locs
@@ -148,10 +221,13 @@ func isScalarValuedMapField(v reflect.Value) bool {
 	return false
 }
 
-// recordMapKeyLocations copies the map-key locations from a scalar-valued map's
+// recordMapKeyLocations moves the map-key locations from a scalar-valued map's
 // own subtree onto parentOrigin.Sequences[field], so each key is addressable by
 // name (the same shape used for sequence items). It is a no-op when the child
 // carries no origin data. Keys are sorted for deterministic output.
+//
+// childOrigin is discarded here, and nothing else holds its Fields, so the
+// slice is sorted and handed over in place rather than copied.
 func recordMapKeyLocations(parentOrigin *Origin, field string, childTree *yaml.OriginTree) {
 	s, ok := childTree.Origin.([]any)
 	if !ok {
@@ -161,11 +237,8 @@ func recordMapKeyLocations(parentOrigin *Origin, field string, childTree *yaml.O
 	if childOrigin == nil || len(childOrigin.Fields) == 0 {
 		return
 	}
-	locs := make([]Location, 0, len(childOrigin.Fields))
-	for _, loc := range childOrigin.Fields {
-		locs = append(locs, loc)
-	}
-	sort.Slice(locs, func(i, j int) bool { return locs[i].Name < locs[j].Name })
+	locs := childOrigin.Fields
+	slices.SortFunc(locs, func(a, b Location) int { return strings.Compare(a.Name, b.Name) })
 	if parentOrigin.Sequences == nil {
 		parentOrigin.Sequences = make(map[string][]Location)
 	}
diff --git a/openapi3/path_item.go b/openapi3/path_item.go
index 701d9911ade37ab723d82b7055eaafb8cfca7c88..ecaa7a993a45d0446967d59d03bd8afb44429dea 100644
--- a/openapi3/path_item.go
+++ b/openapi3/path_item.go
@@ -3,9 +3,10 @@ package openapi3
 import (
 	"context"
 	"encoding/json"
-	"fmt"
 	"maps"
 	"net/http"
+	"regexp"
+	"strings"
 )
 
 // PathItem is specified by OpenAPI/Swagger standard version 3.
@@ -26,10 +27,47 @@ type PathItem struct {
 	Post        *Operation `json:"post,omitempty" yaml:"post,omitempty"`
 	Put         *Operation `json:"put,omitempty" yaml:"put,omitempty"`
 	Trace       *Operation `json:"trace,omitempty" yaml:"trace,omitempty"`
+	Query       *Operation `json:"query,omitempty" yaml:"query,omitempty"` // OpenAPI >=3.2
 	Servers     Servers    `json:"servers,omitempty" yaml:"servers,omitempty"`
 	Parameters  Parameters `json:"parameters,omitempty" yaml:"parameters,omitempty"`
+
+	// AdditionalOperations maps custom HTTP method names to operations.
+	// Keys are case-sensitive HTTP method tokens and must not duplicate
+	// the methods covered by the fixed fields above.
+	AdditionalOperations map[string]*Operation `json:"additionalOperations,omitempty" yaml:"additionalOperations,omitempty"` // OpenAPI >=3.2
 }
 
+// MethodQuery is the HTTP QUERY method, introduced as a fixed Path Item
+// Object field by OpenAPI 3.2. The net/http package has no constant for it.
+const MethodQuery = "QUERY"
+
+// fixedPathItemMethods are the HTTP methods that have a dedicated PathItem
+// field; they must not appear as AdditionalOperations keys.
+var fixedPathItemMethods = map[string]struct{}{
+	http.MethodConnect: {},
+	http.MethodDelete:  {},
+	http.MethodGet:     {},
+	http.MethodHead:    {},
+	http.MethodOptions: {},
+	http.MethodPatch:   {},
+	http.MethodPost:    {},
+	http.MethodPut:     {},
+	http.MethodTrace:   {},
+	MethodQuery:        {},
+}
+
+// PathItemMethods returns the HTTP methods that have a dedicated Path Item
+// Object field, sorted. Any other method an operation is registered under
+// lives in AdditionalOperations, so a caller that treats the two groups
+// differently can tell them apart without listing the fixed methods itself.
+func PathItemMethods() []string {
+	return componentNames(fixedPathItemMethods)
+}
+
+// httpTokenRe matches an RFC 9110 token, the grammar HTTP method names
+// must follow.
+var httpTokenRe = regexp.MustCompile("^[!#$%&'*+\\-.^_`|~0-9A-Za-z]+$")
+
 // MarshalJSON returns the JSON encoding of PathItem.
 func (pathItem PathItem) MarshalJSON() ([]byte, error) {
 	x, err := pathItem.MarshalYAML()
@@ -45,7 +83,7 @@ func (pathItem PathItem) MarshalYAML() (any, error) {
 		return Ref{Ref: ref}, nil
 	}
 
-	m := make(map[string]any, 13+len(pathItem.Extensions))
+	m := make(map[string]any, 15+len(pathItem.Extensions))
 	maps.Copy(m, pathItem.Extensions)
 	if x := pathItem.Summary; x != "" {
 		m["summary"] = x
@@ -80,6 +118,12 @@ func (pathItem PathItem) MarshalYAML() (any, error) {
 	if x := pathItem.Trace; x != nil {
 		m["trace"] = x
 	}
+	if x := pathItem.Query; x != nil {
+		m["query"] = x
+	}
+	if x := pathItem.AdditionalOperations; len(x) != 0 {
+		m["additionalOperations"] = x
+	}
 	if x := pathItem.Servers; len(x) != 0 {
 		m["servers"] = x
 	}
@@ -109,6 +153,8 @@ func (pathItem *PathItem) UnmarshalJSON(data []byte) error {
 	delete(x.Extensions, "post")
 	delete(x.Extensions, "put")
 	delete(x.Extensions, "trace")
+	delete(x.Extensions, "query")
+	delete(x.Extensions, "additionalOperations")
 	delete(x.Extensions, "servers")
 	delete(x.Extensions, "parameters")
 	if len(x.Extensions) == 0 {
@@ -118,8 +164,50 @@ func (pathItem *PathItem) UnmarshalJSON(data []byte) error {
 	return nil
 }
 
-func (pathItem *PathItem) Operations() map[string]*Operation {
-	operations := make(map[string]*Operation)
+// operationEntry pairs an operation with the method it is registered under
+// and the JSON pointer suffix that addresses it inside a PathItem.
+type operationEntry struct {
+	method    string
+	operation *Operation
+	// pointerSuffix is "/get" for a fixed field and
+	// "/additionalOperations/COPY" for a custom method.
+	pointerSuffix string
+}
+
+// operationEntries returns pathItem's operations in a deterministic order
+// (fixed fields first, then AdditionalOperations, each sorted by method),
+// paired with the JSON pointer suffix addressing them. Custom methods
+// shadowed by a fixed field are skipped, matching Operations().
+func (pathItem *PathItem) operationEntries() []operationEntry {
+	fixed := pathItem.fixedOperations()
+	entries := make([]operationEntry, 0, len(fixed)+len(pathItem.AdditionalOperations))
+	for _, method := range componentNames(fixed) {
+		entries = append(entries, operationEntry{
+			method:        method,
+			operation:     fixed[method],
+			pointerSuffix: "/" + strings.ToLower(method),
+		})
+	}
+	for _, method := range componentNames(pathItem.AdditionalOperations) {
+		operation := pathItem.AdditionalOperations[method]
+		if operation == nil {
+			continue
+		}
+		if _, ok := fixed[method]; ok {
+			continue
+		}
+		entries = append(entries, operationEntry{
+			method:        method,
+			operation:     operation,
+			pointerSuffix: "/additionalOperations/" + escapeRefString(method),
+		})
+	}
+	return entries
+}
+
+// fixedOperations returns the operations held by PathItem's fixed fields.
+func (pathItem *PathItem) fixedOperations() map[string]*Operation {
+	operations := make(map[string]*Operation, len(fixedPathItemMethods))
 	if v := pathItem.Connect; v != nil {
 		operations[http.MethodConnect] = v
 	}
@@ -147,6 +235,27 @@ func (pathItem *PathItem) Operations() map[string]*Operation {
 	if v := pathItem.Trace; v != nil {
 		operations[http.MethodTrace] = v
 	}
+	if v := pathItem.Query; v != nil {
+		operations[MethodQuery] = v
+	}
+	return operations
+}
+
+// Operations returns pathItem's operations keyed by HTTP method, including
+// the OpenAPI 3.2 QUERY field and any AdditionalOperations. When an
+// AdditionalOperations key collides with a fixed field, the fixed field
+// wins (Validate reports the duplicate separately).
+func (pathItem *PathItem) Operations() map[string]*Operation {
+	operations := pathItem.fixedOperations()
+	for method, operation := range pathItem.AdditionalOperations {
+		if operation == nil {
+			continue
+		}
+		if _, ok := operations[method]; ok {
+			continue
+		}
+		operations[method] = operation
+	}
 	return operations
 }
 
@@ -170,8 +279,10 @@ func (pathItem *PathItem) GetOperation(method string) *Operation {
 		return pathItem.Put
 	case http.MethodTrace:
 		return pathItem.Trace
+	case MethodQuery:
+		return pathItem.Query
 	default:
-		panic(fmt.Errorf("unsupported HTTP method %q", method))
+		return pathItem.AdditionalOperations[method]
 	}
 }
 
@@ -195,8 +306,18 @@ func (pathItem *PathItem) SetOperation(method string, operation *Operation) {
 		pathItem.Put = operation
 	case http.MethodTrace:
 		pathItem.Trace = operation
+	case MethodQuery:
+		pathItem.Query = operation
 	default:
-		panic(fmt.Errorf("unsupported HTTP method %q", method))
+		// Custom (OpenAPI >=3.2) methods live in AdditionalOperations.
+		if operation == nil {
+			delete(pathItem.AdditionalOperations, method)
+			return
+		}
+		if pathItem.AdditionalOperations == nil {
+			pathItem.AdditionalOperations = make(map[string]*Operation, 1)
+		}
+		pathItem.AdditionalOperations[method] = operation
 	}
 }
 
@@ -205,6 +326,33 @@ func (pathItem *PathItem) Validate(ctx context.Context, opts ...ValidationOption
 	ctx = WithValidationOptions(ctx, opts...)
 	me := newErrCollector(ctx)
 
+	if !getValidationOptions(ctx).isOpenAPI32OrLater {
+		if pathItem.Query != nil {
+			if err := me.emit(errFieldFor32Plus("query", pathItem.Origin)); err != nil {
+				return err
+			}
+		}
+		if len(pathItem.AdditionalOperations) != 0 {
+			if err := me.emit(errFieldFor32Plus("additionalOperations", pathItem.Origin)); err != nil {
+				return err
+			}
+		}
+	}
+
+	for _, method := range componentNames(pathItem.AdditionalOperations) {
+		if _, ok := fixedPathItemMethods[method]; ok {
+			if err := me.emit(newAdditionalOperationsDuplicateMethod(method, pathItem.Origin)); err != nil {
+				return err
+			}
+			continue
+		}
+		if !httpTokenRe.MatchString(method) {
+			if err := me.emit(newAdditionalOperationsInvalidMethod(method, pathItem.Origin)); err != nil {
+				return err
+			}
+		}
+	}
+
 	operations := pathItem.Operations()
 
 	for _, method := range componentNames(operations) {
@@ -239,6 +387,8 @@ func (pathItem *PathItem) isEmpty() bool {
 		pathItem.Post == nil &&
 		pathItem.Put == nil &&
 		pathItem.Trace == nil &&
+		pathItem.Query == nil &&
+		len(pathItem.AdditionalOperations) == 0 &&
 		len(pathItem.Servers) == 0 &&
 		len(pathItem.Parameters) == 0
 }
diff --git a/openapi3/schema.go b/openapi3/schema.go
index 4388a39813c001ff95eca71ce29aa53d72023371..ff86808a63af1abec21cd4f90f9a7f738365881f 100644
--- a/openapi3/schema.go
+++ b/openapi3/schema.go
@@ -1949,6 +1949,15 @@ func (schema *Schema) VisitJSON(value any, opts ...SchemaValidationOption) error
 }
 
 func (schema *Schema) visitJSON(settings *schemaValidationSettings, value any) (err error) {
+	if settings.visitedSchemas == nil {
+		settings.visitedSchemas = make(map[*Schema]struct{})
+	}
+	if _, visited := settings.visitedSchemas[schema]; visited {
+		return nil
+	}
+	settings.visitedSchemas[schema] = struct{}{}
+	defer delete(settings.visitedSchemas, schema)
+
 	switch value := value.(type) {
 	case nil:
 		// Don't use VisitJSONNull, as we still want to reach 'visitXOFOperations', since
@@ -2361,6 +2370,80 @@ func (schema *Schema) visitJSONBoolean(settings *schemaValidationSettings, value
 	return
 }
 
+// multipleOfSlack bounds, as a negative power of two, how far a value may sit
+// from the nearest multiple and still count as one, measured relative to the
+// value itself. A float64 carries about 2^-53 of relative error, so this is a
+// couple of units in the last place: enough to absorb the error a caller's own
+// arithmetic introduced, small enough that a genuine remainder never fits.
+//
+// The window must be measured against the value and not against the quotient.
+// A quotient-relative window grows without bound, and once value/multipleOf
+// reaches 2^49 it exceeds one half, at which point every number validates.
+const multipleOfSlack = 51
+
+// multipleOfFailure reports whether value satisfies multipleOf, and the reason
+// when it does not.
+//
+// The comparison runs on exact rationals rather than on decimals formatted at a
+// fixed precision. A fixed precision is only correct inside a narrow magnitude
+// band: above it the formatting emits binary representation error and rejects
+// valid values, and below it every operand formats to zero, which both accepts
+// any value and divides by zero.
+func multipleOfFailure(value, multipleOf float64) (string, bool) {
+	// A non-finite multipleOf cannot be reported: SchemaError renders the whole
+	// schema as JSON and NaN has no JSON encoding, so building that error would
+	// panic instead of describing the problem. Treat it as no constraint, which
+	// at least replaces the division-by-zero panic the fixed-precision
+	// formatting produced here.
+	if math.IsNaN(multipleOf) || math.IsInf(multipleOf, 0) {
+		return "", true
+	}
+	// JSON Schema requires multipleOf to be strictly greater than zero. Without
+	// this guard a zero or negative value either divided by zero or accepted
+	// every number.
+	if multipleOf <= 0 {
+		return fmt.Sprintf("multipleOf must be greater than zero, got %g", multipleOf), false
+	}
+	// VisitJSON rejects a non-finite number before any keyword runs, but the
+	// exported VisitJSONNumber does not, so one can still reach this point.
+	// Reporting it here is out of scope: SchemaError marshals Value, and NaN has
+	// no JSON encoding, so the error would panic when rendered. Preserve the
+	// existing outcome and leave that entry point to a separate change.
+	if math.IsNaN(value) || math.IsInf(value, 0) {
+		return "", true
+	}
+	notAMultiple := fmt.Sprintf("number must be a multiple of %g", multipleOf)
+
+	exactValue := new(big.Rat).SetFloat64(value)
+	exactMultipleOf := new(big.Rat).SetFloat64(multipleOf)
+	quotient := new(big.Rat).Quo(exactValue, exactMultipleOf)
+	if quotient.IsInt() {
+		return "", true
+	}
+
+	// The quotient is not an integer, so floor and floor+1 bracket it. Both are
+	// computed through big.Int, which no quotient can overflow. Compare the two
+	// candidate multiples against the value itself rather than comparing the
+	// quotient against an integer, so the window stays tied to the value's own
+	// precision at every magnitude.
+	floor := new(big.Int).Div(quotient.Num(), quotient.Denom())
+	var distance *big.Rat
+	for _, k := range []*big.Int{floor, new(big.Int).Add(floor, big.NewInt(1))} {
+		gap := new(big.Rat).Sub(exactValue, new(big.Rat).Mul(new(big.Rat).SetInt(k), exactMultipleOf))
+		gap.Abs(gap)
+		if distance == nil || gap.Cmp(distance) < 0 {
+			distance = gap
+		}
+	}
+
+	slack := new(big.Rat).SetFrac(big.NewInt(1), new(big.Int).Lsh(big.NewInt(1), multipleOfSlack))
+	tolerance := new(big.Rat).Mul(new(big.Rat).Abs(exactValue), slack)
+	if distance.Cmp(tolerance) <= 0 {
+		return "", true
+	}
+	return notAMultiple, false
+}
+
 func (schema *Schema) VisitJSONNumber(value float64) error {
 	settings := newSchemaValidationSettings()
 	return schema.visitJSONNumber(settings, value)
@@ -2563,10 +2646,8 @@ func (schema *Schema) visitJSONNumber(settings *schemaValidationSettings, value
 	if v := schema.MultipleOf; v != nil {
 		// "A numeric instance is valid only if division by this keyword's
 		//    value results in an integer."
-		numRat, denRat := &big.Rat{}, &big.Rat{}
-		numRat.SetString(fmt.Sprintf("%.10f", value))
-		denRat.SetString(fmt.Sprintf("%.10f", *v))
-		if !(&big.Rat{}).Quo(numRat, denRat).IsInt() {
+		reason, ok := multipleOfFailure(value, *v)
+		if !ok {
 			if settings.failfast {
 				return errSchema
 			}
@@ -2574,7 +2655,7 @@ func (schema *Schema) visitJSONNumber(settings *schemaValidationSettings, value
 				Value:                 value,
 				Schema:                schema,
 				SchemaField:           "multipleOf",
-				Reason:                fmt.Sprintf("number must be a multiple of %g", *v),
+				Reason:                reason,
 				customizeMessageError: settings.customizeMessageError,
 			}
 			if !settings.multiError {
@@ -2663,7 +2744,7 @@ func (schema *Schema) visitJSONString(settings *schemaValidationSettings, value
 				me = append(me, err)
 			}
 		}
-		if !cp.MatchString(value) {
+		if cp != nil && !cp.MatchString(value) {
 			err := &SchemaError{
 				Value:                 value,
 				Schema:                schema,
@@ -2795,14 +2876,38 @@ func (schema *Schema) visitJSONArray(settings *schemaValidationSettings, value [
 		me = append(me, err)
 	}
 
-	// "items"
+	// "prefixItems": the schema at index i validates the item at index i.
+	// Positions the array does not reach are simply unconstrained.
+	for i, prefixItemRef := range schema.PrefixItems {
+		if i >= len(value) {
+			break
+		}
+		prefixItemSchema := prefixItemRef.Value
+		if prefixItemSchema == nil {
+			return newUnresolvedRef(prefixItemRef.Ref, prefixItemRef.Origin)
+		}
+		if err := prefixItemSchema.visitJSON(settings, value[i]); err != nil {
+			err = markSchemaErrorIndex(err, i)
+			if !settings.multiError {
+				return err
+			}
+			if itemMe, ok := err.(MultiError); ok {
+				me = append(me, itemMe...)
+			} else {
+				me = append(me, err)
+			}
+		}
+	}
+
+	// "items" applies to the positions prefixItems does not cover. Without
+	// prefixItems that is every position, which is the OAS 3.0 behaviour.
 	if itemSchemaRef := schema.Items; itemSchemaRef != nil {
 		itemSchema := itemSchemaRef.Value
 		if itemSchema == nil {
 			return newUnresolvedRef(itemSchemaRef.Ref, itemSchemaRef.Origin)
 		}
-		for i, item := range value {
-			if err := itemSchema.visitJSON(settings, item); err != nil {
+		for i := len(schema.PrefixItems); i < len(value); i++ {
+			if err := itemSchema.visitJSON(settings, value[i]); err != nil {
 				err = markSchemaErrorIndex(err, i)
 				if !settings.multiError {
 					return err
diff --git a/openapi3/schema_formats.go b/openapi3/schema_formats.go
index 5053510a3c6dde2256bfa0409df642e8eec79c90..dd8d2189c7b17d81d1af8967e4900bdda1079837 100644
--- a/openapi3/schema_formats.go
+++ b/openapi3/schema_formats.go
@@ -34,6 +34,11 @@ const (
 	// FormatOfStringForUUIDOfRFC4122 is an optional predefined format for UUID v1-v5 as specified by RFC4122
 	FormatOfStringForUUIDOfRFC4122 = `^(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|00000000-0000-0000-0000-000000000000)$`
 
+	// FormatOfStringForUUIDOfRFC9562 is an optional predefined format for UUID v1-v8 as specified by RFC9562,
+	// which obsoletes RFC4122. In addition to the versioned layout it also accepts the special Nil UUID
+	// (all zeroes) and Max UUID (all ones) defined in sections 5.9 and 5.10 of the RFC.
+	FormatOfStringForUUIDOfRFC9562 = `^(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|00000000-0000-0000-0000-000000000000|[fF]{8}-[fF]{4}-[fF]{4}-[fF]{4}-[fF]{12})$`
+
 	// FormatOfStringForEmail pattern catches only some suspiciously wrong-looking email addresses.
 	// Use DefineStringFormat(...) if you need something stricter.
 	FormatOfStringForEmail = `^[^@]+@[^@<>",\s]+$`
diff --git a/openapi3/schema_jsonschema_validator.go b/openapi3/schema_jsonschema_validator.go
index d610e535d2c7f2eb46cfa73ef6d21e6caec808dc..7d6a7613be6bc232adcb1ff28f9891756bfe021d 100644
--- a/openapi3/schema_jsonschema_validator.go
+++ b/openapi3/schema_jsonschema_validator.go
@@ -4,6 +4,7 @@ import (
 	"encoding/json"
 	"errors"
 	"fmt"
+	"math"
 	"strings"
 
 	"github.com/santhosh-tekuri/jsonschema/v6"
@@ -16,7 +17,7 @@ type jsonSchemaValidator struct {
 }
 
 // newJSONSchemaValidator creates a new validator using JSON Schema 2020-12
-func newJSONSchemaValidator(schema *Schema) (*jsonSchemaValidator, error) {
+func newJSONSchemaValidator(schema *Schema, settings *schemaValidationSettings) (*jsonSchemaValidator, error) {
 	// Convert OpenAPI Schema to JSON Schema format
 	schemaBytes, err := json.Marshal(schema)
 	if err != nil {
@@ -35,6 +36,9 @@ func newJSONSchemaValidator(schema *Schema) (*jsonSchemaValidator, error) {
 	compiler := jsonschema.NewCompiler()
 	compiler.DefaultDraft(jsonschema.Draft2020)
 
+	// Keep enforcing the formats the built-in validator enforces
+	registerFormatValidators(compiler, schemaMap, settings)
+
 	// Add the schema
 	schemaURL := "https://example.com/schema.json"
 	if err := compiler.AddResource(schemaURL, schemaMap); err != nil {
@@ -53,6 +57,88 @@ func newJSONSchemaValidator(schema *Schema) (*jsonSchemaValidator, error) {
 	}, nil
 }
 
+func registerFormatValidators(compiler *jsonschema.Compiler, schemaMap map[string]any, settings *schemaValidationSettings) {
+	formats := make(map[string]struct{})
+	collectFormats(schemaMap, formats)
+	if len(formats) == 0 {
+		return
+	}
+
+	for format := range formats {
+		compiler.RegisterFormat(&jsonschema.Format{
+			Name:     format,
+			Validate: formatValidator(format, settings),
+		})
+	}
+	compiler.AssertFormat() // has to be explicitly asserted
+}
+
+func collectFormats(node any, formats map[string]struct{}) {
+	switch node := node.(type) {
+	case map[string]any:
+		if format, ok := node["format"].(string); ok && format != "" {
+			formats[format] = struct{}{}
+		}
+		for _, value := range node {
+			collectFormats(value, formats)
+		}
+	case []any:
+		for _, value := range node {
+			collectFormats(value, formats)
+		}
+	}
+}
+
+func formatValidator(format string, settings *schemaValidationSettings) func(any) error {
+	return func(value any) error {
+		switch value := value.(type) {
+		case string:
+			f, ok := settings.stringFormats[format]
+			if !ok {
+				if f, ok = SchemaStringFormats[format]; !ok {
+					return nil
+				}
+			}
+			return f.Validate(value)
+		case json.Number:
+			if number, err := value.Float64(); err == nil {
+				return validateNumberFormat(format, settings, number)
+			}
+		case float64:
+			return validateNumberFormat(format, settings, value)
+		case float32:
+			return validateNumberFormat(format, settings, float64(value))
+		case int:
+			return validateNumberFormat(format, settings, float64(value))
+		case int32:
+			return validateNumberFormat(format, settings, float64(value))
+		case int64:
+			return validateNumberFormat(format, settings, float64(value))
+		}
+		return nil
+	}
+}
+
+func validateNumberFormat(format string, settings *schemaValidationSettings, value float64) error {
+	if value == math.Trunc(value) && !math.IsInf(value, 0) {
+		f, ok := settings.integerFormats[format]
+		if !ok {
+			f, ok = SchemaIntegerFormats[format]
+		}
+		if ok {
+			return f.Validate(int64(value))
+		}
+	}
+
+	f, ok := settings.numberFormats[format]
+	if !ok {
+		if f, ok = SchemaNumberFormats[format]; !ok {
+			return nil
+		}
+	}
+	return f.Validate(value)
+}
+
 // transformOpenAPIToJSONSchema converts OpenAPI 3.0/3.1 specific keywords to JSON Schema format
 func transformOpenAPIToJSONSchema(schema map[string]any) {
 	// Handle nullable - in OpenAPI 3.0, nullable is a boolean flag
@@ -202,7 +288,7 @@ func formatValidationError(verr *jsonschema.ValidationError, parentPath string)
 
 // useJSONSchema2020 validates using the JSON Schema 2020-12 validator
 func (schema *Schema) useJSONSchema2020(settings *schemaValidationSettings, value any) error {
-	validator, err := newJSONSchemaValidator(schema)
+	validator, err := newJSONSchemaValidator(schema, settings)
 	if err != nil {
 		// Fall back to built-in validator if compilation fails
 		return schema.visitJSON(settings, value)
diff --git a/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Prediction_3_0_openapi_yaml__validate b/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Prediction_3_0_openapi_yaml__validate
deleted file mode 100644
index 4e74a92fc5cdc1604ffbb32f5a94b58cb8f91067..0000000000000000000000000000000000000000
--- a/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Prediction_3_0_openapi_yaml__validate
+++ /dev/null
@@ -1 +0,0 @@
-invalid paths: invalid path /{projectId}/detect/iterations/{publishedName}/image: invalid operation POST: invalid example: example Successful DetectImage request: Error at "/id": string doesn't match the format "uuid": string doesn't match pattern "^(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|00000000-0000-0000-0000-000000000000)$" | Error at "/project": string doesn't match the format "uuid": string doesn't match pattern "^(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|00000000-0000-0000-0000-000000000000)$"
diff --git a/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_0_openapi_yaml__validate b/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_0_openapi_yaml__validate
index 336b8c10043ca25f782a82220698635f70cf891e..6711c89f6aa1469d118fbdf5ae4d32a2ab4d50f8 100644
--- a/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_0_openapi_yaml__validate
+++ b/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_0_openapi_yaml__validate
@@ -1 +1,9 @@
-invalid paths: invalid path /projects/{projectId}/images/regions: invalid operation DELETE: invalid example: Successful DeleteImageRegions request: Error at "/0": string doesn't match the format "uuid": string doesn't match pattern "^(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|00000000-0000-0000-0000-000000000000)$"
+invalid paths: invalid path /projects/{projectId}/images/tagged/count: invalid operation GET: invalid example: example Successful GetTaggedImageCount request: value must be an integer
+Schema:
+  {
+    "format": "int32",
+    "type": "integer"
+  }
+
+Value:
+  "10"
diff --git a/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_1_openapi_yaml__validate b/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_1_openapi_yaml__validate
index 336b8c10043ca25f782a82220698635f70cf891e..0dbecd3646b3415f852fe46d0ebee1c4834becfe 100644
--- a/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_1_openapi_yaml__validate
+++ b/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_1_openapi_yaml__validate
@@ -1 +1,17 @@
-invalid paths: invalid path /projects/{projectId}/images/regions: invalid operation DELETE: invalid example: Successful DeleteImageRegions request: Error at "/0": string doesn't match the format "uuid": string doesn't match pattern "^(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|00000000-0000-0000-0000-000000000000)$"
+invalid paths: invalid path /projects/{projectId}/images/suggested: invalid operation POST: invalid example: example Successful QuerySuggestedImages request: Error at "/token/sortBy": value is not one of the allowed values ["UncertaintyAscending","UncertaintyDescending"]
+Schema:
+  {
+    "description": "OrderBy. Ordering mechanism for your results.",
+    "enum": [
+      "UncertaintyAscending",
+      "UncertaintyDescending"
+    ],
+    "type": "string",
+    "x-ms-enum": {
+      "modelAsString": true,
+      "name": "SortBy"
+    }
+  }
+
+Value:
+  "Newest"
diff --git a/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_2_openapi_yaml__validate b/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_2_openapi_yaml__validate
index 336b8c10043ca25f782a82220698635f70cf891e..0dbecd3646b3415f852fe46d0ebee1c4834becfe 100644
--- a/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_2_openapi_yaml__validate
+++ b/openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_2_openapi_yaml__validate
@@ -1 +1,17 @@
-invalid paths: invalid path /projects/{projectId}/images/regions: invalid operation DELETE: invalid example: Successful DeleteImageRegions request: Error at "/0": string doesn't match the format "uuid": string doesn't match pattern "^(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|00000000-0000-0000-0000-000000000000)$"
+invalid paths: invalid path /projects/{projectId}/images/suggested: invalid operation POST: invalid example: example Successful QuerySuggestedImages request: Error at "/token/sortBy": value is not one of the allowed values ["UncertaintyAscending","UncertaintyDescending"]
+Schema:
+  {
+    "description": "OrderBy. Ordering mechanism for your results.",
+    "enum": [
+      "UncertaintyAscending",
+      "UncertaintyDescending"
+    ],
+    "type": "string",
+    "x-ms-enum": {
+      "modelAsString": true,
+      "name": "SortBy"
+    }
+  }
+
+Value:
+  "Newest"
diff --git a/openapi3/testdata/apis_guru_openapi_directory/nexmo_com_voice_1_3_10_openapi_yaml__validate b/openapi3/testdata/apis_guru_openapi_directory/nexmo_com_voice_1_3_10_openapi_yaml__validate
index c7e5978827829f0ccc780ef72c9a12b621962d60..9840f7044c48c7ec18cf4c079dfe71c5dc3df4ea 100644
--- a/openapi3/testdata/apis_guru_openapi_directory/nexmo_com_voice_1_3_10_openapi_yaml__validate
+++ b/openapi3/testdata/apis_guru_openapi_directory/nexmo_com_voice_1_3_10_openapi_yaml__validate
@@ -1 +1,10 @@
-invalid components: schema "CreateCallResponse": invalid example: string doesn't match the format "uuid": string doesn't match pattern "^(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|00000000-0000-0000-0000-000000000000)$"
+invalid components: schema "DTMFRequest": invalid example: value must be a string
+Schema:
+  {
+    "description": "The digits to send",
+    "example": 1713,
+    "type": "string"
+  }
+
+Value:
+  1713
diff --git a/openapi3/testdata/discriminatorLocalMapping.yml.internalized.yml b/openapi3/testdata/discriminatorLocalMapping.yml.internalized.yml
new file mode 100644
index 0000000000000000000000000000000000000000..9f8c1b885d9c820bd6417c7be7fff368ffe1ce08
--- /dev/null
+++ b/openapi3/testdata/discriminatorLocalMapping.yml.internalized.yml
@@ -0,0 +1,45 @@
+{
+    "components": {
+        "schemas": {
+            "Cat": {
+                "properties": {
+                    "petType": {
+                        "type": "string"
+                    }
+                },
+                "type": "object"
+            },
+            "Dog": {
+                "properties": {
+                    "petType": {
+                        "type": "string"
+                    }
+                },
+                "type": "object"
+            },
+            "Pet": {
+                "discriminator": {
+                    "mapping": {
+                        "cat": "#/components/schemas/Cat",
+                        "dog": "Dog"
+                    },
+                    "propertyName": "petType"
+                },
+                "oneOf": [
+                    {
+                        "$ref": "#/components/schemas/Dog"
+                    },
+                    {
+                        "$ref": "#/components/schemas/Cat"
+                    }
+                ]
+            }
+        }
+    },
+    "info": {
+        "title": "local discriminator mappings",
+        "version": "1.0.0"
+    },
+    "openapi": "3.1.0",
+    "paths": {}
+}
diff --git a/openapi3/testdata/issue1205/ext.yml b/openapi3/testdata/issue1205/ext.yml
new file mode 100644
index 0000000000000000000000000000000000000000..8c0f71555aa44ec131510098ef88bc62f3602d1e
--- /dev/null
+++ b/openapi3/testdata/issue1205/ext.yml
@@ -0,0 +1,24 @@
+openapi: 3.1.0
+info:
+  title: recursive discriminated union
+  version: 1.0.0
+paths: {}
+components:
+  schemas:
+    Comp:
+      oneOf:
+        - $ref: '#/components/schemas/Container'
+      discriminator:
+        propertyName: type
+        mapping:
+          container: '#/components/schemas/Container'
+    Container:
+      type: object
+      required: [type]
+      properties:
+        type:
+          type: string
+        children:
+          type: array
+          items:
+            $ref: '#/components/schemas/Comp'
\ No newline at end of file
diff --git a/openapi3/testdata/issue1205/mutual.yml.internalized.yml b/openapi3/testdata/issue1205/mutual.yml.internalized.yml
new file mode 100644
index 0000000000000000000000000000000000000000..df4972bfc4d530afe0c1909e20ed951731ba7f70
--- /dev/null
+++ b/openapi3/testdata/issue1205/mutual.yml.internalized.yml
@@ -0,0 +1,85 @@
+{
+    "components": {
+        "schemas": {
+            "Root": {
+                "properties": {
+                    "a": {
+                        "$ref": "#/components/schemas/mutual-a_AUnion"
+                    },
+                    "b": {
+                        "$ref": "#/components/schemas/mutual-b_BUnion"
+                    }
+                },
+                "type": "object"
+            },
+            "mutual-a_ALeaf": {
+                "properties": {
+                    "kind": {
+                        "type": "string"
+                    },
+                    "over": {
+                        "$ref": "#/components/schemas/mutual-b_BUnion"
+                    },
+                    "self": {
+                        "$ref": "#/components/schemas/mutual-a_AUnion"
+                    }
+                },
+                "required": [
+                    "kind"
+                ],
+                "type": "object"
+            },
+            "mutual-a_AUnion": {
+                "discriminator": {
+                    "mapping": {
+                        "across": "#/components/schemas/mutual-b_BUnion",
+                        "aleaf": "#/components/schemas/mutual-a_ALeaf"
+                    },
+                    "propertyName": "kind"
+                },
+                "oneOf": [
+                    {
+                        "$ref": "#/components/schemas/mutual-a_ALeaf"
+                    }
+                ]
+            },
+            "mutual-b_BLeaf": {
+                "properties": {
+                    "back": {
+                        "$ref": "#/components/schemas/mutual-a_AUnion"
+                    },
+                    "kind": {
+                        "type": "string"
+                    },
+                    "self": {
+                        "$ref": "#/components/schemas/mutual-b_BUnion"
+                    }
+                },
+                "required": [
+                    "kind"
+                ],
+                "type": "object"
+            },
+            "mutual-b_BUnion": {
+                "discriminator": {
+                    "mapping": {
+                        "across": "#/components/schemas/mutual-a_AUnion",
+                        "bleaf": "#/components/schemas/mutual-b_BLeaf"
+                    },
+                    "propertyName": "kind"
+                },
+                "oneOf": [
+                    {
+                        "$ref": "#/components/schemas/mutual-b_BLeaf"
+                    }
+                ]
+            }
+        }
+    },
+    "info": {
+        "title": "mutually recursive unions across documents",
+        "version": "1.0.0"
+    },
+    "openapi": "3.1.0",
+    "paths": {}
+}
diff --git a/openapi3/testdata/issue1205/openapi.yml.internalized.yml b/openapi3/testdata/issue1205/openapi.yml.internalized.yml
new file mode 100644
index 0000000000000000000000000000000000000000..f7b4d452264c5c4df77fb2a80a2055637b4d059b
--- /dev/null
+++ b/openapi3/testdata/issue1205/openapi.yml.internalized.yml
@@ -0,0 +1,50 @@
+{
+    "components": {
+        "schemas": {
+            "Probe": {
+                "properties": {
+                    "deep": {
+                        "$ref": "#/components/schemas/ext_Comp"
+                    }
+                },
+                "type": "object"
+            },
+            "ext_Comp": {
+                "discriminator": {
+                    "mapping": {
+                        "container": "#/components/schemas/ext_Container"
+                    },
+                    "propertyName": "type"
+                },
+                "oneOf": [
+                    {
+                        "$ref": "#/components/schemas/ext_Container"
+                    }
+                ]
+            },
+            "ext_Container": {
+                "properties": {
+                    "children": {
+                        "items": {
+                            "$ref": "#/components/schemas/ext_Comp"
+                        },
+                        "type": "array"
+                    },
+                    "type": {
+                        "type": "string"
+                    }
+                },
+                "required": [
+                    "type"
+                ],
+                "type": "object"
+            }
+        }
+    },
+    "info": {
+        "title": "external recursive discriminated union",
+        "version": "1.0.0"
+    },
+    "openapi": "3.1.0",
+    "paths": {}
+}
diff --git a/openapi3/validation_code.go b/openapi3/validation_code.go
index f2daa343fcf61ef0171382e3e79b8ec22b584788..6c4302b6072984ad6a824e0ce04e7503486d6aa6 100644
--- a/openapi3/validation_code.go
+++ b/openapi3/validation_code.go
@@ -28,6 +28,15 @@ type CodedError interface {
 	Code() string
 }
 
+func (e *AdditionalOperationsDuplicateMethodError) Code() string {
+	return "additional-operations-duplicate-method"
+}
+func (e *AdditionalOperationsFieldFor32Plus) Code() string {
+	return "additional-operations-field-for-3-2-plus"
+}
+func (e *AdditionalOperationsInvalidMethodError) Code() string {
+	return "additional-operations-invalid-method"
+}
 func (e *AnchorFieldFor31Plus) Code() string             { return "anchor-field-for-3-1-plus" }
 func (e *APIKeyInInvalidError) Code() string             { return "security-scheme-apikey-in-invalid" }
 func (e *APIKeySecuritySchemeNameRequired) Code() string { return "security-scheme-name-required" }
@@ -119,6 +128,7 @@ func (e *PatternPropertiesFieldFor31Plus) Code() string {
 }
 func (e *PrefixItemsFieldFor31Plus) Code() string   { return "prefix-items-field-for-3-1-plus" }
 func (e *PropertyNamesFieldFor31Plus) Code() string { return "property-names-field-for-3-1-plus" }
+func (e *QueryFieldFor32Plus) Code() string         { return "query-field-for-3-2-plus" }
 func (e *RequestBodyContentRequired) Code() string  { return "request-body-content-required" }
 func (e *ResponseDescriptionRequired) Code() string { return "response-description-required" }
 func (e *ResponsesNonEmptyRequired) Code() string   { return "responses-required" }
@@ -163,6 +173,9 @@ func ValidationErrorCodes() []string {
 }
 
 var validationErrorCodes = []string{
+	"additional-operations-duplicate-method",
+	"additional-operations-field-for-3-2-plus",
+	"additional-operations-invalid-method",
 	"additional-properties-both-forms-exclusive",
 	"anchor-field-for-3-1-plus",
 	"authorization-url-forbidden",
@@ -227,6 +240,7 @@ var validationErrorCodes = []string{
 	"pattern-properties-field-for-3-1-plus",
 	"prefix-items-field-for-3-1-plus",
 	"property-names-field-for-3-1-plus",
+	"query-field-for-3-2-plus",
 	"read-only-write-only-mutually-exclusive",
 	"request-body-content-required",
 	"response-description-required",
diff --git a/openapi3/validation_error.go b/openapi3/validation_error.go
index f2954afb32707e0c615caeb69e717917e3c42262..59a544f0b87d8cf49daa19c479a70fec98a6130a 100644
--- a/openapi3/validation_error.go
+++ b/openapi3/validation_error.go
@@ -535,6 +535,36 @@ func (e *DuplicateParameterError) Error() string {
 	return fmt.Sprintf("more than one %q parameter has name %q", e.In, e.Name)
 }
 
+// AdditionalOperationsDuplicateMethodError clusters "additionalOperations
+// key duplicates a fixed field" failures. OpenAPI 3.2's
+// `additionalOperations` map may only carry methods that have no dedicated
+// Path Item Object field.
+type AdditionalOperationsDuplicateMethodError struct {
+	// Method is the offending additionalOperations key.
+	Method string
+	// Origin is the source location of the offending path item when the
+	// document was loaded with Loader.IncludeOrigin = true.
+	Origin *Origin
+}
+
+func (e *AdditionalOperationsDuplicateMethodError) Error() string {
+	return fmt.Sprintf("additionalOperations key %q duplicates a fixed path item field", e.Method)
+}
+
+// AdditionalOperationsInvalidMethodError clusters "additionalOperations key
+// is not an HTTP method" failures. Keys must be RFC 9110 tokens.
+type AdditionalOperationsInvalidMethodError struct {
+	// Method is the offending additionalOperations key.
+	Method string
+	// Origin is the source location of the offending path item when the
+	// document was loaded with Loader.IncludeOrigin = true.
+	Origin *Origin
+}
+
+func (e *AdditionalOperationsInvalidMethodError) Error() string {
+	return fmt.Sprintf("additionalOperations key %q is not a valid HTTP method token", e.Method)
+}
+
 // DuplicateRequiredFieldError clusters "duplicate field in required" failures.
 // The elements of a schema's `required` array MUST be unique (JSON Schema
 // 2020-12 §6.5.3 for OpenAPI 3.1, draft-04 for OpenAPI 3.0).
@@ -1424,7 +1454,7 @@ func exampleValueOrigin(ex *Example, fallback *Origin) *Origin {
 	if ex == nil || ex.Origin == nil {
 		return fallback
 	}
-	if loc, ok := ex.Origin.Fields["value"]; ok {
+	if loc, ok := ex.Origin.Fields.Lookup("value"); ok {
 		return &Origin{Key: &loc}
 	}
 	return ex.Origin
@@ -1531,8 +1561,24 @@ func (e *ItemSchemaFieldFor32Plus) As(target any) bool {
 	return asValidationError(target, &e.ValidationError)
 }
 
+type QueryFieldFor32Plus struct{ ValidationError }
+
+func (e *QueryFieldFor32Plus) As(target any) bool {
+	return asValidationError(target, &e.ValidationError)
+}
+
+type AdditionalOperationsFieldFor32Plus struct{ ValidationError }
+
+func (e *AdditionalOperationsFieldFor32Plus) As(target any) bool {
+	return asValidationError(target, &e.ValidationError)
+}
+
 var fieldFor32PlusLeaves = map[string]func(msg string) error{
 	"itemSchema": func(m string) error { return &ItemSchemaFieldFor32Plus{ValidationError{Message: m}} },
+	"query":      func(m string) error { return &QueryFieldFor32Plus{ValidationError{Message: m}} },
+	"additionalOperations": func(m string) error {
+		return &AdditionalOperationsFieldFor32Plus{ValidationError{Message: m}}
+	},
 }
 
 func errFieldFor32Plus(field string, origin *Origin) error {
@@ -1546,6 +1592,14 @@ func errFieldFor32Plus(field string, origin *Origin) error {
 	return newFieldVersionMismatch(field, "3.2", leaf, origin)
 }
 
+func newAdditionalOperationsDuplicateMethod(method string, origin *Origin) error {
+	return &AdditionalOperationsDuplicateMethodError{Method: method, Origin: origin}
+}
+
+func newAdditionalOperationsInvalidMethod(method string, origin *Origin) error {
+	return &AdditionalOperationsInvalidMethodError{Method: method, Origin: origin}
+}
+
 func newPathParameterRequired(param string, origin *Origin) error {
 	return &PathParameterRequiredError{Param: param, Origin: origin}
 }
diff --git a/openapi3filter/req_resp_decoder.go b/openapi3filter/req_resp_decoder.go
index 98417470e4a3ec07e293c6dda25698f8f0cd565e..bff7561215356f6b7e4c6e9d5dcabfb99c033d2c 100644
--- a/openapi3filter/req_resp_decoder.go
+++ b/openapi3filter/req_resp_decoder.go
@@ -194,6 +194,10 @@ func defaultContentParameterDecoder(param *openapi3.Parameter, values []string)
 		err = fmt.Errorf("parameter %q has no content schema", param.Name)
 		return
 	}
+	if mt.Schema == nil {
+		err = fmt.Errorf("parameter %q content media type has no schema", param.Name)
+		return
+	}
 	outSchema = mt.Schema.Value
 
 	unmarshal := func(encoded string, paramSchema *openapi3.SchemaRef) (decoded any, err error) {
@@ -263,15 +267,29 @@ func decodeStyledParameter(param *openapi3.Parameter, input *RequestValidationIn
 	return decodeValue(dec, param.Name, sm, param.Schema, param.Required)
 }
 
+var errCircularSchema = errors.New("circular schema reference detected while decoding")
+
 func decodeValue(dec valueDecoder, param string, sm *openapi3.SerializationMethod, schema *openapi3.SchemaRef, required bool) (any, bool, error) {
+	return decodeValueGuarded(dec, param, sm, schema, required, nil)
+}
+
+func decodeValueGuarded(dec valueDecoder, param string, sm *openapi3.SerializationMethod, schema *openapi3.SchemaRef, required bool, seen []*openapi3.Schema) (any, bool, error) {
 	var found bool
 
+	if schema == nil {
+		return nil, false, nil
+	}
+	if slices.Contains(seen, schema.Value) {
+		return nil, false, errCircularSchema
+	}
+	seen = append(seen, schema.Value)
+
 	if len(schema.Value.AllOf) > 0 {
 		var value any
 		var err error
 		for _, sr := range schema.Value.AllOf {
 			var f bool
-			value, f, err = decodeValue(dec, param, sm, sr, required)
+			value, f, err = decodeValueGuarded(dec, param, sm, sr, required, seen)
 			found = found || f
 			if value == nil || err != nil {
 				break
@@ -282,7 +300,7 @@ func decodeValue(dec valueDecoder, param string, sm *openapi3.SerializationMetho
 
 	if len(schema.Value.AnyOf) > 0 {
 		for _, sr := range schema.Value.AnyOf {
-			value, f, _ := decodeValue(dec, param, sm, sr, required)
+			value, f, _ := decodeValueGuarded(dec, param, sm, sr, required, seen)
 			found = found || f
 			if value != nil {
 				return value, found, nil
@@ -298,7 +316,7 @@ func decodeValue(dec valueDecoder, param string, sm *openapi3.SerializationMetho
 		isMatched := 0
 		var value any
 		for _, sr := range schema.Value.OneOf {
-			v, f, _ := decodeValue(dec, param, sm, sr, required)
+			v, f, _ := decodeValueGuarded(dec, param, sm, sr, required, seen)
 			found = found || f
 			if v != nil {
 				value = v
@@ -514,10 +532,23 @@ func (d *urlValuesDecoder) DecodePrimitive(param string, sm *openapi3.Serializat
 		return nil, ok, nil
 	}
 
+	// Repeated query keys: prefer the first non-empty value so an empty
+	// leading occurrence cannot hide a later value from schema validation
+	// (#1230). A lone empty string is still returned unchanged.
+	raw := values[0]
+	if raw == "" && len(values) > 1 {
+		for _, v := range values[1:] {
+			if v != "" {
+				raw = v
+				break
+			}
+		}
+	}
+
 	if schema.Value.Type == nil && schema.Value.Pattern != "" {
-		return values[0], ok, nil
+		return raw, ok, nil
 	}
-	val, err := parsePrimitive(values[0], schema)
+	val, err := parsePrimitive(raw, schema)
 	return val, ok, err
 }
 
@@ -557,6 +588,9 @@ func (d *urlValuesDecoder) DecodeArray(param string, sm *openapi3.SerializationM
 // Every item is parsed as a primitive value.
 // The function returns an error when an error happened while parse array's items.
 func (d *urlValuesDecoder) parseArray(raw []string, schemaRef *openapi3.SchemaRef) ([]any, error) {
+	if schemaRef.Value.Items == nil || schemaRef.Value.Items.Value == nil {
+		return nil, errors.New("array items schema is required for decoding")
+	}
 	var value []any
 
 	for i, v := range raw {
@@ -643,6 +677,13 @@ const (
 	urlDecoderDelimiter = "\x1F" // should not conflict with URL characters
 )
 
+func decodesAdditionalProperties(schema *openapi3.Schema) bool {
+	if schema.AdditionalProperties.Schema != nil {
+		return true
+	}
+	return schema.AdditionalProperties.Has != nil && *schema.AdditionalProperties.Has
+}
+
 func (d *urlValuesDecoder) DecodeObject(param string, sm *openapi3.SerializationMethod, schema *openapi3.SchemaRef) (map[string]any, bool, error) {
 	var propsFn func(url.Values) (map[string]string, error)
 	switch sm.Style {
@@ -667,10 +708,15 @@ func (d *urlValuesDecoder) DecodeObject(param string, sm *openapi3.Serialization
 			return propsFromString(values[0], ",", ",")
 		}
 	case "deepObject":
+		// Compile the parameter-name prefix matcher once: it depends only on
+		// param (constant for the whole loop), not on the loop variable. Doing
+		// this inside the loop recompiles it once per query key, turning an
+		// attacker-controlled key count into proportional CPU.
+		paramPrefixRE := regexp.MustCompile(fmt.Sprintf(`^%s\[`, regexp.QuoteMeta(param)))
 		propsFn = func(params url.Values) (map[string]string, error) {
 			props := make(map[string]string)
 			for key, values := range params {
-				if !regexp.MustCompile(fmt.Sprintf(`^%s\[`, regexp.QuoteMeta(param))).MatchString(key) {
+				if !paramPrefixRE.MatchString(key) {
 					continue
 				}
 				matches := deepObjectBracketRE.FindAllStringSubmatch(key, -1)
@@ -707,7 +753,7 @@ func (d *urlValuesDecoder) DecodeObject(param string, sm *openapi3.Serialization
 		return nil, false, err
 	}
 
-	found := false
+	found := sm.Style == "deepObject" && len(props) > 0 && decodesAdditionalProperties(schema.Value)
 	for propName := range schema.Value.Properties {
 		if _, ok := props[propName]; ok {
 			found = true
@@ -993,6 +1039,9 @@ func buildResObj(params map[string]any, parentKeys []string, key string, schema
 
 	switch {
 	case schema.Value.Type.Is("array"):
+		if schema.Value.Items == nil || schema.Value.Items.Value == nil {
+			return nil, &ParseError{path: pathFromKeys(mapKeys), Kind: KindOther, Reason: "array items schema is required"}
+		}
 		paramArr, ok := deepGet(params, mapKeys...)
 		if !ok {
 			return nil, nil
@@ -1046,6 +1095,15 @@ func buildResObj(params map[string]any, parentKeys []string, key string, schema
 					resultMap[k] = r
 				}
 			}
+		} else if schema.Value.AdditionalProperties.Has != nil && *schema.Value.AdditionalProperties.Has {
+			// additionalProperties: true is free-form: retain dynamic values as
+			// decoded query-string data, but never overwrite schema-decoded
+			// properties.
+			for k, v := range objectParams {
+				if _, exists := resultMap[k]; !exists {
+					resultMap[k] = v
+				}
+			}
 		}
 
 		return resultMap, nil
@@ -1124,6 +1182,9 @@ func pathFromKeys(kk []string) []any {
 // Every item is parsed as a primitive value.
 // The function returns an error when an error happened while parse array's items.
 func parseArray(raw []string, schemaRef *openapi3.SchemaRef) ([]any, error) {
+	if schemaRef.Value.Items == nil || schemaRef.Value.Items.Value == nil {
+		return nil, errors.New("array items schema is required for decoding")
+	}
 	var value []any
 	for i, v := range raw {
 		item, err := parsePrimitive(v, schemaRef.Value.Items)
@@ -1418,6 +1479,9 @@ func UrlencodedBodyDecoder(body io.Reader, header http.Header, schema *openapi3.
 		case propType.Is("object"):
 			return nil, fmt.Errorf("unsupported schema of request body's property %q", propName)
 		case propType.Is("array"):
+			if propSchema.Value.Items == nil || propSchema.Value.Items.Value == nil {
+				return nil, fmt.Errorf("unsupported schema of request body's property %q: array items required", propName)
+			}
 			items := propSchema.Value.Items.Value
 			if !(items.Type.Is("string") || items.Type.Is("integer") || items.Type.Is("number") || items.Type.Is("boolean")) {
 				return nil, fmt.Errorf("unsupported schema of request body's property %q", propName)
@@ -1561,6 +1625,9 @@ func MultipartBodyDecoder(body io.Reader, header http.Header, schema *openapi3.S
 				}
 			}
 			if valueSchema.Value.Type.Is("array") {
+				if valueSchema.Value.Items == nil {
+					return nil, fmt.Errorf("unsupported schema of multipart part %q: array items required", name)
+				}
 				valueSchema = valueSchema.Value.Items
 			}
 		}
@@ -1659,7 +1726,7 @@ func ZipFileBodyDecoder(body io.Reader, header http.Header, schema *openapi3.Sch
 			for {
 				n, err := rc.Read(buffer)
 				if 0 < n {
-					content = append(content, buffer...)
+					content = append(content, buffer[:n]...)
 				}
 				if err == io.EOF {
 					break
diff --git a/openapi3filter/validation_handler.go b/openapi3filter/validation_handler.go
index d4bb1efa09b2ff2d969fdce61c81c68bd358fa01..6ddbef5afa7f7c077b96b0ddb674672db98b3847 100644
--- a/openapi3filter/validation_handler.go
+++ b/openapi3filter/validation_handler.go
@@ -3,6 +3,7 @@ package openapi3filter
 import (
 	"context"
 	"net/http"
+	"strings"
 
 	"github.com/getkin/kin-openapi/openapi3"
 	"github.com/getkin/kin-openapi/routers"
@@ -44,9 +45,7 @@ func (h *ValidationHandler) Load() error {
 	if h.Handler == nil {
 		h.Handler = http.DefaultServeMux
 	}
-	if h.AuthenticationFunc == nil {
-		h.AuthenticationFunc = NoopAuthenticationFunc
-	}
+	// NOTE: users MUST set AuthenticationFunc explicitly or expect ErrAuthenticationServiceMissing when verifying SecurityRequirements
 	if h.ErrorEncoder == nil {
 		h.ErrorEncoder = DefaultErrorEncoder
 	}
@@ -81,6 +80,12 @@ func (h *ValidationHandler) before(w http.ResponseWriter, r *http.Request) (hand
 	return false
 }
 
+// ErrEncodedPathSeparator is returned when a request path holds an encoded path
+// separator and the decoded path resolves to another operation than the escaped
+// path does. Serving such a request would validate one operation while the
+// wrapped handler serves the other one.
+var ErrEncodedPathSeparator error = &routers.RouteError{Reason: "path contains an encoded path separator resolving to another operation"}
+
 func (h *ValidationHandler) validateRequest(r *http.Request) error {
 	// Find route
 	route, pathParams, err := h.router.FindRoute(r)
@@ -88,6 +93,10 @@ func (h *ValidationHandler) validateRequest(r *http.Request) error {
 		return err
 	}
 
+	if err := h.checkEncodedPathSeparator(r, route); err != nil {
+		return err
+	}
+
 	options := &Options{
 		AuthenticationFunc: h.AuthenticationFunc,
 	}
@@ -105,3 +114,31 @@ func (h *ValidationHandler) validateRequest(r *http.Request) error {
 
 	return nil
 }
+
+// checkEncodedPathSeparator rejects a request whose encoded path separators make
+// r.URL.Path and r.URL.RawPath select different operations. The router matches
+// on the decoded path while routers such as gorilla/mux with UseEncodedPath
+// match on the escaped one, so the operation validated here — its security
+// requirements included — would not be the operation the wrapped handler serves.
+func (h *ValidationHandler) checkEncodedPathSeparator(r *http.Request, route *routers.Route) error {
+	escapedPath := r.URL.EscapedPath()
+	segment := escapedPath
+	for _, separator := range []string{"%2F", "%2f"} {
+		segment = strings.ReplaceAll(segment, separator, "~")
+	}
+	if segment == escapedPath {
+		return nil
+	}
+
+	shadow := r.Clone(r.Context())
+	shadow.URL.Path, shadow.URL.RawPath = segment, ""
+	escapedRoute, _, err := h.router.FindRoute(shadow)
+	if err != nil ||
+		escapedRoute.Method != route.Method ||
+		escapedRoute.Path != route.Path ||
+		escapedRoute.Operation != route.Operation {
+		return ErrEncodedPathSeparator
+	}
+
+	return nil
+}

# (32 test/doc file(s) of the upstream fix omitted here)

# ... 18 more source file(s) changed in this fix, listed instead of shown to save space (the same kind of change unless the line says otherwise):
- go.mod: +1 -1; first added line: github.com/santhosh-tekuri/jsonschema/v6 v6.0.3
- openapi2/path_item.go: +1 -1; first added line: return nil
- openapi3/doc.go: +2 -0; first added line: //   - Path Item Object query field for the HTTP QUERY method
- openapi3/schema_pattern.go: +2 -0; first added line: // A failed compile can yield a typed nil, which no call site's nil check catches.
- openapi3/schema_validation_settings.go: +4 -0; first added line: // visitedSchemas provides pointer-identity cycle detection for runtime
- openapi3/testdata/apis_guru_openapi_directory/flat_io_2_13_0_openapi_yaml__validate: +0 -1; first added line: 
- openapi3/testdata/apis_guru_openapi_directory/mist_com_0_37_7_openapi_yaml__validate: +1 -1; first added line: invalid paths: invalid path /api/v1/sites/{site_id}/devices/{device_id}: invalid operation PUT: invalid example: input matches more than one
- openapi3/testdata/apis_guru_openapi_directory/ndhm_gov_in_ndhm_cm_0_5_openapi_yaml__validate: +9 -1; first added line: invalid components: schema "HealthInformationNotification": invalid example: value must be a string
- openapi3/testdata/discriminatorLocalMapping.yml: +26 -0; first added line: openapi: 3.1.0
- openapi3/testdata/issue1205/mutual-a.yml: +25 -0; first added line: openapi: 3.1.0
- openapi3/testdata/issue1205/mutual-b.yml: +25 -0; first added line: openapi: 3.1.0
- openapi3/testdata/issue1205/mutual.yml: +14 -0; first added line: openapi: 3.1.0
- openapi3/testdata/issue1205/openapi.yml: +12 -0; first added line: openapi: 3.1.0
- openapi3/walk_parameters.go: +3 -5; first added line: for _, entry := range item.operationEntries() {
- openapi3/walk_schemas.go: +2 -3; first added line: for _, entry := range item.operationEntries() {
- openapi3filter/testdata/encoded_path_authorization_bypass.yml: +30 -0; first added line: openapi: 3.0.3
- routers/gorillamux/router.go: +3 -0; first added line: if route.Operation == nil {
- routers/legacy/router.go: +7 -0; first added line: if node == nil {

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### .github/docs/openapi3.txt
```
package openapi3 // import "github.com/getkin/kin-openapi/openapi3"

Package openapi3 parses and writes OpenAPI 3 specification documents.

Supports OpenAPI 3.0, OpenAPI 3.1, and OpenAPI 3.2:
  - OpenAPI 3.0.x:
    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md
  - OpenAPI 3.1.x:
    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md
  - OpenAPI 3.2.x: https://spec.openapis.org/oas/v3.2.0.html

OpenAPI 3.1 Features:
  - Type arrays with null support (e.g., ["string", "null"])
  - JSON Schema 2020-12 keywords (const, examples, prefixItems, etc.)
  - Webhooks for defining callback operations
  - JSON Schema dialect specification
  - SPDX license identifiers

OpenAPI 3.2 Features:
  - Media Type Object itemSchema for streaming sequential media types

The implementation maintains 100% backward compatibility with OpenAPI 3.0.

For OpenAPI 3.1 validation, use the JSON Schema 2020-12 validator option:

    schema.VisitJSON(value, openapi3.EnableJSONSchema2020())

Version detection is available via helper methods:

    if doc.IsOpenAPI31OrLater() {
        // Handle OpenAPI 3.1 specific features
    }
    if doc.IsOpenAPI32OrLater() {
        // Handle OpenAPI 3.2 specific features
    }

Code generated by go generate using refs.tmpl; DO NOT EDIT refs.go.

CONSTANTS

const (
	ParameterInPath   = "path"
	ParameterInQuery  = "query"
	ParameterInHeader = "header"
	ParameterInCookie = "cookie"
)
const (
	TypeArray   = "array"
	TypeBoolean = "boolean"
	TypeInteger = "integer"
	TypeNumber  = "number"
	TypeObject  = "object"
	TypeString  = "string"
	TypeNull    = "null"
)
const (
	// FormatOfStringForUUIDOfRFC4122 is an optional predefined format for UUID v1-v5 as specified by RFC4122
	FormatOfStringForUUIDOfRFC4122 = `^(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|00000000-0000-0000-0000-000000000000)$`

	// FormatOfStringForEmail pattern catches only some suspiciously wrong-looking email addresses.
	// Use DefineStringFormat(...) if you need something stricter.
	FormatOfStringForEmail = `^[^@]+@[^@<>",\s]+$`

	// FormatOfStringByte is a regexp for base64-encoded characters, for example, "U3dhZ2dlciByb2Nrcw=="
	FormatOfStringByte = `(^$|^[a-zA-Z0-9+/\-_]*=*$)`

	// FormatOfStringDate is a RFC3339 date format regexp, for example "2017-07-21".
	FormatOfStringDate = `^[0-9]{4}-(0[1-9]|10|11|12)-(0[1-9]|[12][0-9]|3[01])$`

	// FormatOfStringDateTime is a RFC3339 date-time format regexp, for example "2017-07-21T17:32:28Z".
	FormatOfStringDateTime = `^[0-9]{4}-(0[1-9]|10|11|12)-(0[1-9]|[12][0-9]|3[01])T([0-1][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?(Z|(\+|-)[0-9]{2}:[0-9]{2})$`
)
const (
	SerializationSimple         = "simple"
	SerializationLabel          = "label"
	SerializationMatrix         = "matrix"
	SerializationForm           = "form"
	SerializationSpaceDelimited = "spaceDelimited"
	SerializationPipeDelimited  = "pipeDelimited"
	SerializationDeepObject     = "deepObject"
)

VARIABLES

var (
	IdentifierRegExp            = regexp.MustCompile(`^[` + identifierChars + `]+$`)
	InvalidIdentifierCharRegExp = regexp.MustCompile(`[^` + identifierChars + `]`)
)
    IdentifierRegExp verifies whether Component object key matches contains just
    'identifierChars', according to OpenAPI v3.x. InvalidIdentifierCharRegExp
    matches all characters not contained in 'identifierChars'. However, to be
    able supporting legacy OpenAPI v2.x, there is a need to customize above
    pattern in order not to fail converted v2-v3 validation

var (
	// SchemaErrorDetailsDisabled disables printing of details about schema errors.
	SchemaErrorDetailsDisabled = false

	// ErrOneOfConflict is the SchemaError Origin when data matches more than one oneOf schema
	ErrOneOfConflict = errors.New("input matches more than one oneOf schemas")

	// ErrSchemaInputNaN may be returned when validating a number
	ErrSchemaInputNaN = errors.New("floating point NaN is not allowed")
	// ErrSchemaInputInf may be returned when validating a number
	ErrSchemaInputInf = errors.New("floating point Inf is not allowed")
)
var (
	// SchemaStringFormats is a map of custom string format validators.
	SchemaStringFormats = make(map[string]StringFormatValidator)
	// SchemaNumberFormats is a map of custom number format validators.
	SchemaNumberFormats = make(map[string]NumberFormatValidator)
	// SchemaIntegerFormats is a map of custom integer format validators.
	SchemaIntegerFormats = make(map[string]IntegerFormatValidator)
)
var DefaultReadFromURI = URIMapCache(ReadFromURIs(ReadFromHTTP(http.DefaultClient), ReadFromFile))
    DefaultReadFromURI returns a caching ReadFromURIFunc which can read remote
    HTTP URIs and local file URIs.

var ErrURINotSupported = errors.New("unsupported URI")
    ErrURINotSupported indicates the ReadFromURIFunc does not know how to handle
    a given URI.

var IncludeOrigin = false
    IncludeOrigin specifies whether to include the origin of the OpenAPI
    elements. Deprecated: set Loader.IncludeOrigin instead. This global is read
    by NewLoader for backward compatibility but is not safe for concurrent use.

var SkipSubtree = errors.New("skip schema subtree")
    SkipSubtree, when returned by a WalkSchemasFunc, tells WalkSchemas not to
    descend into the current schema's sub-schemas. The schema itself has already
    been visited. Any other non-nil error stops the walk and is returned by
    WalkSchemas. It mirrors filepath.SkipDir.


FUNCTIONS

func BoolPtr(value bool) *bool
    BoolPtr is a helper for defining OpenAPI schemas.

    Deprecated: Use Ptr instead.

func DefaultRefNameResolver(doc *T, ref ComponentRef) string
    DefaultRefResolver is a default implementation of refNameResolver for the
    InternalizeRefs function.

    The external reference is internalized to (hopefully) a unique name.
    If the external reference matches (by path) to another reference in the root
    document then the name of that component is used.

    The transformation involves:
      - Cutting the "#/components/<type>" part.
      - Cutting the file extensions (.yaml/.json) from documents.
      - Trimming the common directory with the root spec.
      - Replace invalid characters with underscores.

    This is an injective mapping over a "reasonable" amount of the possible
    openapi spec domain space but is not perfect. There might be edge cases.

func DefineIPv4Format()
    DefineIPv4Format opts in ipv4 format validation on top of OAS 3 spec

func DefineIPv6Format()
    DefineIPv6Format opts in ipv6 format validation on top of OAS 3 spec

func DefineIntegerFormatValidator(name string, validator IntegerFormatValidator)
    DefineIntegerFormatValidator defines a custom format validator for a given
    integer format.

func DefineNumberFormatValidator(name string, validator NumberFormatValidator)
    DefineNumberFormatValidator defines a custom format validator for a given
    number format.

func DefineStringFormat(name string, pattern string)
    DefineStringFormat defines a regexp pattern for a given string format

    Deprecated: Use openapi3.DefineStringFormatValidator(name,
    NewRegexpFormatValidator(pattern)) instead.

func DefineStringFormatCallback(name string, callback func(string) error)
    DefineStringFormatCallback defines a callback function for a given string
    format

    Deprecated: Use openapi3.DefineStringFormatValidator(name,
    NewCallbackValidator(fn)) instead.

func DefineStringFormatValidator(name string, validator StringFormatValidator)
    DefineStringFormatValidator defines a custom format validator for a given
    string format.

func Float64Ptr(value float64) *float64
    Float64Ptr is a helper for defining OpenAPI schemas.

    Deprecated: Use Ptr instead.

func Int64Ptr(value int64) *int64
    Int64Ptr is a helper for defining OpenAPI schemas.

    Deprecated: Use Ptr instead.

func Ptr[T any](value T) *T
    Ptr is a helper for defining OpenAPI schemas.

func ReadFromFile(loader *Loader, location *url.URL) ([]byte, error)
    ReadFromFile is a ReadFromURIFunc which reads local file URIs.

func ReferencesComponentInRootDocument(doc *T, ref ComponentRef) (string, bool)
    ReferencesComponentInRootDocument returns if the given component reference
    references the same document or element as another component reference in
    the root document's '#/components/<type>'. If it does, it returns the name
    of it in the form '#/components/<type>/NameXXX'

    Of course given a component from the root document will always match itself.

    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#reference-object
    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#relative-references-in-urls

    Example. Take the spec with directory structure:

        openapi.yaml
        schemas/
        ├─ record.yaml
        ├─ records.yaml

    In openapi.yaml we have:

        components:
          schemas:
            Record:
              $ref: schemas/record.yaml

    Case 1: records.yml references a component in the root document

        $ref: ../openapi.yaml#/components/schemas/Record

    This would return...

        #/components/schemas/Record

    Case 2: records.yml indirectly refers to the same schema as a schema the
    root document's '#/components/schemas'.

        $ref: ./record.yaml

    This would also return...

        #/components/schemas/Record

func RegisterArrayUniqueItemsChecker(fn SliceUniqueItemsChecker)
    RegisterArrayUniqueItemsChecker is used to register a customized function
    used to check if JSON array have unique items.

func Uint64Ptr(value uint64) *uint64
    Uint64Ptr is a helper for defining OpenAPI schemas.

    Deprecated: Use Ptr instead.

func ValidateIdentifier(value string) error
    ValidateIdentifier returns an error if the given component name does not
    match IdentifierRegExp.

func ValidationErrorCodes() []string
    ValidationErrorCodes returns every code a validation error can carry,
    sorted. TestValidationErrorCodes keeps it in sync with the errors the
    validators emit.

func WithValidationOptions(ctx context.Context, opts ...ValidationOption) context.Context
    WithValidationOptions allows adding validation options to a context object
    that can be used when validating any OpenAPI type.


TYPES

type APIKeyInInvalidError struct {
	// Value is the rejected `in:` value (empty when the field was
	// omitted, otherwise the bad value e.g. "body").
	Value string
	// Origin is the source location of the offending security scheme
	// when the document was loaded with Loader.IncludeOrigin = true.
	Origin *Origin
}
    APIKeyInInvalidError clusters "apiKey should have 'in'. It can be 'query',
    'header' or 'cookie', not X" failures. Fires when an apiKey security scheme
    either omits `in:` or sets it to a value outside {query, header, cookie}.
    Carries the rejected value so callers can render or filter; empty string
    means the field was missing entirely.

func (e *APIKeyInInvalidError) Code() string

func (e *APIKeyInInvalidError) Error() string

type APIKeySecuritySchemeNameRequired struct{ ValidationError }

func (e *APIKeySecuritySchemeNameRequired) As(target any) bool

func (e *APIKeySecuritySchemeNameRequired) Code() string

type AdditionalProperties = BoolSchema
    AdditionalProperties is a type alias for BoolSchema, kept for backward
    compatibility.

type AnchorFieldFor31Plus struct{ ValidationError }

func (e *AnchorFieldFor31Plus) As(target any) bool

func (e *AnchorFieldFor31Plus) Code() string

type BoolSchema struct {
	Has    *bool
	Schema *SchemaRef
}
    BoolSchema represents a JSON Schema keyword that can be either a boolean
    or a schema object. Used for additionalProperties, unevaluatedProperties,
    and unevaluatedItems.

func (bs BoolSchema) MarshalJSON() ([]byte, error)
    MarshalJSON returns the JSON encoding of BoolSchema.

func (bs BoolSchema) MarshalYAML() (any, error)
    MarshalYAML returns the YAML encoding of BoolSchema.

func (bs *BoolSchema) UnmarshalJSON(data []byte) error
    UnmarshalJSON sets BoolSchema to a copy of data.

type Callback struct {
	Extensions map[string]any `json:"-" yaml:"-"`
	Origin     *Origin        `json:"-" yaml:"-"`

	// Has unexported fields.
}
    Callback is specified by OpenAPI/Swagger standard version 3. See
    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#callback-object

func NewCallback(opts ...NewCallbackOption) *Callback
    NewCallback builds a Callback object with path items in insertion order.

func NewCallbackWithCapacity(cap int) *Callback
    NewCallbackWithCapacity builds a callback object of the given capacity.

func (callback *Callback) Delete(key string)
    Delete removes the entry associated with key 'key' from 'callback'.

func (callback Callback) JSONLookup(token string) (any, error)
    JSONLookup implements
    https://github.com/go-openapi/jsonpointer#JSONPointable

func (callback *Callback) Keys() []string
    Keys returns the callback keys in a fixed order

func (callback *Callback) Len() int
    Len returns the amount of keys in callback excluding callback.Extensions.

func (callback *Callback) Map() (m map[string]*PathItem)
    Map returns callback as a 'map'. Note: iteration on Go maps is not ordered.

func (callback *Callback) MarshalJSON() ([]byte, error)
    MarshalJSON returns the JSON encoding of Callback.

func (callback *Callback) MarshalYAML() (any, error)
    MarshalYAML returns the YAML encoding of Callback.

func (callback *Callback) Set(key string, value *PathItem)
    Set adds or replaces key 'key' of 'callback' with 'value'. Note: 'callback'
    MUST be non-nil

func (callback *Callback) UnmarshalJSON(data []byte) (err error)
    UnmarshalJSON sets Callback to a copy of data.

func (callback *Callback) Validate(ctx context.Context, opts ...ValidationOption) error
    Validate returns an error if Callback does not comply with the OpenAPI spec.

func (callback *Callback) Value(key string) *PathItem
    Value returns the callback for key or nil

type CallbackRef struct {
	// Extensions only captures fields starting with 'x-' as no other fields
	// are allowed by the openapi spec.
	Extensions map[string]any
	Origin     *Origin `json:"-" yaml:"-"`
	// Reference Object summary and description are supported in OpenAPI 3.1+.
	Summary     *string `json:"summary,omitempty" yaml:"summary,omitempty"`
	Description *string `json:"description,omitempty" yaml:"description,omitempty"`

	Ref   string
	Value *Callback

	// Has unexported fields.
}
    CallbackRef represents either a Callback or a $ref to a Callback. When
    serializing and both fields are set, Ref is preferred over Value.

func (x *CallbackRef) CollectionName() string
    CollectionName returns the JSON string used for a collection of these
    components.

func (x *CallbackRef) JSONLookup(token string) (any, error)
    JSONLookup implements
    https://pkg.go.dev/github.com/go-openapi/jsonpointer#JSONPointable

func (x CallbackRef) MarshalJSON() ([]byte, error)
    MarshalJSON returns the JSON encoding of CallbackRef.

func (x CallbackRef) MarshalYAML() (any, error)
    MarshalYAML returns the YAML encoding of CallbackRef.

func (x *CallbackRef) RefPath() *url.URL
    RefPath returns the path of the $ref relative to the root document.

func (x *CallbackRef) RefString() string
    RefString returns the $ref value.

func (x *CallbackRef) UnmarshalJSON(data []byte) error
    UnmarshalJSON sets CallbackRef to a copy of data.

func (x *CallbackRef) Validate(ctx context.Context, opts ...ValidationOption) error
    Validate returns an error if CallbackRef does not comply with the OpenAPI
    spec.

type Callbacks map[string]*CallbackRef // Callbacks represents components' named callbacks

func (m Callbacks) JSONLookup(token string) (any, error)
    JSONLookup implements
    https://pkg.go.dev/github.com/go-openapi/jsonpointer#JSONPointable

type CodedError interface {
	error
	Code() string
}
    CodedError is implemented by every typed validation error. Code returns
    a stable, kebab-case identifier for the validation rule that failed (e.g.
    "operation-responses-required"), so consumers can suppress specific
    findings, assign per-rule severities, emit machine-readable diagnostics
    (e.g. the LSP Diagnostic.code field), or link to per-rule documentation
    without depending on message text.

    Every code is declared as a literal on its error type; nothing is derived.
    Codes are a contract: message wording and Go type names may change freely,
    codes may not. Renaming or removing a code is a breaking change and
    is recorded in the README changelog. The full set is available from
    ValidationErrorCodes.

    Like net.Error, this interface exists as an assertion target for consumers;
    the package itself constructs concrete error types and does not consume it.
    Reach the code of a wrapped error with errors.As:

        var coded openapi3.CodedError
        if errors.As(err, &coded) {
        	fmt.Println(coded.Code())
        }

type CommentFieldFor31Plus struct{ ValidationError }

func (e *CommentFieldFor31Plus) As(target any) bool

func (e *CommentFieldFor31Plus) Code() string

type ComponentRef interface {
	RefString() string
	RefPath() *url.URL
	CollectionName() string
}

type ComponentValidationError struct {
	// Section is the lowercase singular form of the component bucket
	// ("schema", "parameter", "header", "request body", "response",
	// "security scheme", "example", "link", "callback").
	Section string
	// Name is the component map key.
	Name  string
	Cause error
}
    ComponentValidationError wraps validation errors inside the Components
    container, carrying which sub-section (Schemas, Parameters, etc.) and which
    component name failed.

func (e *ComponentValidationError) Error() string

func (e *ComponentValidationError) Unwrap() error

type Components struct {
	Extensions map[string]any `json:"-" yaml:"-"`
	Origin     *Origin        `json:"-" yaml:"-"`

	Schemas         Schemas         `json:"schemas,omitempty" yaml:"schemas,omitempty"`
	Parameters      ParametersMap   `json:"parameters,omitempty" yaml:"parameters,omitempty"`
	Headers         Headers         `json:"headers,omitempty" yaml:"headers,omitempty"`
	RequestBodies   RequestBodies   `json:"requestBodies,omitempty" yaml:"requestBodies,omitempty"`
	Responses       ResponseBodies  `json:"responses,omitempty" yaml:"responses,omitempty"`
	SecuritySchemes SecuritySchemes `json:"securitySchemes,omitempty" yaml:"securitySchemes,omitempty"`
	Examples        Examples        `json:"examples,omitempty" yaml:"examples,omitempty"`
	Links           Links           `json:"links,omitempty" yaml:"links,omitempty"`
	Callbacks       Callbacks       `json:"callbacks,omitempty" yaml:"callbacks,omitempty"`
}
    Components is specified by OpenAPI/Swagger standard version 3. See
    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#components-object

func NewComponents() Components

func (components Components) MarshalJSON() ([]byte, error)
    MarshalJSON returns the JSON encoding of Components.

func (components Components) MarshalYAML() (any, error)
    MarshalYAML returns the YAML encoding of Components.

func (components *Components) UnmarshalJSON(data []byte) error
    UnmarshalJSON sets Components to a copy of data.

func (components *Components) Validate(ctx context.Context, opts ...ValidationOption) error
    Validate returns an error if Components does not comply with the OpenAPI
    spec.

type ConflictingPathsError struct {
	// Path1 / Path2 are the two conflicting path keys, in document
	// order.
	Path1 string
	Path2 string
	// Origin is the source location of the paths object when the
	// document was loaded with Loader.IncludeOrigin = true.
	Origin *Origin
}
    ConflictingPathsError clusters "conflicting paths X and Y" failures.
    Fires when two path keys normalize to the same template (e.g. "/users/{a}"
    and "/users/{b}" both normalize to "/users/{}").

func (e *ConflictingPathsError) Code() string

func (e *ConflictingPathsError) Error() string

type ConstFieldFor31Plus struct{ ValidationError }

func (e *ConstFieldFor31Plus) As(target any) bool

func (e *ConstFieldFor31Plus) Code() string

type Contact struct {
	Extensions map[string]any `json:"-" yaml:"-"`
	Origin     *Origin        `json:"-" yaml:"-"`

	Name  string `json:"name,omitempty" yaml:"name,omitempty"`
	URL   string `json:"url,omitempty" yaml:"url,omitempty"`
	Email string `json:"email,omitempty" yaml:"email,omitempty"`
}
    Contact is specified by OpenAPI/Swagger standard version 3. See
    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#contact-object

func (contact Contact) MarshalJSON() ([]byte, error)
    MarshalJSON returns the JSON encoding of Contact.

func (contact Contact) MarshalYAML() (any, error)
    MarshalYAML returns the YAML encoding of Contact.

func (contact *Contact) UnmarshalJSON(data []byte) error
    UnmarshalJSON sets Contact to a copy of data.

func (contact *Contact) Validate(ctx context.Context, opts ...ValidationOption) error
    Validate returns an error if Contact does not comply with the OpenAPI spec.

type ContainsFieldFor31Plus struct{ ValidationError }

func (e *ContainsFieldFor31Plus) As(target any) bool

func (e *ContainsFieldFor31Plus) Code() string

type Content map[string]*MediaType
    Content is specified by OpenAPI/Swagger 3.0 standard.

func NewContent() Content

func NewContentWithFormDataSchema(schema *Schema) Content

func NewContentWithFormDataSchemaRef(schema *SchemaRef) Content

func NewContentWithJSONSchema(schema *Schema) Content

func NewContentWithJSONSchemaRef(schema *SchemaRef) Content

func NewContentWithSchema(schema *Schema, consumes []string) Content

func NewContentWithSchemaRef(schema *SchemaRef, consumes []string) Content

func (content Content) Get(mime string) *MediaType

func (content Content) Validate(ctx context.Context, opts ...ValidationOption) error
    Validate returns an error if Content does not comply with the OpenAPI spec.

type ContentEncodingFieldFor31Plus struct{ ValidationError }

func (e *ContentEncodingFieldFor31Plus) As(target any) bool

func (e *ContentEncodingFieldFor31Plus) Code() string

type ContentMediaTypeFieldFor31Plus struct{ ValidationError }

func (e *ContentMediaTypeFieldFor31Plus) As(target any) bool

func (e *ContentMediaTypeFieldFor31Plus) Code() string

type ContentSchemaFieldFor31Plus struct{ ValidationError }

func (e *ContentSchemaFieldFor31Plus) As(target any) bool

func (e *ContentSchemaFieldFor31Plus) Code() string

type DefaultViolatesSchema struct{ SchemaValueError }

func (e *DefaultViolatesSchema) As(target any) bool

func (e *DefaultViolatesSchema) Code() string

type DefsFieldFor31Plus struct{ ValidationError }

func (e *DefsFieldFor31Plus) As(target any) bool

func (e *DefsFieldFor31Plus) Code() string

type DependentRequiredFieldFor31Plus struct{ ValidationError }

func (e *DependentRequiredFieldFor31Plus) As(target any) bool

func (e *DependentRequiredFieldFor31Plus) Code() string

type DependentSchemasFieldFor31Plus struct{ ValidationError }

func (e *DependentSchemasFieldFor31Plus) As(target any) bool

func (e *DependentSchemasFieldFor31Plus) Code() string

type Discriminator struct {
	Extensions map[string]any `json:"-" yaml:"-"`
	Origin     *Origin        `json:"-" yaml:"-"`

	PropertyName string                `json:"propertyName" yaml:"propertyName"` // required
	Mapping      map[string]MappingRef `json:"mapping,omitempty" yaml:"mapping,omitempty"`
}
    Discriminator is specified by OpenAPI/Swagger standard version 3. See
    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#discriminator-object

func (discriminator Discriminator) MarshalJSON() ([]byte, error)
    MarshalJSON returns the JSON encoding of Discriminator.

func (discriminator Discriminator) MarshalYAML() (any, error)
    MarshalYAML returns the YAML encoding of Discriminator.

func (discriminator *Discriminator) UnmarshalJSON(data []byte) error
    UnmarshalJSON sets Discriminator to a copy of data.

func (discriminator *Discriminator) Validate(ctx context.Context, opts ...ValidationOption) error
    Validate returns an error if Discriminator does not comply with the OpenAPI
    spec.

type DuplicateOperationIDError struct {
	// OperationID is the duplicated operationId value.
	OperationID string
	// Endpoint1 / Endpoint2 are the two offending endpoints, in
	// deterministic order (lexicographically) for stable error messages.
	Endpoint1 string
	Endpoint2 string
	// Origin is the source location of the second (offending) operation
	// when the document was loaded with Loader.IncludeOrigin = true. The
	// pre-existing Endpoint1 is implicitly fine; the duplicate landed at
	// Endpoint2's site, which is the natural "go fix this" pointer.
	Origin *Origin
}
    DuplicateOperationIDError clusters "two operations share an operationId"
    failures. operationIds must be unique across all paths in a document.
    Endpoints are rendered as "<METHOD> <path>" (e.g. "POST /things").

func (e *DuplicateOperationIDError) Code() string

func (e *DuplicateOperationIDError) Error() string

type DuplicateParameterError struct {
	// In is the parameter location (e.g. "query", "path", "header").
	In string
	// Name is the duplicated parameter name.
	Name string
	// Origin is the source location of the offending parameter when
	// the document was loaded with Loader.IncludeOrigin = true.
	Origin *Origin
}
    DuplicateParameterError clusters "more than one X parameter has name Y"
    failures. Fires when two parameters on an operation (or path item) share the
    same In + Name combination.

func (e *DuplicateParameterError) Code() string

func (e *DuplicateParameterError) Error() string

type DuplicateRequiredFieldError struct {
	// Field is the field name listed more than once in `required`.
	Field string
	// Origin is the source location of the offending schema when the
	// document was loaded with Loader.IncludeOrigin = true.
	Origin *Origin
}
    DuplicateRequiredFieldError clusters "duplicate field in required" failures.
    The elements of a schema's `required` array MUST be unique (JSON Schema
    2020-12 §6.5.3 for OpenAPI 3.1, draft-04 for OpenAPI 3.0).

func (e *DuplicateRequiredFieldError) Code() string

func (e *DuplicateRequiredFieldError) Error() string

type DuplicateTagError struct {
	// Name is the tag name that appears more than once.
	Name string
	// Origin is the source location of the offending tag when the document
	// was loaded with Loader.IncludeOrigin = true.
	Origin *Origin
}
    DuplicateTagError clusters "more than one tag has name X" failures. Each tag
    name in the document-root `tags` list MUST be unique (OpenAPI Object).

func (e *DuplicateTagError) Code() string

func (e *DuplicateTagError) Error() string

type DynamicAnchorFieldFor31Plus struct{ ValidationError }

func (e *DynamicAnchorFieldFor31Plus) As(target any) bool

func (e *DynamicAnchorFieldFor31Plus) Code() string

type DynamicRefFieldFor31Plus struct{ ValidationError }

func (e *DynamicRefFieldFor31Plus) As(target any) bool

func (e *DynamicRefFieldFor31Plus) Code() string

type EitherFieldRequiredError struct {
	// Fields is the set of field names, at least one of which must be
	// set (e.g. ["value", "externalValue"]).
	Fields []string
	// Cause is the underlying leaf error. Walked by errors.Unwrap.
	Cause error
	// Origin is the source location of the offending element when the
	// document was loaded with Loader.IncludeOrigin = true.
	Origin *Origin
}
    EitherFieldRequiredError clusters "at least one of these fields must be set"
    failures (example.value vs externalValue, link.operationId vs operationRef).

func (e *EitherFieldRequiredError) Error() string

func (e *EitherFieldRequiredError) Unwrap() error

type ElseFieldFor31Plus struct{ ValidationError }

func (e *ElseFieldFor31Plus) As(target any) bool

func (e *ElseFieldFor31Plus) Code() string

type Encoding struct {
	Extensions map[string]any `json:"-" yaml:"-"`
	Origin     *Origin        `json:"-" yaml:"-"`

	ContentType   string  `json:"contentType,omitempty" yaml:"contentType,omitempty"`
	Headers       Headers `json:"headers,omitempty" yaml:"headers,omitempty"`
	Style         string  `json:"style,omitempty" yaml:"style,omitempty"`
	Explode       *bool   `json:"explode,omitempty" yaml:"explode,omitempty"`
	AllowReserved bool    `json:"allowReserved,omitempty" yaml:"allowReserved,omitempty"`
}
    Encoding is specified by OpenAPI/Swagger 3.0 standard. See
    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#encoding-object

func NewEncoding() *Encoding

func (encoding Encoding) MarshalJSON() ([]byte, error)
    MarshalJSON returns the JSON encoding of Encoding.

func (encoding Encoding) MarshalYAML() (any, error)
    MarshalYAML returns the YAML encoding of Encoding.

func (encoding *Encoding) SerializationMethod() *SerializationMethod
    SerializationMethod returns a serialization method of request body.
    When serialization method is not defined the method returns the default
    serialization method.

func (encoding *Encoding) UnmarshalJSON(data []byte) error
    UnmarshalJSON sets Encoding to a copy of data.

func (encoding *Encoding) Validate(ctx context.Context, opts ...ValidationOption) error
    Validate returns an error if Encoding does not comply with the OpenAPI spec.

func (encoding *Encoding) WithHeader(name string, header *Header) *Encoding

func (encoding *Encoding) WithHeaderRef(name string, ref *HeaderRef) *Encoding

type Encodings map[string]*Encoding
    Encodings is a map of encoding objects keyed by field name.

type ExactlyOneFieldError struct {
	// Fields is the set of fields, exactly one of which must be set
	// (e.g. ["content", "schema"]).
	Fields []string
	// Cause is the underlying leaf error. Walked by errors.Unwrap.
	Cause error
	// Origin is the source location of the offending element when the
	// document was loaded with Loader.IncludeOrigin = true.
	Origin *Origin
}
    ExactlyOneFieldError clusters "exactly one of these fields must be set"
    failures — e.g. a parameter or header where neither content nor schema is
    set, or both are.

func (e *ExactlyOneFieldError) Error() string

func (e *ExactlyOneFieldError) Unwrap() error

type Example struct {
	Extensions map[string]any `json:"-" yaml:"-"`
	Origin     *Origin        `json:"-" yaml:"-"`

	Summary       string `json:"summary,omitempty" yaml:"summary,omitempty"`
	Description   string `json:"description,omitempty" yaml:"description,omitempty"`
	Value         any    `json:"value,omitempty" yaml:"value,omitempty"`
	ExternalValue string `json:"externalValue,omitempty" yaml:"externalValue,omitempty"`
}
    Example is specified by OpenAPI/Swagger 3.0 standard. See
    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#example-object

func NewExample(value any) *Example

func (example Example) MarshalJSON() ([]byte, error)
    MarshalJSON returns the JSON encoding of Example.

func (example Example) MarshalYAML() (any, error)
    MarshalYAML returns the YAML encoding of Example.

func (example *Example) UnmarshalJSON(data []byte) error
    UnmarshalJSON sets Example to a copy of data.

func (example *Example) Validate(ctx context.Context, opts ...ValidationOption) error
    Validate returns an error if Example does not comply with the OpenAPI spec.

type ExampleRef struct {
	// Extensions only captures fields starting with 'x-' as no other fields
	// are allowed by the openapi spec.
	Extensions map[string]any
	Origin     *Origin `json:"-" yaml:"-"`
	// Reference Object summary and description are supported in OpenAPI 3.1+.
	Summary     *string `json:"summary,omitempty" yaml:"summary,omitempty"`
	Description *string `json:"description,omitempty" yaml:"description,omitempty"`

	Ref   string
	Value *Example

	// Has unexported fields.
}
    ExampleRef represents either a Example or a $ref to a Example. When
    serializing and both fields are set, Ref is preferred over Value.

func (x *ExampleRef) CollectionName() string
    CollectionName returns the JSON string used for a collection of these
    components.

func (x *ExampleRef) JSONLookup(token string) (any, error)
    JSONLookup implements
    https://pkg.go.dev/github.com/go-openapi/jsonpointer#JSONPointable

func (x ExampleRef) MarshalJSON() ([]byte, error)
    MarshalJSON returns the JSON encoding of ExampleRef.

func (x ExampleRef) MarshalYAML() (any, error)
    MarshalYAML returns the YAML encoding of ExampleRef.

func (x *ExampleRef) RefPath() *url.URL
    RefPath returns the path of the $ref relative to the root document.

func (x *ExampleRef) RefString() string
    RefString returns the $ref value.

func (x *ExampleRef) UnmarshalJSON(data []byte) error
    UnmarshalJSON sets ExampleRef to a copy of data.

func (x *ExampleRef) Validate(ctx context.Context, opts ...ValidationOption) error
    Validate returns an error if ExampleRef does not comply with the OpenAPI
    spec.

type ExampleValueExternalValueExclusive struct{ ValidationError }

func (e *ExampleValueExternalValueExclusive) As(target any) bool

func (e *ExampleValueExternalValueExclusive) Code() string

type ExampleValueOrExternalValueRequired struct{ ValidationError }

func (e *ExampleValueOrExternalValueRequired) As(target any) bool

func (e *ExampleValueOrExternalValueRequired) Code() string

type ExampleViolatesSchema struct{ SchemaValueError }
    ExampleViolatesSchema and DefaultViolatesSchema mark which schema value kind
    failed. They embed SchemaValueError, and their As exposes it, so errors.As
    with a *SchemaValueError target keeps matching.

func (e *ExampleViolatesSchema) As(target any) bool

func (e *ExampleViolatesSchema) Code() string

type Examples map[string]*ExampleRef // Examples represents components' named examples

func (m Examples) JSONLookup(token string) (any, error)
    JSONLookup implements
    https://pkg.go.dev/github.com/go-openapi/jsonpointer#JSONPointable

type ExamplesFieldFor31Plus struct{ ValidationError }

func (e *ExamplesFieldFor31Plus) As(target any) bool

func (e *ExamplesFieldFor31Plus) Code() string

type ExclusiveBound struct {
	Bool  *bool    // For OpenAPI 3.0 style (modifier for min/max)
	Value *float64 // For OpenAPI 3.1 style (actual bound value)
}
    ExclusiveBound represents exclusiveMinimum/exclusiveMaximum which changed
    type between OpenAPI versions. In OpenAPI 3.0 (JSON Schema draft-04):
    boolean that modifies minimum/maximum In OpenAPI 3.1 (JSON Schema 2020-12):
    number representing the actual exclusive bound

func (eb ExclusiveBound) IsSet() bool
    IsSet returns true if either Bool or Value is set.

func (eb ExclusiveBound) IsTrue() bool
    IsTrue returns true if the bound is set as a boolean true (OpenAPI 3.0
    style).

func (eb ExclusiveBound) MarshalJSON() ([]byte, error)
    MarshalJSON returns the JSON encoding of ExclusiveBound.

func (eb ExclusiveBound) MarshalYAML() (any, error)
    MarshalYAML returns the YAML encoding of ExclusiveBound.

func (eb *ExclusiveBound) UnmarshalJSON(data []byte) error
    UnmarshalJSON sets ExclusiveBound to a copy of data.

type ExternalDocs struct {
	Extensions map[string]any `json:"-" yaml:"-"`
	Origin     *Origin        `json:"-" yaml:"-"`

	Description string `json:"description,omitempty" yaml:"description,omitempty"`
	URL         string `json:"url,omitempty" yaml:"url,omitempty"`
}
    ExternalDocs is specified by OpenAPI/Swagger standard version 3. See
    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#external-documentation-object

func (e ExternalDocs) MarshalJSON() ([]byte, error)
    MarshalJSON returns the JSON encoding of ExternalDocs.

func (e ExternalDocs) MarshalYAML() (any, error)
    MarshalYAML returns the YAML encoding of ExternalDocs.

func (e *ExternalDocs) UnmarshalJSON(data []byte) error
    UnmarshalJSON sets ExternalDocs to a copy of data.

func (e *ExternalDocs) Validate(ctx context.Context, opts ...ValidationOption) error
    Validate returns an error if ExternalDocs does not comply with the OpenAPI
    spec.

type ExternalDocsURLRequired struct{ ValidationError }

func (e *ExternalDocsURLRequired) As(target any) bool

func (e *ExternalDocsURLRequired) Code() string

type ExternalDocsURLValidationError struct {
	Cause error
}
    ExternalDocsURLValidationError wraps the URL parse failure on an
    ExternalDocs object.

func (e *ExternalDocsURLValidationError) Error() string

func (e *ExternalDocsURLValidationError) Unwrap() error

type ExtraSiblingFieldsError struct {
	// Fields is the list of unexpected sibling field names.
	Fields []string
	// Origin is the source location of the parent object that carries
	// the extra siblings when the document was loaded with
	// Loader.IncludeOrigin = true.
	Origin *Origin
}
    ExtraSiblingFieldsError clusters "unexpected sibling fields" failures. Most
    commonly this fires when fields appear alongside a $ref that the OpenAPI
    spec doesn't allow there, or as unknown keys on objects whose only permitted
    extras are `x-` extensions. Carries the offending field names so callers can
    render or filter.

func (e *ExtraSiblingFieldsError) Code() string

func (e *ExtraSiblingFieldsError) Error() string

type FieldVersionMismatchError struct {
	// Field is the field name flagged (e.g. "summary", "identifier",
	// "$defs", "prefixItems", "contains", ...).
	Field string
	// MinVersion is the minimum OpenAPI version that allows the field
	// (e.g. "3.1").
	MinVersion string
	// Cause is the underlying leaf error. Walked by errors.Unwrap.
	Cause error
	// Origin is the source location of the offending element when the
	// document was loaded with Loader.IncludeOrigin = true. Nil for
	// document-root fields (Loader doesn't track Origin on *T) and on
	// loads where origin tracking was off.
	Origin *Origin
}
    FieldVersionMismatchError clusters "field X is for OpenAPI >=Y" failures
    (3.1+ keywords used in 3.0 documents). Carries the field name and minimum
    version, wraps the per-site leaf.

func (e *FieldVersionMismatchError) Error() string

func (e *FieldVersionMismatchError) Unwrap() error

type ForbiddenFieldError struct {
	// Field is the name of the forbidden field (e.g. "name", "in",
	// "authorizationUrl", "tokenUrl").
	Field string
	// Cause is the underlying leaf error. Walked by errors.Unwrap.
	Cause error
	// Origin is the source location of the offending element when the
	// document was loaded with Loader.IncludeOrigin = true.
	Origin *Origin
}
    ForbiddenFieldError clusters "field X must not be set in this context"
    failures (header.name and header.in inside a Headers map, OAuth flow URLs
    that don't apply to the chosen flow type).

func (e *ForbiddenFieldError) Error() string

func (e *ForbiddenFieldError) Unwrap() error

type FormatValidator[T any] interface {
	Validate(value T) error
}
    FormatValidator is an interface for custom format validators.

func NewCallbackValidator[T any](fn func(T) error) FormatValidator[T]
    NewCallbackValidator creates a new FormatValidator that uses a callback
    function to validate the value.

func NewIPValidator(isIPv4 bool) FormatValidator[string]
    NewIPValidator creates a new FormatValidator that validates the value is an
    IP address.

func NewRangeFormatValidator[T int64 | float64](min, max T) FormatValidator[T]
    NewRangeFormatValidator creates a new FormatValidator that validates the
    value is within a given range.

type Header struct {
	Parameter
}
    Header is specified by OpenAPI/Swagger 3.0 standard. See
    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#header-object

func (header Header) JSONLookup(token string) (any, error)
    JSONL
... [truncated, file is 158597 chars]
```

### .github/docs/openapi3filter.txt
```
package openapi3filter // import "github.com/getkin/kin-openapi/openapi3filter"

Package openapi3filter validates that requests and inputs request an OpenAPI 3
specification file.

CONSTANTS

const (
	// ErrCodeOK indicates no error. It is also the default value.
	ErrCodeOK = 0
	// ErrCodeCannotFindRoute happens when the validator fails to resolve the
	// request to a defined OpenAPI route.
	ErrCodeCannotFindRoute = iota
	// ErrCodeRequestInvalid happens when the inbound request does not conform
	// to the OpenAPI 3 specification.
	ErrCodeRequestInvalid = iota
	// ErrCodeResponseInvalid happens when the wrapped handler response does
	// not conform to the OpenAPI 3 specification.
	ErrCodeResponseInvalid = iota
)

VARIABLES

var ErrAuthenticationServiceMissing = errors.New("missing AuthenticationFunc")
    ErrAuthenticationServiceMissing is returned when no authentication service
    is defined for the request validator

var ErrInvalidEmptyValue = errors.New("empty value is not allowed")
    ErrInvalidEmptyValue is returned when a value of a parameter or request body
    is empty while it's not allowed.

var ErrInvalidRequired = errors.New("value is required but missing")
    ErrInvalidRequired is returned when a required value of a parameter or
    request body is not defined.

var JSONPrefixes = []string{
	")]}',\n",
}

FUNCTIONS

func ConvertErrors(err error) error
    ConvertErrors converts all errors to the appropriate error format.

func CsvBodyDecoder(body io.Reader, header http.Header, schema *openapi3.SchemaRef, encFn EncodingFn) (any, error)
    CsvBodyDecoder is a body decoder that decodes a csv body to a string.

func DefaultErrorEncoder(_ context.Context, err error, w http.ResponseWriter)
    DefaultErrorEncoder writes the error to the ResponseWriter, by default a
    content type of text/plain, a body of the plain text of the error, and a
    status code of 500. If the error implements Headerer, the provided headers
    will be applied to the response. If the error implements json.Marshaler,
    and the marshaling succeeds, a content type of application/json and the JSON
    encoded form of the error will be used. If the error implements StatusCoder,
    the provided StatusCode will be used instead of 500.

func FileBodyDecoder(body io.Reader, header http.Header, schema *openapi3.SchemaRef, encFn EncodingFn) (any, error)
    FileBodyDecoder is a body decoder that decodes a file body to a string.

func JSONBodyDecoder(body io.Reader, header http.Header, schema *openapi3.SchemaRef, encFn EncodingFn) (any, error)
    JSONBodyDecoder decodes a JSON formatted body. It is public so that is easy
    to register additional JSON based formats.

func MultipartBodyDecoder(body io.Reader, header http.Header, schema *openapi3.SchemaRef, encFn EncodingFn) (any, error)
func NoopAuthenticationFunc(context.Context, *AuthenticationInput) error
    NoopAuthenticationFunc is an AuthenticationFunc

func PlainBodyDecoder(body io.Reader, header http.Header, schema *openapi3.SchemaRef, encFn EncodingFn) (any, error)
func RegisterBodyDecoder(contentType string, decoder BodyDecoder)
    RegisterBodyDecoder registers a request body's decoder for a content type.

    If a decoder for the specified content type already exists, the function
    replaces it with the specified decoder. This call is not thread-safe:
    body decoders should not be created/destroyed by multiple goroutines.

func RegisterBodyEncoder(contentType string, encoder BodyEncoder)
    RegisterBodyEncoder enables package-wide decoding of contentType values

func TrimJSONPrefix(data []byte) []byte
    TrimJSONPrefix trims one of the possible prefixes

func UnregisterBodyDecoder(contentType string)
    UnregisterBodyDecoder dissociates a body decoder from a content type.

    Decoding this content type will result in an error. This call is not
    thread-safe: body decoders should not be created/destroyed by multiple
    goroutines.

func UnregisterBodyEncoder(contentType string)
    UnregisterBodyEncoder disables package-wide decoding of contentType values

func UrlencodedBodyDecoder(body io.Reader, header http.Header, schema *openapi3.SchemaRef, encFn EncodingFn) (any, error)
func ValidateParameter(ctx context.Context, input *RequestValidationInput, parameter *openapi3.Parameter) error
    ValidateParameter validates a parameter's value by JSON schema. The function
    returns RequestError with a ParseError cause when unable to parse a value.
    The function returns RequestError with ErrInvalidRequired cause when a value
    of a required parameter is not defined. The function returns RequestError
    with ErrInvalidEmptyValue cause when a value of a required parameter is not
    defined. The function returns RequestError with a openapi3.SchemaError cause
    when a value is invalid by JSON schema.

func ValidateRequest(ctx context.Context, input *RequestValidationInput) error
    ValidateRequest is used to validate the given input according to previous
    loaded OpenAPIv3 spec. If the input does not match the OpenAPIv3 spec,
    a non-nil error will be returned.

    Note: One can tune the behavior of uniqueItems: true verification by
    registering a custom function with openapi3.RegisterArrayUniqueItemsChecker

func ValidateRequestBody(ctx context.Context, input *RequestValidationInput, requestBody *openapi3.RequestBody) error
    ValidateRequestBody validates data of a request's body.

    The function returns RequestError with ErrInvalidRequired cause when a
    value is required but not defined. The function returns RequestError with a
    openapi3.SchemaError cause when a value is invalid by JSON schema.

func ValidateResponse(ctx context.Context, input *ResponseValidationInput) error
    ValidateResponse is used to validate the given input according to previous
    loaded OpenAPIv3 spec. If the input does not match the OpenAPIv3 spec,
    a non-nil error will be returned.

    Note: One can tune the behavior of uniqueItems: true verification by
    registering a custom function with openapi3.RegisterArrayUniqueItemsChecker

func ValidateSecurityRequirements(ctx context.Context, input *RequestValidationInput, srs openapi3.SecurityRequirements) error
    ValidateSecurityRequirements goes through multiple OpenAPI 3 security
    requirements in order and returns nil on the first valid requirement.
    If no requirement is met, errors are returned in order.

func YamlBodyDecoder(body io.Reader, header http.Header, schema *openapi3.SchemaRef, encFn EncodingFn) (any, error)
func ZipFileBodyDecoder(body io.Reader, header http.Header, schema *openapi3.SchemaRef, encFn EncodingFn) (any, error)
    ZipFileBodyDecoder is a body decoder that decodes a zip file body to a
    string. Use with caution as this implementation may be susceptible to a zip
    bomb attack.


TYPES

type AuthenticationFunc func(context.Context, *AuthenticationInput) error
    AuthenticationFunc allows for custom security requirement
    validation. A non-nil error fails authentication according to
    https://spec.openapis.org/oas/v3.1.0#security-requirement-object See
    ValidateSecurityRequirements

type AuthenticationInput struct {
	RequestValidationInput *RequestValidationInput
	SecuritySchemeName     string
	SecurityScheme         *openapi3.SecurityScheme
	Scopes                 []string
}

func (input *AuthenticationInput) NewError(err error) error

type BodyDecoder func(io.Reader, http.Header, *openapi3.SchemaRef, EncodingFn) (any, error)
    BodyDecoder is an interface to decode a body of a request or response.
    An implementation must return a value that is a primitive, []any,
    or map[string]any.

func RegisteredBodyDecoder(contentType string) BodyDecoder
    RegisteredBodyDecoder returns the registered body decoder for the given
    content type.

    If no decoder was registered for the given content type, nil is returned.
    This call is not thread-safe: body decoders should not be created/destroyed
    by multiple goroutines.

type BodyEncoder func(body any) ([]byte, error)
    BodyEncoder really is an (encoding/json).Marshaler

func RegisteredBodyEncoder(contentType string) BodyEncoder
    RegisteredBodyEncoder returns the registered body encoder for the given
    content type.

    If no encoder was registered for the given content type, nil is returned.

type ContentParameterDecoder func(param *openapi3.Parameter, values []string) (any, *openapi3.Schema, error)
    A ContentParameterDecoder takes a parameter definition from the OpenAPI
    spec, and the value which we received for it. It is expected to return the
    value unmarshaled into an interface which can be traversed for validation,
    it should also return the schema to be used for validating the object,
    since there can be more than one in the content spec.

    If a query parameter appears multiple times, values[] will have more than
    one value, but for all other parameter types it should have just one.

type CustomSchemaErrorFunc func(err *openapi3.SchemaError) string
    CustomSchemaErrorFunc allows for custom the schema error message.

type EncodingFn func(partName string) *openapi3.Encoding
    EncodingFn is a function that returns an encoding of a request body's part.

type ErrCode int
    ErrCode is used for classification of different types of errors that may
    occur during validation. These may be used to write an appropriate response
    in ErrFunc.

type ErrFunc func(ctx context.Context, w http.ResponseWriter, status int, code ErrCode, err error)
    ErrFunc handles errors that may occur during validation.

type ErrorEncoder func(ctx context.Context, err error, w http.ResponseWriter)
    ErrorEncoder is responsible for encoding an error to the ResponseWriter.
    Users are encouraged to use custom ErrorEncoders to encode HTTP errors to
    their clients, and will likely want to pass and check for their own error
    types. See the example shipping/handling service.

type Headerer interface {
	Headers() http.Header
}
    Headerer is checked by DefaultErrorEncoder. If an error value implements
    Headerer, the provided headers will be applied to the response writer,
    after the Content-Type is set.

type LogFunc func(ctx context.Context, message string, err error)
    LogFunc handles log messages that may occur during validation.

type Options struct {
	// Set ExcludeRequestBody so ValidateRequest skips request body validation
	ExcludeRequestBody bool

	// Set ExcludeRequestQueryParams so ValidateRequest skips request query params validation
	ExcludeRequestQueryParams bool

	// Set ExcludeResponseBody so ValidateResponse skips response body validation
	ExcludeResponseBody bool

	// Set ExcludeReadOnlyValidations so ValidateRequest skips read-only validations
	ExcludeReadOnlyValidations bool

	// Set ExcludeWriteOnlyValidations so ValidateResponse skips write-only validations
	ExcludeWriteOnlyValidations bool

	// Set IncludeResponseStatus so ValidateResponse fails on response
	// status not defined in OpenAPI spec
	IncludeResponseStatus bool

	MultiError bool

	// Set RegexCompiler to override the regex implementation
	RegexCompiler openapi3.RegexCompilerFunc

	// Set RejectWhenRequestBodyNotSpecified so ValidateRequest fails when request body is present but not defined in the specification
	RejectWhenRequestBodyNotSpecified bool

	// A document with security schemes defined will not pass validation
	// unless an AuthenticationFunc is defined.
	// See NoopAuthenticationFunc
	AuthenticationFunc AuthenticationFunc

	// Indicates whether default values are set in the
	// request. If true, then they are not set
	SkipSettingDefaults bool

	// Additional schema validation options to pass through to schema validation.
	// Use this to pass document-scoped format validators or other per-validation options.
	SchemaValidationOptions []openapi3.SchemaValidationOption
	// Has unexported fields.
}
    Options used by ValidateRequest and ValidateResponse

func (o *Options) WithCustomSchemaErrorFunc(f CustomSchemaErrorFunc)
    WithCustomSchemaErrorFunc sets a function to override the schema error
    message. If the passed function returns an empty string, it returns to the
    previous Error() implementation.

type ParseError struct {
	Kind   ParseErrorKind
	Value  any
	Reason string
	Cause  error

	// Has unexported fields.
}
    ParseError describes errors which happens while parse operation's
    parameters, requestBody, or response.

func (e *ParseError) Error() string

func (e *ParseError) Path() []any
    Path returns a path to the root cause.

func (e *ParseError) RootCause() error
    RootCause returns a root cause of ParseError.

func (e ParseError) Unwrap() error

type ParseErrorKind int
    ParseErrorKind describes a kind of ParseError. The type simplifies
    comparison of errors.

const (
	// KindOther describes an untyped parsing error.
	KindOther ParseErrorKind = iota
	// KindUnsupportedFormat describes an error that happens when a value has an unsupported format.
	KindUnsupportedFormat
	// KindInvalidFormat describes an error that happens when a value does not conform a format
	// that is required by a serialization method.
	KindInvalidFormat
)
type RequestError struct {
	Input       *RequestValidationInput
	Parameter   *openapi3.Parameter
	RequestBody *openapi3.RequestBody
	Reason      string
	Err         error
}
    RequestError is returned by ValidateRequest when request does not match
    OpenAPI spec

func (err *RequestError) Error() string

func (err RequestError) Unwrap() error

type RequestValidationInput struct {
	Request      *http.Request
	PathParams   map[string]string
	QueryParams  url.Values
	Route        *routers.Route
	Options      *Options
	ParamDecoder ContentParameterDecoder
}

func (input *RequestValidationInput) GetQueryParams() url.Values

type ResponseError struct {
	Input  *ResponseValidationInput
	Reason string
	Err    error
}
    ResponseError is returned by ValidateResponse when response does not match
    OpenAPI spec

func (err *ResponseError) Error() string

func (err ResponseError) Unwrap() error

type ResponseValidationInput struct {
	RequestValidationInput *RequestValidationInput
	Status                 int
	Header                 http.Header
	Body                   io.ReadCloser
	Options                *Options
}

func (input *ResponseValidationInput) SetBodyBytes(value []byte) *ResponseValidationInput

type SecurityRequirementsError struct {
	SecurityRequirements openapi3.SecurityRequirements
	Errors               []error
}
    SecurityRequirementsError is returned by ValidateSecurityRequirements when
    no requirement is met.

func (err *SecurityRequirementsError) Error() string

func (err SecurityRequirementsError) Unwrap() []error

type StatusCoder interface {
	StatusCode() int
}
    StatusCoder is checked by DefaultErrorEncoder. If an error value implements
    StatusCoder, the StatusCode will be used when encoding the error.
    By default, StatusInternalServerError (500) is used.

type ValidationError struct {
	// A unique identifier for this particular occurrence of the problem.
	Id string `json:"id,omitempty" yaml:"id,omitempty"`
	// The HTTP status code applicable to this problem.
	Status int `json:"status,omitempty" yaml:"status,omitempty"`
	// An application-specific error code, expressed as a string value.
	Code string `json:"code,omitempty" yaml:"code,omitempty"`
	// A short, human-readable summary of the problem. It **SHOULD NOT** change from occurrence to occurrence of the problem, except for purposes of localization.
	Title string `json:"title,omitempty" yaml:"title,omitempty"`
	// A human-readable explanation specific to this occurrence of the problem.
	Detail string `json:"detail,omitempty" yaml:"detail,omitempty"`
	// An object containing references to the source of the error
	Source *ValidationErrorSource `json:"source,omitempty" yaml:"source,omitempty"`
}
    ValidationError struct provides granular error information useful
    for communicating issues back to end user and developer. Based on
    https://jsonapi.org/format/#error-objects

func (e *ValidationError) Error() string
    Error implements the error interface.

func (e *ValidationError) StatusCode() int
    StatusCode implements the StatusCoder interface for DefaultErrorEncoder

type ValidationErrorEncoder struct {
	Encoder ErrorEncoder
}
    ValidationErrorEncoder wraps a base ErrorEncoder to handle ValidationErrors

func (enc *ValidationErrorEncoder) Encode(ctx context.Context, err error, w http.ResponseWriter)
    Encode implements the ErrorEncoder interface for encoding ValidationErrors

type ValidationErrorSource struct {
	// A JSON Pointer [RFC6901] to the associated entity in the request document [e.g. \"/data\" for a primary data object, or \"/data/attributes/title\" for a specific attribute].
	Pointer string `json:"pointer,omitempty" yaml:"pointer,omitempty"`
	// A string indicating which query parameter caused the error.
	Parameter string `json:"parameter,omitempty" yaml:"parameter,omitempty"`
}
    ValidationErrorSource struct

type ValidationHandler struct {
	Handler            http.Handler
	AuthenticationFunc AuthenticationFunc
	File               string
	ErrorEncoder       ErrorEncoder
	// Has unexported fields.
}

func (h *ValidationHandler) Load() error

func (h *ValidationHandler) Middleware(next http.Handler) http.Handler
    Middleware implements gorilla/mux MiddlewareFunc

func (h *ValidationHandler) ServeHTTP(w http.ResponseWriter, r *http.Request)

type Validator struct {
	// Has unexported fields.
}
    Validator provides HTTP request and response validation middleware.

func NewValidator(router routers.Router, options ...ValidatorOption) *Validator
    NewValidator returns a new response validation middleware, using the given
    routes from an OpenAPI 3 specification.

func (v *Validator) Middleware(h http.Handler) http.Handler
    Middleware returns an http.Handler which wraps the given handler with
    request and response validation.

type ValidatorOption func(*Validator)
    ValidatorOption defines an option that may be specified when creating a
    Validator.

func OnErr(f ErrFunc) ValidatorOption
    OnErr provides a callback that handles writing an HTTP response on a
    validation error. This allows customization of error responses without
    prescribing a particular form. This callback is only called on response
    validator errors in Strict mode.

func OnLog(f LogFunc) ValidatorOption
    OnLog provides a callback that handles logging in the Validator. This allows
    the validator to integrate with a services' existing logging system without
    prescribing a particular one.

func Strict(strict bool) ValidatorOption
    Strict, if set, causes an internal server error to be sent if the wrapped
    handler response fails response validation. If not set, the response is sent
    and the error is only logged.

func ValidationOptions(options Options) ValidatorOption
    ValidationOptions sets request/response validation options on the validator.


```

### README.md
```
[![CI](https://github.com/getkin/kin-openapi/workflows/go/badge.svg)](https://github.com/getkin/kin-openapi/actions)
[![Go Reference](https://pkg.go.dev/badge/github.com/getkin/kin-openapi.svg)](https://pkg.go.dev/github.com/getkin/kin-openapi)
[![Join Gitter Chat Channel -](https://badges.gitter.im/getkin/kin.svg)](https://gitter.im/getkin/kin?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# Introduction
A [Go](https://go.dev) project for handling [OpenAPI](https://www.openapis.org/) files. We target:
* [OpenAPI `v2.0`](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/2.0.md) (formerly known as Swagger)
* [OpenAPI `v3.0`](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md)
* [OpenAPI `v3.1`](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md) Soon! [Tracking issue here.](https://github.com/getkin/kin-openapi/issues/230)

Licensed under the [MIT License](./LICENSE).

## Contributors, users and sponsors
The project has received pull requests [from many people](https://github.com/getkin/kin-openapi/graphs/contributors). Thanks to everyone!

Please, [give back to this project](https://github.com/sponsors/fenollp) by becoming a sponsor.

Here's some projects that depend on _kin-openapi_:
  * [github.com/go-fuego/fuego](https://github.com/go-fuego/fuego) - "Framework generating OpenAPI 3 spec from source code"
  * [github.com/a-h/rest](https://github.com/a-h/rest) - "Generate OpenAPI 3.0 specifications from Go code without annotations or magic comments"
  * [github.com/Tufin/oasdiff](https://github.com/Tufin/oasdiff) - "A diff tool for OpenAPI Specification 3"
  * [github.com/danielgtaylor/apisprout](https://github.com/danielgtaylor/apisprout) - "Lightweight, blazing fast, cross-platform OpenAPI 3 mock server with validation"
  * [github.com/oapi-codegen/oapi-codegen](https://github.com/oapi-codegen/oapi-codegen) - "Generate Go client and server boilerplate from OpenAPI 3 specifications"
  * [github.com/dunglas/vulcain](https://github.com/dunglas/vulcain) - "Use HTTP/2 Server Push to create fast and idiomatic client-driven REST APIs"
  * [github.com/danielgtaylor/restish](https://github.com/danielgtaylor/restish) - "...a CLI for interacting with REST-ish HTTP APIs with some nice features built-in"
  * [github.com/goadesign/goa](https://github.com/goadesign/goa) - "Design-based APIs and microservices in Go"
  * [github.com/hashicorp/nomad-openapi](https://github.com/hashicorp/nomad-openapi) - "Nomad is an easy-to-use, flexible, and performant workload orchestrator that can deploy a mix of microservice, batch, containerized, and non-containerized applications. Nomad is easy to operate and scale and has native Consul and Vault integrations."
  * [gitlab.com/jamietanna/httptest-openapi](https://gitlab.com/jamietanna/httptest-openapi) ([*blog post*](https://www.jvt.me/posts/2022/05/22/go-openapi-contract-test/)) - "Go OpenAPI Contract Verification for use with `net/http`"
  * [github.com/SIMITGROUP/openapigenerator](https://github.com/SIMITGROUP/openapigenerator) - "Openapi v3 microservices generator"
  * [https://github.com/projectsveltos/addon-controller](https://github.com/projectsveltos/addon-controller) - "Kubernetes add-on controller designed to manage tens of clusters."
  * (Feel free to add your project by [creating an issue](https://github.com/getkin/kin-openapi/issues/new) or a pull request)

## Alternatives
* [libopenapi](https://github.com/pb33f/libopenapi) a fully featured, high performance OpenAPI 3.1, 3.0 and Swagger parser, library, validator and toolkit
* [go-swagger](https://github.com/go-swagger/go-swagger) stated [*OpenAPIv3 won't be supported*](https://github.com/go-swagger/go-swagger/issues/1122#issuecomment-575968499)
* [swaggo](https://github.com/swaggo/swag) has an [open issue on OpenAPIv3](https://github.com/swaggo/swag/issues/386)

Be sure to check [OpenAPI Initiative](https://github.com/OAI)'s [great tooling list](https://github.com/OAI/OpenAPI-Specification/blob/master/IMPLEMENTATIONS.md) as well as [OpenAPI.Tools](https://openapi.tools/).

# Structure
  * _openapi2_ ([Go Reference](https://pkg.go.dev/github.com/getkin/kin-openapi/openapi2))
    * Support for OpenAPI 2 files, including serialization, deserialization, and validation.
  * _openapi2conv_ ([Go Reference](https://pkg.go.dev/github.com/getkin/kin-openapi/openapi2conv))
    * Converts OpenAPI 2 files into OpenAPI 3 files.
  * _openapi3_ ([Go Reference](https://pkg.go.dev/github.com/getkin/kin-openapi/openapi3))
    * Support for OpenAPI 3 files, including serialization, deserialization, and validation.
  * _openapi3filter_ ([Go Reference](https://pkg.go.dev/github.com/getkin/kin-openapi/openapi3filter))
    * Validates HTTP requests and responses
    * Provides a [gorilla/mux](https://github.com/gorilla/mux) router for OpenAPI operations
  * _openapi3gen_ ([Go Reference](https://pkg.go.dev/github.com/getkin/kin-openapi/openapi3gen))
    * Generates `*openapi3.Schema` values for Go types.

# Some recipes
## Validating an OpenAPI document
```shell
go run github.com/getkin/kin-openapi/cmd/validate@latest [--defaults] [--examples] [--ext] [--patterns] -- <local YAML or JSON file>
```

## Loading OpenAPI document
Use `openapi3.Loader`, which resolves all references:
```go
loader := openapi3.NewLoader()
doc, err := loader.LoadFromFile("my-openapi-spec.json")
```

## Tracking source locations (Origin)

When `IncludeOrigin` is enabled, the loader records the file, line, and column of each element in the OpenAPI document. This is useful for tools that need to report errors or changes with precise source locations (e.g. linters, diff tools, editors).

```go
loader := openapi3.NewLoader()
loader.IncludeOrigin = true
doc, err := loader.LoadFromFile("my-openapi-spec.json")

// Each element has an Origin field with source location info
fmt.Println(doc.Info.Origin.Key.File)   // "my-openapi-spec.json"
fmt.Println(doc.Info.Origin.Key.Line)   // 2
fmt.Println(doc.Info.Origin.Key.Column) // 1
```

The `Origin` struct contains three parts:
- **`Key`** — the location of the object itself (file, line, column).
- **`Fields`** — locations of scalar fields within the object (e.g. `origin.Fields["description"]` gives the line of the `description` field).
- **`Sequences`** — locations of items in sequence-valued fields. For example, `origin.Sequences["enum"]` gives the location of each item in an `enum` array. This is used for fields like `enum`, `required`, and `servers` where the individual items are scalars and don't have their own `Origin` field.

Origin data is populated by an internal post-processing step after YAML decoding — it is not part of the OpenAPI spec itself. For this reason, Origin fields are excluded from serialization. If you marshal a loaded document back to JSON/YAML, origin data will not appear in the output.

## Identifying validation errors by code

Each validation error carries a stable, kebab-case code (e.g. `operation-responses-required`), independent of the message text, so tools can suppress specific findings, assign per-rule severities, or emit machine-readable diagnostics. The full catalog is available from `openapi3.ValidationErrorCodes()`.

```go
err := doc.Validate(ctx, openapi3.EnableMultiError())
for _, e := range err.(openapi3.MultiError) {
	var coded openapi3.CodedError
	if errors.As(e, &coded) {
		fmt.Println(coded.Code(), e) // e.g. "operation-responses-required value of responses must be an object"
	}
}
```

## Getting OpenAPI operation that matches request
```go
loader := openapi3.NewLoader()
doc, _ := loader.LoadFromData([]byte(`...`))
_ = doc.Validate(loader.Context)
router, _ := gorillamux.NewRouter(doc)
route, pathParams, _ := router.FindRoute(httpRequest)
// Do something with route.Operation
```

## Validating HTTP requests/responses
```go
package main

import (
	"context"
	"fmt"
	"net/http"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/getkin/kin-openapi/openapi3filter"
	"github.com/getkin/kin-openapi/routers/gorillamux"
)

func main() {
	ctx := context.Background()
	loader := &openapi3.Loader{Context: ctx, IsExternalRefsAllowed: true}
	doc, _ := loader.LoadFromFile(".../My-OpenAPIv3-API.yml")
	// Validate document
	_ = doc.Validate(ctx)
	router, _ := gorillamux.NewRouter(doc)
	httpReq, _ := http.NewRequest(http.MethodGet, "/items", nil)

	// Find route
	route, pathParams, _ := router.FindRoute(httpReq)

	// Validate request
	requestValidationInput := &openapi3filter.RequestValidationInput{
		Request:    httpReq,
		PathParams: pathParams,
		Route:      route,
	}
	_ = openapi3filter.ValidateRequest(ctx, requestValidationInput)

	// Handle that request
	// --> YOUR CODE GOES HERE <--
	responseHeaders := http.Header{"Content-Type": []string{"application/json"}}
	responseCode := 200
	responseBody := []byte(`{}`)

	// Validate response
	responseValidationInput := &openapi3filter.ResponseValidationInput{
		RequestValidationInput: requestValidationInput,
		Status:                 responseCode,
		Header:                 responseHeaders,
	}
	responseValidationInput.SetBodyBytes(responseBody)
	_ = openapi3filter.ValidateResponse(ctx, responseValidationInput)
}
```

## Custom content type for body of HTTP request/response

By default, the library parses a body of the HTTP request and response of [a few content types](https://github.com/getkin/kin-openapi/blob/6da871e0e170b7637eb568c265c08bc2b5d6e7a3/openapi3filter/req_resp_decoder.go#L1264) e.g. `"text/plain"` or `"application/json"`.
To support other content types you must register decoders for them:

```go
func main() {
	// ...

	// Register a body's decoder for content type "application/xml".
	openapi3filter.RegisterBodyDecoder("application/xml", xmlBodyDecoder)

	// Now you can validate HTTP request that contains a body with content type "application/xml".
	requestValidationInput := &openapi3filter.RequestValidationInput{
		Request:    httpReq,
		PathParams: pathParams,
		Route:      route,
	}
	if err := openapi3filter.ValidateRequest(ctx, requestValidationInput); err != nil {
		panic(err)
	}

	// ...

	// And you can validate HTTP response that contains a body with content type "application/xml".
	if err := openapi3filter.ValidateResponse(ctx, responseValidationInput); err != nil {
		panic(err)
	}
}

func xmlBodyDecoder(body io.Reader, h http.Header, schema *openapi3.SchemaRef, encFn openapi3filter.EncodingFn) (decoded any, err error) {
	// Decode body to a primitive, []any, or map[string]any.
}
```

## Custom function to check uniqueness of array items

By default, the library checks unique items using the following predefined function:

```go
func isSliceOfUniqueItems(xs []any) bool {
	s := len(xs)
	m := make(map[string]struct{}, s)
	for _, x := range xs {
		key, _ := json.Marshal(&x)
		m[string(key)] = struct{}{}
	}
	return s == len(m)
}
```

In the predefined function `json.Marshal` is used to generate a string that can
be used as a map key which is to check the uniqueness of an array
when the array items are objects or arrays. You can register
you own function according to your input data to get better performance:

```go
func main() {
	// ...

	// Register a customized function used to check uniqueness of array.
	openapi3.RegisterArrayUniqueItemsChecker(arrayUniqueItemsChecker)

	// ... other validate codes
}

func arrayUniqueItemsChecker(items []any) bool {
	// Check the uniqueness of the input slice
}
```

## Custom function to change schema error messages

By default, the error message returned when validating a value includes the error reason, the schema, and the input value.

For example, given the following schema:

```json
{
  "type": "string",
  "allOf": [
    { "pattern": "[A-Z]" },
    { "pattern": "[a-z]" },
    { "pattern": "[0-9]" },
    { "pattern": "[!@#$%^&*()_+=-?~]" }
  ]
}
```

Passing the input value `"secret"` to this schema will produce the following error message:

```
string doesn't match the regular expression "[A-Z]"
Schema:
  {
    "pattern": "[A-Z]"
  }

Value:
  "secret"
```

Including the original value in the error message can be helpful for debugging, but it may not be appropriate for sensitive information such as secrets.

To disable the extra details in the schema error message, you can set the `openapi3.SchemaErrorDetailsDisabled` option to `true`:

```go
func main() {
	// ...

	// Disable schema error detailed error messages
	openapi3.SchemaErrorDetailsDisabled = true

	// ... other validate codes
}
```

This will shorten the error message to present only the reason:

```
string doesn't match the regular expression "[A-Z]"
```

For more fine-grained control over the error message, you can pass a custom `openapi3filter.Options` object to `openapi3filter.RequestValidationInput` that includes a `openapi3filter.CustomSchemaErrorFunc`.

```go
func validationOptions() *openapi3filter.Options {
	options := &openapi3filter.Options{}
	options.WithCustomSchemaErrorFunc(safeErrorMessage)
	return options
}

func safeErrorMessage(err *openapi3.SchemaError) string {
	return err.Reason
}
```

This will change the schema validation errors to return only the `Reason` field, which is guaranteed to not include the original value.

## Reconciling component $ref types

`ReferencesComponentInRootDocument` is a useful helper function to check if a component reference
coincides with a reference in the root document's component objects fixed fields.

This can be used to determine if two schema definitions are of the same structure, helpful for
code generation tools when generating go type models.

```go
doc, err = loader.LoadFromFile("openapi.yml")

for _, path := range doc.Paths.InMatchingOrder() {
	pathItem := doc.Paths.Find(path)

	if pathItem.Get == nil || pathItem.Get.Responses.Status(200) {
		continue
	}

	for _, s := range pathItem.Get.Responses.Status(200).Value.Content {
		name, match := ReferencesComponentInRootDocument(doc, s.Schema)
		fmt.Println(path, match, name) // /record true #/components/schemas/BookRecord
	}
}
```

## CHANGELOG: Sub-v1 breaking API changes

### v0.143.0
* Removed the `openapi3.StringMap[V]` type (an internal helper for origin-aware map unmarshalling, obsolete since origin tracking moved to a separate `OriginTree` pass). `openapi3.Discriminator.Mapping` field type changed from `StringMap[MappingRef]` to `map[string]MappingRef`, and `openapi3.OAuthFlow.Scopes` from `StringMap[string]` to `map[string]string`.

### v0.137.0
* Reinstated `openapi3.*Ptr(..)` funcs for Go 1.25

### v0.136.0
* `openapi3.Schema.ExclusiveMin` and `openapi3.Schema.ExclusiveMax` fields changed from `bool` to `ExclusiveBound` (a union type holding `*bool` for OpenAPI 3.0 or `*float64` for OpenAPI 3.1).
* `openapi3.Schema.PrefixItems` field changed from `[]*SchemaRef` to `SchemaRefs`.
* `openapi3.Schema.UnevaluatedItems` and `openapi3.Schema.UnevaluatedProperties` fields changed from `*SchemaRef` to `BoolSchema` (a union type accepting either a boolean or a schema object).
* Removed `openapi3.*Ptr(..)` funcs: they all can be replaced with `new(..)` since Go 1.26

### v0.135.0
* `openapi3.MediaType.Encoding` field type changed from `map[string]*Encoding` to `Encodings`
* `openapi3.Server.Variables` field type changed from `map[string]*ServerVariable` to `ServerVariables`

### v0.134.0
* `openapi3.Location` gained `File` and `Name` fields (`string` type, replacing previous `int`-only struct layout)
* `openapi3.Origin` gained `Sequences` field (`map[string][]Location`, extending previous `map[string]Location`-only struct)

### v0.131.0
* No longer `openapi3filter.RegisterBodyDecoder` the `openapi3filter.ZipFileBodyDecoder` by default.

### v0.129.0
* `openapi3.Discriminator.Mapping` and `openapi3.OAuthFlow.Scopes` fields went from a `map[string]string` to the new type `StringMap`

### v0.127.0
* Downgraded `github.com/gorilla/mux` dep from `1.8.1` to `1.8.0`.

### v0.126.0
* `openapi3.CircularReferenceError` and `openapi3.CircularReferenceCounter` are removed. `openapi3.Loader` now implements reference backtracking, so any kind of circular references should be properly resolved.
* `InternalizeRefs` now takes a refNameResolver that has access to `openapi3.T` and more properties of the reference needing resolving.
* The `DefaultRefNameResolver` has been updated, choosing names that will be less likely to collide with each other. Because of this internalized specs will likely change slightly.
* `openapi3.Format` and `openapi3.FormatCallback` are removed and the type of `openapi3.SchemaStringFormats` has changed.

### v0.125.0
* The `openapi3filter.ErrFunc` and `openapi3filter.LogFunc` func types now take the validated request's context as first argument.

### v0.124.0
* `openapi3.Schema.Type` & `openapi2.Parameter.Type` fields went from a `string` to the type `*Type` with methods: `Includes`, `Is`, `Permits` & `Slice`.

### v0.122.0
* `Paths` field of `openapi3.T` is now a pointer
* `Responses` field of `openapi3.Operation` is now a pointer
* `openapi3.Paths` went from `map[string]*PathItem` to a struct with an `Extensions` field and methods: `Set`, `Value`, `Len`, `Map`, and `New*`.
* `openapi3.Callback` went from `map[string]*PathItem` to a struct with an `Extensions` field and methods: `Set`, `Value`, `Len`, `Map`, and `New*`.
* `openapi3.Responses` went from `map[string]*ResponseRef` to a struct with an `Extensions` field and methods: `Set`, `Value`, `Len`, `Map`, and `New*`.
* `(openapi3.Responses).Get(int)` renamed to `(*openapi3.Responses).Status(int)`

### v0.121.0
* Introduce `openapi3.RequestBodies` (an alias on `map[string]*openapi3.ResponseRef`) and use it in place of `openapi3.Responses` for field `openapi3.Components.Responses`.

### v0.116.0
* Dropped `openapi3filter.DefaultOptions`. Use `&openapi3filter.Options{}` directly instead.

### v0.113.0
* The string format `email` has been removed by default. To use it please call `openapi3.DefineStringFormat("email", openapi3.FormatOfStringForEmail)`.
* Field `openapi3.T.Components` is now a pointer.
* Fields `openapi3.Schema.AdditionalProperties` and `openapi3.Schema.AdditionalPropertiesAllowed` are replaced by `openapi3.Schema.AdditionalProperties.Schema` and `openapi3.Schema.AdditionalProperties.Has` respectively.
* Type `openapi3.ExtensionProps` is now just `map[string]any` and extensions are accessible through the `Extensions` field.

### v0.112.0
* `(openapi3.ValidationOptions).ExamplesValidationDisabled` has been unexported.
* `(openapi3.ValidationOptions).SchemaFormatValidationEnabled` has been unexported.
* `(openapi3.ValidationOptions).SchemaPatternValidationDisabled` has been unexported.

### v0.111.0
* Changed `func (*_) Validate(ctx context.Context) error` to `func (*_) Validate(ctx context.Context, opts ...ValidationOption) error`.
* `openapi3.WithValidationOptions(ctx context.Context, opts *ValidationOptions) context.Context` prototype changed to `openapi3.WithValidationOptions(ctx context.Context, opts ...ValidationOption) context.Context`.

### v0.101.0
* `openapi3.SchemaFormatValidationDisabled` has been removed in favour of an option `openapi3.EnableSchemaFormatValidation()` passed to `openapi3.T.Validate`. The default behaviour is also now to not validate formats, as the OpenAPI spec mentions the `format` is an open value.

### v0.84.0
* The prototype of `openapi3gen.NewSchemaRefForValue` changed:
	* It no longer returns a map but that is still accessible under the field `(*Generator).SchemaRefs`.
	* It now takes in an additional argument (basically `doc.Components.Schemas`) which gets written to so `$ref` cycles can be properly handled.

### v0.61.0
* Renamed `openapi2.Swagger` to `openapi2.T`.
* Renamed `openapi2conv.FromV3Swagger` to `openapi2conv.FromV3`.
* Renamed `openapi2conv.ToV3Swagger` to `openapi2conv.ToV3`.
* Renamed `openapi3.LoadSwaggerFromData` to `openapi3.LoadFromData`.
* Renamed `openapi3.LoadSwaggerFromDataWithPath` to `openapi3.LoadFromDataWithPath`.
* Renamed `openapi3.LoadSwaggerFromFile` to `openapi3.LoadFromFile`.
* Renamed `openapi3.LoadSwaggerFromURI` to `openapi3.LoadFromURI`.
* Renamed `openapi3.NewSwaggerLoader` to `openapi3.NewLoader`.
* Renamed `openapi3.Swagger` to `openapi3.T`.
* Renamed `openapi3.SwaggerLoader` to `openapi3.Loader`.
* Renamed `openapi3filter.ValidationHandler.SwaggerFile` to `openapi3filter.ValidationHandler.File`.
* Renamed `routers.Route.Swagger` to `routers.Route.Spec`.

### v0.51.0
* Type `openapi3filter.Route` moved to `routers` (and `Route.Handler` was dropped. See https://github.com/getkin/kin-openapi/issues/329)
* Type `openapi3filter.RouteError` moved to `routers` (so did `ErrPathNotFound` and `ErrMethodNotAllowed` which are now `RouteError`s)
* Routers' `FindRoute(...)` method now takes only one argument: `*http.Request`
* `getkin/kin-openapi/openapi3filter.Router` moved to `getkin/kin-openapi/routers/legacy`
* `openapi3filter.NewRouter()` and its related `WithSwaggerFromFile(string)`, `WithSwagger(*openapi3.Swagger)`, `AddSwaggerFromFile(string)` and `AddSwagger(*openapi3.Swagger)` are all replaced with a single `<router package>.NewRouter(*openapi3.Swagger)`
	* NOTE: the `NewRouter(doc)` call now requires that the user ensures `doc` is valid (`doc.Validate() != nil`). This used to be asserted.

### v0.47.0
Field `(*openapi3.SwaggerLoader).LoadSwaggerFromURIFunc` of type `func(*openapi3.SwaggerLoader, *url.URL) (*openapi3.Swagger, error)` was removed after the addition of the field `(*openapi3.SwaggerLoader).ReadFromURIFunc` of type `func(*openapi3.SwaggerLoader, *url.URL) ([]byte, error)`.

```

### go.mod
```
module github.com/getkin/kin-openapi

go 1.25

require (
	github.com/go-openapi/jsonpointer v0.22.5
	github.com/gorilla/mux v1.8.0
	github.com/oasdiff/yaml v0.1.1
	github.com/oasdiff/yaml3 v0.0.14
	github.com/santhosh-tekuri/jsonschema/v6 v6.0.2
	github.com/stretchr/testify v1.9.0
)

require (
	github.com/davecgh/go-spew v1.1.1 // indirect
	github.com/go-openapi/swag/jsonname v0.25.5 // indirect
	github.com/kr/text v0.2.0 // indirect
	github.com/pmezard/go-difflib v1.0.0 // indirect
	golang.org/x/text v0.14.0 // indirect
	gopkg.in/check.v1 v1.0.0-20201130134442-10cb98267c6c // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)

```

### go.sum
```
github.com/creack/pty v1.1.9/go.mod h1:oKZEueFk5CKHvIhNR5MUki03XCEU+Q6VDXinZuGJ33E=
github.com/davecgh/go-spew v1.1.1 h1:vj9j/u1bqnvCEfJOwUhtlOARqs3+rkHYY13jYWTU97c=
github.com/davecgh/go-spew v1.1.1/go.mod h1:J7Y8YcW2NihsgmVo/mv3lAwl/skON4iLHjSsI+c5H38=
github.com/dlclark/regexp2 v1.11.0 h1:G/nrcoOa7ZXlpoa/91N3X7mM3r8eIlMBBJZvsz/mxKI=
github.com/dlclark/regexp2 v1.11.0/go.mod h1:DHkYz0B9wPfa6wondMfaivmHpzrQ3v9q8cnmRbL6yW8=
github.com/go-openapi/jsonpointer v0.22.5 h1:8on/0Yp4uTb9f4XvTrM2+1CPrV05QPZXu+rvu2o9jcA=
github.com/go-openapi/jsonpointer v0.22.5/go.mod h1:gyUR3sCvGSWchA2sUBJGluYMbe1zazrYWIkWPjjMUY0=
github.com/go-openapi/swag/jsonname v0.25.5 h1:8p150i44rv/Drip4vWI3kGi9+4W9TdI3US3uUYSFhSo=
github.com/go-openapi/swag/jsonname v0.25.5/go.mod h1:jNqqikyiAK56uS7n8sLkdaNY/uq6+D2m2LANat09pKU=
github.com/go-openapi/testify/v2 v2.4.0 h1:8nsPrHVCWkQ4p8h1EsRVymA2XABB4OT40gcvAu+voFM=
github.com/go-openapi/testify/v2 v2.4.0/go.mod h1:HCPmvFFnheKK2BuwSA0TbbdxJ3I16pjwMkYkP4Ywn54=
github.com/gorilla/mux v1.8.0 h1:i40aqfkR1h2SlN9hojwV5ZA91wcXFOvkdNIeFDP5koI=
github.com/gorilla/mux v1.8.0/go.mod h1:DVbg23sWSpFRCP0SfiEN6jmj59UnW/n46BH5rLB71So=
github.com/kr/pretty v0.2.1 h1:Fmg33tUaq4/8ym9TJN1x7sLJnHVwhP33CNkpYV/7rwI=
github.com/kr/pretty v0.2.1/go.mod h1:ipq/a2n7PKx3OHsz4KJII5eveXtPO4qwEXGdVfWzfnI=
github.com/kr/pty v1.1.1/go.mod h1:pFQYn66WHrOpPYNljwOMqo10TkYh1fy3cYio2l3bCsQ=
github.com/kr/text v0.1.0/go.mod h1:4Jbv+DJW3UT/LiOwJeYQe1efqtUx/iVham/4vfdArNI=
github.com/kr/text v0.2.0 h1:5Nx0Ya0ZqY2ygV366QzturHI13Jq95ApcVaJBhpS+AY=
github.com/kr/text v0.2.0/go.mod h1:eLer722TekiGuMkidMxC/pM04lWEeraHUUmBw8l2grE=
github.com/oasdiff/yaml v0.1.1 h1:6nHx+pn9gBRM6YpBlFZFQGCCd1nuvqOBtTD3KKTgGxY=
github.com/oasdiff/yaml v0.1.1/go.mod h1:EYJNoyktvWMJ0Hmhx+6qTaqMOsalUaRGT8Sj1hNcegU=
github.com/oasdiff/yaml3 v0.0.14 h1:aLJee3hxBK2H5wdXd9iPcIXb93Nty1Ge0pT171eHtkw=
github.com/oasdiff/yaml3 v0.0.14/go.mod h1:csto2xfDjYccdUn/yw/bPjj/cYTdp6HtFA0J4TWG+gg=
github.com/pmezard/go-difflib v1.0.0 h1:4DBwDE0NGyQoBHbLQYPwSUPoCMWR5BEzIk/f1lZbAQM=
github.com/pmezard/go-difflib v1.0.0/go.mod h1:iKH77koFhYxTK1pcRnkKkqfTogsbg7gZNVY4sRDYZ/4=
github.com/santhosh-tekuri/jsonschema/v6 v6.0.2 h1:KRzFb2m7YtdldCEkzs6KqmJw4nqEVZGK7IN2kJkjTuQ=
github.com/santhosh-tekuri/jsonschema/v6 v6.0.2/go.mod h1:JXeL+ps8p7/KNMjDQk3TCwPpBy0wYklyWTfbkIzdIFU=
github.com/stretchr/testify v1.9.0 h1:HtqpIVDClZ4nwg75+f6Lvsy/wHu+3BoSGCbBAcpTsTg=
github.com/stretchr/testify v1.9.0/go.mod h1:r2ic/lqez/lEtzL7wO/rwa5dbSLXVDPFyf8C91i36aY=
golang.org/x/text v0.14.0 h1:ScX5w1eTa3QqT8oi6+ziP7dTV1S2+ALU0bI+0zXKWiQ=
golang.org/x/text v0.14.0/go.mod h1:18ZOQIKpY8NJVqYksKHtTdi31H5itFRjB5/qKTNYzSU=
gopkg.in/check.v1 v0.0.0-20161208181325-20d25e280405/go.mod h1:Co6ibVJAznAaIkqp8huTwlJQCZ016jof/cbN4VW5Yz0=
gopkg.in/check.v1 v1.0.0-20201130134442-10cb98267c6c h1:Hei/4ADfdWqJk1ZMxUNpqntNwaWcugrBjAiHlqqRiVk=
gopkg.in/check.v1 v1.0.0-20201130134442-10cb98267c6c/go.mod h1:JHkPIbrfpd72SG/EVd6muEfDQjcINNoR0C8j2r3qZ4Q=
gopkg.in/yaml.v3 v3.0.1 h1:fxVm/GzAzEWqLHuvctI91KS9hhNmmWOoWu0XTYJS7CA=
gopkg.in/yaml.v3 v3.0.1/go.mod h1:K4uyk7z7BCEPqu6E+C64Yfv1cQ7kz7rIZviUmN+EgEM=

```

### openapi2/path_item.go
```
package openapi2

import (
	"encoding/json"
	"fmt"
	"maps"
	"net/http"

	"github.com/getkin/kin-openapi/openapi3"
)

type PathItem struct {
	Extensions map[string]any `json:"-" yaml:"-"`

	Ref string `json:"$ref,omitempty" yaml:"$ref,omitempty"`

	Delete     *Operation `json:"delete,omitempty" yaml:"delete,omitempty"`
	Get        *Operation `json:"get,omitempty" yaml:"get,omitempty"`
	Head       *Operation `json:"head,omitempty" yaml:"head,omitempty"`
	Options    *Operation `json:"options,omitempty" yaml:"options,omitempty"`
	Patch      *Operation `json:"patch,omitempty" yaml:"patch,omitempty"`
	Post       *Operation `json:"post,omitempty" yaml:"post,omitempty"`
	Put        *Operation `json:"put,omitempty" yaml:"put,omitempty"`
	Parameters Parameters `json:"parameters,omitempty" yaml:"parameters,omitempty"`
}

// MarshalJSON returns the JSON encoding of PathItem.
func (pathItem PathItem) MarshalJSON() ([]byte, error) {
	if ref := pathItem.Ref; ref != "" {
		return json.Marshal(openapi3.Ref{Ref: ref})
	}

	m := make(map[string]any, 8+len(pathItem.Extensions))
	maps.Copy(m, pathItem.Extensions)
	if x := pathItem.Delete; x != nil {
		m["delete"] = x
	}
	if x := pathItem.Get; x != nil {
		m["get"] = x
	}
	if x := pathItem.Head; x != nil {
		m["head"] = x
	}
	if x := pathItem.Options; x != nil {
		m["options"] = x
	}
	if x := pathItem.Patch; x != nil {
		m["patch"] = x
	}
	if x := pathItem.Post; x != nil {
		m["post"] = x
	}
	if x := pathItem.Put; x != nil {
		m["put"] = x
	}
	if x := pathItem.Parameters; len(x) != 0 {
		m["parameters"] = x
	}
	return json.Marshal(m)
}

// UnmarshalJSON sets PathItem to a copy of data.
func (pathItem *PathItem) UnmarshalJSON(data []byte) error {
	type PathItemBis PathItem
	var x PathItemBis
	if err := json.Unmarshal(data, &x); err != nil {
		return unmarshalError(err)
	}
	_ = json.Unmarshal(data, &x.Extensions)
	delete(x.Extensions, "$ref")
	delete(x.Extensions, "delete")
	delete(x.Extensions, "get")
	delete(x.Extensions, "head")
	delete(x.Extensions, "options")
	delete(x.Extensions, "patch")
	delete(x.Extensions, "post")
	delete(x.Extensions, "put")
	delete(x.Extensions, "parameters")
	if len(x.Extensions) == 0 {
		x.Extensions = nil
	}
	*pathItem = PathItem(x)
	return nil
}

func (pathItem *PathItem) Operations() map[string]*Operation {
	operations := make(map[string]*Operation)
	if v := pathItem.Delete; v != nil {
		operations[http.MethodDelete] = v
	}
	if v := pathItem.Get; v != nil {
		operations[http.MethodGet] = v
	}
	if v := pathItem.Head; v != nil {
		operations[http.MethodHead] = v
	}
	if v := pathItem.Options; v != nil {
		operations[http.MethodOptions] = v
	}
	if v := pathItem.Patch; v != nil {
		operations[http.MethodPatch] = v
	}
	if v := pathItem.Post; v != nil {
		operations[http.MethodPost] = v
	}
	if v := pathItem.Put; v != nil {
		operations[http.MethodPut] = v
	}
	return operations
}

func (pathItem *PathItem) GetOperation(method string) *Operation {
	switch method {
	case http.MethodDelete:
		return pathItem.Delete
	case http.MethodGet:
		return pathItem.Get
	case http.MethodHead:
		return pathItem.Head
	case http.MethodOptions:
		return pathItem.Options
	case http.MethodPatch:
		return pathItem.Patch
	case http.MethodPost:
		return pathItem.Post
	case http.MethodPut:
		return pathItem.Put
	default:
		panic(fmt.Errorf("unsupported HTTP method %q", method))
	}
}

func (pathItem *PathItem) SetOperation(method string, operation *Operation) {
	switch method {
	case http.MethodDelete:
		pathItem.Delete = operation
	case http.MethodGet:
		pathItem.Get = operation
	case http.MethodHead:
		pathItem.Head = operation
	case http.MethodOptions:
		pathItem.Options = operation
	case http.MethodPatch:
		pathItem.Patch = operation
	case http.MethodPost:
		pathItem.Post = operation
	case http.MethodPut:
		pathItem.Put = operation
	default:
		panic(fmt.Errorf("unsupported HTTP method %q", method))
	}
}

```

### openapi2conv/openapi2_conv.go
```
package openapi2conv

import (
	"cmp"
	"errors"
	"fmt"
	"maps"
	"net/url"
	"slices"
	"strings"

	"github.com/getkin/kin-openapi/openapi2"
	"github.com/getkin/kin-openapi/openapi3"
)

// ToV3 converts an OpenAPIv2 spec to an OpenAPIv3 spec
func ToV3(doc2 *openapi2.T) (*openapi3.T, error) {
	return ToV3WithLoader(doc2, openapi3.NewLoader(), nil)
}

func ToV3WithLoader(doc2 *openapi2.T, loader *openapi3.Loader, location *url.URL) (*openapi3.T, error) {
	doc3 := &openapi3.T{
		OpenAPI:      "3.0.3",
		Info:         &doc2.Info,
		Components:   &openapi3.Components{},
		Tags:         doc2.Tags,
		Extensions:   stripNonExtensions(doc2.Extensions),
		ExternalDocs: doc2.ExternalDocs,
	}

	if host := doc2.Host; host != "" {
		if strings.Contains(host, "/") {
			err := fmt.Errorf("invalid host %q. This MUST be the host only and does not include the scheme nor sub-paths", host)
			return nil, err
		}
		schemes := doc2.Schemes
		if len(schemes) == 0 {
			schemes = []string{"https"}
		}
		basePath := doc2.BasePath
		if basePath == "" {
			basePath = "/"
		}
		for _, scheme := range schemes {
			u := url.URL{
				Scheme: scheme,
				Host:   host,
				Path:   basePath,
			}
			doc3.AddServer(&openapi3.Server{URL: u.String()})
		}
	}

	doc3.Components.Schemas = make(map[string]*openapi3.SchemaRef)
	if parameters := doc2.Parameters; len(parameters) != 0 {
		doc3.Components.Parameters = make(map[string]*openapi3.ParameterRef)
		doc3.Components.RequestBodies = make(map[string]*openapi3.RequestBodyRef)
		for k, parameter := range parameters {
			v3Parameter, v3RequestBody, v3SchemaMap, err := ToV3Parameter(doc3.Components, parameter, doc2.Consumes)
			switch {
			case err != nil:
				return nil, err
			case v3RequestBody != nil:
				doc3.Components.RequestBodies[k] = v3RequestBody
			case v3SchemaMap != nil:
				for _, v3Schema := range v3SchemaMap {
					doc3.Components.Schemas[k] = v3Schema
				}
			default:
				doc3.Components.Parameters[k] = v3Parameter
			}
		}
	}

	if paths := doc2.Paths; len(paths) != 0 {
		doc3.Paths = openapi3.NewPathsWithCapacity(len(paths))
		for path, pathItem := range paths {
			r, err := ToV3PathItem(doc2, doc3.Components, pathItem, doc2.Consumes)
			if err != nil {
				return nil, err
			}
			doc3.Paths.Set(path, r)
		}
	}

	if responses := doc2.Responses; len(responses) != 0 {
		doc3.Components.Responses = make(openapi3.ResponseBodies, len(responses))
		for k, response := range responses {
			r, err := ToV3Response(response, doc2.Produces)
			if err != nil {
				return nil, err
			}
			doc3.Components.Responses[k] = r
		}
	}

	maps.Copy(doc3.Components.Schemas, ToV3Schemas(doc2.Definitions))

	if m := doc2.SecurityDefinitions; len(m) != 0 {
		doc3SecuritySchemes := make(map[string]*openapi3.SecuritySchemeRef)
		for k, v := range m {
			r, err := ToV3SecurityScheme(v)
			if err != nil {
				return nil, err
			}
			doc3SecuritySchemes[k] = r
		}
		doc3.Components.SecuritySchemes = doc3SecuritySchemes
	}

	doc3.Security = ToV3SecurityRequirements(doc2.Security)

	if err := loader.ResolveRefsIn(doc3, location); err != nil {
		return nil, err
	}

	return doc3, nil
}

func ToV3PathItem(doc2 *openapi2.T, components *openapi3.Components, pathItem *openapi2.PathItem, consumes []string) (*openapi3.PathItem, error) {
	doc3 := &openapi3.PathItem{
		Extensions: stripNonExtensions(pathItem.Extensions),
	}
	for method, operation := range pathItem.Operations() {
		doc3Operation, err := ToV3Operation(components, pathItem, operation, consumes)
		if err != nil {
			return nil, err
		}
		doc3.SetOperation(method, doc3Operation)
	}
	for _, parameter := range pathItem.Parameters {
		v3Parameter, v3RequestBody, v3Schema, err := ToV3Parameter(components, parameter, consumes)
		switch {
		case err != nil:
			return nil, err
		case v3RequestBody != nil:
			return nil, errors.New("pathItem must not have a body parameter")
		case v3Schema != nil:
			return nil, errors.New("pathItem must not have a schema parameter")
		default:
			doc3.Parameters = append(doc3.Parameters, v3Parameter)
		}
	}
	return doc3, nil
}

func ToV3Operation(components *openapi3.Components, pathItem *openapi2.PathItem, operation *openapi2.Operation, consumes []string) (*openapi3.Operation, error) {
	if operation == nil {
		return nil, nil
	}
	doc3 := &openapi3.Operation{
		OperationID:  operation.OperationID,
		Summary:      operation.Summary,
		Description:  operation.Description,
		Deprecated:   operation.Deprecated,
		Tags:         operation.Tags,
		Extensions:   stripNonExtensions(operation.Extensions),
		ExternalDocs: operation.ExternalDocs,
	}
	if v := operation.Security; v != nil {
		doc3Security := ToV3SecurityRequirements(*v)
		doc3.Security = &doc3Security
	}

	if len(operation.Consumes) > 0 {
		consumes = operation.Consumes
	}

	var reqBodies []*openapi3.RequestBodyRef
	formDataSchemas := make(map[string]*openapi3.SchemaRef)
	for _, parameter := range operation.Parameters {
		v3Parameter, v3RequestBody, v3SchemaMap, err := ToV3Parameter(components, parameter, consumes)
		switch {
		case err != nil:
			return nil, err
		case v3RequestBody != nil:
			reqBodies = append(reqBodies, v3RequestBody)
		case v3SchemaMap != nil:
			maps.Copy(formDataSchemas, v3SchemaMap)
		default:
			doc3.Parameters = append(doc3.Parameters, v3Parameter)
		}
	}
	var err error
	if doc3.RequestBody, err = onlyOneReqBodyParam(reqBodies, formDataSchemas, components, consumes); err != nil {
		return nil, err
	}

	if responses := operation.Responses; responses != nil {
		doc3.Responses = openapi3.NewResponsesWithCapacity(len(responses))
		for k, response := range responses {
			responseRef3, err := ToV3Response(response, operation.Produces)
			if err != nil {
				return nil, err
			}
			doc3.Responses.Set(k, responseRef3)
		}
	}
	return doc3, nil
}

func getParameterNameFromOldRef(ref string) string {
	cleanPath := strings.TrimPrefix(ref, "#/parameters/")
	pathSections := strings.SplitN(cleanPath, "/", 1)

	return pathSections[0]
}

func ToV3Parameter(components *openapi3.Components, parameter *openapi2.Parameter, consumes []string) (*openapi3.ParameterRef, *openapi3.RequestBodyRef, map[string]*openapi3.SchemaRef, error) {
	if ref := parameter.Ref; ref != "" {
		if strings.HasPrefix(ref, "#/parameters/") {
			name := getParameterNameFromOldRef(ref)
			if _, ok := components.RequestBodies[name]; ok {
				v3Ref := strings.Replace(ref, "#/parameters/", "#/components/requestBodies/", 1)
				return nil, &openapi3.RequestBodyRef{Ref: v3Ref}, nil, nil
			} else if schema, ok := components.Schemas[name]; ok {
				schemaRefMap := make(map[string]*openapi3.SchemaRef)
				if val, ok := schema.Value.Extensions["x-formData-name"]; ok {
					name = val.(string)
				}
				v3Ref := strings.Replace(ref, "#/parameters/", "#/components/schemas/", 1)
				schemaRefMap[name] = &openapi3.SchemaRef{Ref: v3Ref}
				return nil, nil, schemaRefMap, nil
			}
		}
		return &openapi3.ParameterRef{Ref: ToV3Ref(ref)}, nil, nil, nil
	}

	switch parameter.In {
	case "body":
		result := &openapi3.RequestBody{
			Description: parameter.Description,
			Required:    parameter.Required,
			Extensions:  stripNonExtensions(parameter.Extensions),
		}
		if parameter.Name != "" {
			if result.Extensions == nil {
				result.Extensions = make(map[string]any, 1)
			}
			result.Extensions["x-originalParamName"] = parameter.Name
		}

		if schemaRef := parameter.Schema; schemaRef != nil {
			result.WithSchemaRef(ToV3SchemaRef(schemaRef), consumes)
		}
		return nil, &openapi3.RequestBodyRef{Value: result}, nil, nil

	case "formData":
		format, typ := parameter.Format, parameter.Type
		if typ.Is("file") {
			format, typ = "binary", &openapi3.Types{"string"}
		}
		if parameter.Extensions == nil {
			parameter.Extensions = make(map[string]any, 1)
		}
		parameter.Extensions["x-formData-name"] = parameter.Name
		var required []string
		if parameter.Required {
			required = []string{parameter.Name}
		}
		schemaRef := &openapi3.SchemaRef{Value: &openapi3.Schema{
			Description:     parameter.Description,
			Type:            typ,
			Extensions:      stripNonExtensions(parameter.Extensions),
			Format:          format,
			Enum:            parameter.Enum,
			Min:             parameter.Minimum,
			Max:             parameter.Maximum,
			ExclusiveMin:    openapi3.ExclusiveBound{Bool: boolPtr(parameter.ExclusiveMin)},
			ExclusiveMax:    openapi3.ExclusiveBound{Bool: boolPtr(parameter.ExclusiveMax)},
			MinLength:       parameter.MinLength,
			MaxLength:       parameter.MaxLength,
			Default:         parameter.Default,
			MinItems:        parameter.MinItems,
			MaxItems:        parameter.MaxItems,
			Pattern:         parameter.Pattern,
			AllowEmptyValue: parameter.AllowEmptyValue,
			UniqueItems:     parameter.UniqueItems,
			MultipleOf:      parameter.MultipleOf,
			Required:        required,
		}}
		if parameter.Items != nil {
			schemaRef.Value.Items = ToV3SchemaRef(parameter.Items)
		}

		schemaRefMap := make(map[string]*openapi3.SchemaRef, 1)
		schemaRefMap[parameter.Name] = schemaRef
		return nil, nil, schemaRefMap, nil

	default:
		required := parameter.Required
		if parameter.In == openapi3.ParameterInPath {
			required = true
		}

		var schemaRefRef string
		if schemaRef := parameter.Schema; schemaRef != nil && schemaRef.Ref != "" {
			schemaRefRef = schemaRef.Ref
		}
		result := &openapi3.Parameter{
			In:          parameter.In,
			Name:        parameter.Name,
			Description: parameter.Description,
			Required:    required,
			Extensions:  stripNonExtensions(parameter.Extensions),
			Schema: ToV3SchemaRef(&openapi2.SchemaRef{Value: &openapi2.Schema{
				Type:            parameter.Type,
				Format:          parameter.Format,
				Enum:            parameter.Enum,
				Min:             parameter.Minimum,
				Max:             parameter.Maximum,
				ExclusiveMin:    parameter.ExclusiveMin,
				ExclusiveMax:    parameter.ExclusiveMax,
				MinLength:       parameter.MinLength,
				MaxLength:       parameter.MaxLength,
				Default:         parameter.Default,
				Items:           parameter.Items,
				MinItems:        parameter.MinItems,
				MaxItems:        parameter.MaxItems,
				Pattern:         parameter.Pattern,
				AllowEmptyValue: parameter.AllowEmptyValue,
				UniqueItems:     parameter.UniqueItems,
				MultipleOf:      parameter.MultipleOf,
			},
				Ref: schemaRefRef,
			}),
		}
		return &openapi3.ParameterRef{Value: result}, nil, nil, nil
	}
}

func formDataBody(bodies map[string]*openapi3.SchemaRef, reqs map[string]bool, consumes []string) *openapi3.RequestBodyRef {
	if len(bodies) != len(reqs) {
		panic(`request bodies and them being required must match`)
	}
	requireds := make([]string, 0, len(reqs))
	for propName, req := range reqs {
		if _, ok := bodies[propName]; !ok {
			panic(`request bodies and them being required must match`)
		}
		if req {
			requireds = append(requireds, propName)
		}
	}
	for s, ref := range bodies {
		if ref.Value != nil && len(ref.Value.Required) > 0 {
			ref.Value.Required = nil
			bodies[s] = ref
		}
	}
	slices.Sort(requireds)
	schema := &openapi3.Schema{
		Type:       &openapi3.Types{"object"},
		Properties: bodies,
		Required:   requireds,
	}
	return &openapi3.RequestBodyRef{
		Value: openapi3.NewRequestBody().WithSchema(schema, consumes),
	}
}

func getParameterNameFromNewRef(ref string) string {
	cleanPath := strings.TrimPrefix(ref, "#/components/schemas/")
	pathSections := strings.SplitN(cleanPath, "/", 1)

	return pathSections[0]
}

func onlyOneReqBodyParam(bodies []*openapi3.RequestBodyRef, formDataSchemas map[string]*openapi3.SchemaRef, components *openapi3.Components, consumes []string) (*openapi3.RequestBodyRef, error) {
	if len(bodies) > 1 {
		return nil, errors.New("multiple body parameters cannot exist for the same operation")
	}

	if len(bodies) != 0 && len(formDataSchemas) != 0 {
		return nil, errors.New("body and form parameters cannot exist together for the same operation")
	}

	for _, requestBodyRef := range bodies {
		return requestBodyRef, nil
	}

	if len(formDataSchemas) > 0 {
		formDataParams := make(map[string]*openapi3.SchemaRef, len(formDataSchemas))
		formDataReqs := make(map[string]bool, len(formDataSchemas))
		for formDataName, formDataSchema := range formDataSchemas {
			if formDataSchema.Ref != "" {
				name := getParameterNameFromNewRef(formDataSchema.Ref)
				if schema := components.Schemas[name]; schema != nil && schema.Value != nil {
					if tempName, ok := schema.Value.Extensions["x-formData-name"]; ok {
						name = tempName.(string)
					}
					formDataParams[name] = formDataSchema
					formDataReqs[name] = false
					for _, req := range schema.Value.Required {
						if name == req {
							formDataReqs[name] = true
						}
					}
				}
			} else if formDataSchema.Value != nil {
				formDataParams[formDataName] = formDataSchema
				formDataReqs[formDataName] = false
				for _, req := range formDataSchema.Value.Required {
					if formDataName == req {
						formDataReqs[formDataName] = true
					}
				}
			}
		}

		return formDataBody(formDataParams, formDataReqs, consumes), nil
	}

	return nil, nil
}

func ToV3Response(response *openapi2.Response, produces []string) (*openapi3.ResponseRef, error) {
	if ref := response.Ref; ref != "" {
		return &openapi3.ResponseRef{Ref: ToV3Ref(ref)}, nil
	}
	result := &openapi3.Response{
		Description: &response.Description,
		Extensions:  stripNonExtensions(response.Extensions),
	}

	// Default to "application/json" if "produces" is not specified.
	if len(produces) == 0 {
		produces = []string{"application/json"}
	}

	if schemaRef := response.Schema; schemaRef != nil {
		schema := ToV3SchemaRef(schemaRef)
		result.Content = make(openapi3.Content, len(produces))
		for _, mime := range produces {
			result.Content[mime] = openapi3.NewMediaType().WithSchemaRef(schema)
		}
	}
	if headers := response.Headers; len(headers) > 0 {
		result.Headers = ToV3Headers(headers)
	}
	return &openapi3.ResponseRef{Value: result}, nil
}

func ToV3Headers(defs map[string]*openapi2.Header) openapi3.Headers {
	headers := make(openapi3.Headers, len(defs))
	for name, header := range defs {
		header.In = ""
		header.Name = ""
		if ref := header.Ref; ref != "" {
			headers[name] = &openapi3.HeaderRef{Ref: ToV3Ref(ref)}
		} else {
			parameter, _, _, _ := ToV3Parameter(nil, &header.Parameter, nil)
			headers[name] = &openapi3.HeaderRef{Value: &openapi3.Header{
				Parameter: *parameter.Value,
			}}
		}
	}
	return headers
}

func ToV3Schemas(defs map[string]*openapi2.SchemaRef) map[string]*openapi3.SchemaRef {
	schemas := make(map[string]*openapi3.SchemaRef, len(defs))
	for name, schema := range defs {
		schemas[name] = ToV3SchemaRef(schema)
	}
	return schemas
}

func ToV3SchemaRef(schema *openapi2.SchemaRef) *openapi3.SchemaRef {
	if schema == nil {
		return &openapi3.SchemaRef{}
	}

	if ref := schema.Ref; ref != "" {
		return &openapi3.SchemaRef{Ref: ToV3Ref(ref)}
	}

	if schema.Value == nil {
		return &openapi3.SchemaRef{
			Extensions: schema.Extensions,
		}
	}

	v3Schema := &openapi3.Schema{
		Extensions:           schema.Value.Extensions,
		Type:                 schema.Value.Type,
		Title:                schema.Value.Title,
		Format:               schema.Value.Format,
		Description:          schema.Value.Description,
		Enum:                 schema.Value.Enum,
		Default:              schema.Value.Default,
		Example:              schema.Value.Example,
		ExternalDocs:         schema.Value.ExternalDocs,
		UniqueItems:          schema.Value.UniqueItems,
		ExclusiveMin:         openapi3.ExclusiveBound{Bool: boolPtr(schema.Value.ExclusiveMin)},
		ExclusiveMax:         openapi3.ExclusiveBound{Bool: boolPtr(schema.Value.ExclusiveMax)},
		ReadOnly:             schema.Value.ReadOnly,
		WriteOnly:            schema.Value.WriteOnly,
		AllowEmptyValue:      schema.Value.AllowEmptyValue,
		Deprecated:           schema.Value.Deprecated,
		XML:                  schema.Value.XML,
		Min:                  schema.Value.Min,
		Max:                  schema.Value.Max,
		MultipleOf:           schema.Value.MultipleOf,
		MinLength:            schema.Value.MinLength,
		MaxLength:            schema.Value.MaxLength,
		Pattern:              schema.Value.Pattern,
		MinItems:             schema.Value.MinItems,
		MaxItems:             schema.Value.MaxItems,
		Required:             schema.Value.Required,
		MinProps:             schema.Value.MinProps,
		MaxProps:             schema.Value.MaxProps,
		AllOf:                make(openapi3.SchemaRefs, len(schema.Value.AllOf)),
		Properties:           make(openapi3.Schemas),
		AdditionalProperties: toV3AdditionalProperties(schema.Value.AdditionalProperties),
	}

	if schema.Value.Discriminator != "" {
		v3Schema.Discriminator = &openapi3.Discriminator{
			PropertyName: schema.Value.Discriminator,
		}
	}

	if schema.Value.Items != nil {
		v3Schema.Items = ToV3SchemaRef(schema.Value.Items)
	}
	if schema.Value.Type.Is("file") {
		v3Schema.Format, v3Schema.Type = "binary", &openapi3.Types{"string"}
	}
	for k, v := range schema.Value.Properties {
		v3Schema.Properties[k] = ToV3SchemaRef(v)
	}
	for i, v := range schema.Value.AllOf {
		v3Schema.AllOf[i] = ToV3SchemaRef(v)
	}
	if val, ok := v3Schema.Extensions["x-nullable"]; ok {
		if nullable, valid := val.(bool); valid {
			v3Schema.Nullable = nullable
			delete(v3Schema.Extensions, "x-nullable")
		}
	}

	return &openapi3.SchemaRef{
		Extensions: schema.Extensions,
		Value:      v3Schema,
	}
}

func toV3AdditionalProperties(from openapi3.AdditionalProperties) openapi3.AdditionalProperties {
	return openapi3.AdditionalProperties{
		Has:    from.Has,
		Schema: convertRefsInV3SchemaRef(from.Schema),
	}
}

func convertRefsInV3SchemaRef(from *openapi3.SchemaRef) *openapi3.SchemaRef {
	if from == nil {
		return nil
	}
	to := *from
	to.Ref = ToV3Ref(to.Ref)
	if to.Value != nil {
		v := *from.Value
		to.Value = &v
		if to.Value.Items != nil {
			to.Value.Items.Ref = ToV3Ref(to.Value.Items.Ref)
		}
		to.Value.AdditionalProperties = toV3AdditionalProperties(to.Value.AdditionalProperties)

		if len(to.Value.AllOf) > 0 {
			allOf := make(openapi3.SchemaRefs, len(to.Value.AllOf))
			for i, schemaRef := range to.Value.AllOf {
				allOf[i] = convertRefsInV3SchemaRef(schemaRef)
			}
			to.Value.AllOf = allOf
		}
	}
	return &to
}

var ref2To3 = map[string]string{
	"#/definitions/": "#/components/schemas/",
	"#/responses/":   "#/components/responses/",
	"#/parameters/":  "#/components/parameters/",
}

func ToV3Ref(ref string) string {
	for old, new := range ref2To3 {
		if strings.HasPrefix(ref, old) {
			ref = strings.Replace(ref, old, new, 1)
		}
	}
	return ref
}

func FromV3Ref(ref string) string {
	for new, old := range ref2To3 {
		if strings.HasPrefix(ref, old) {
			ref = strings.Replace(ref, old, new, 1)
		} else if strings.HasPrefix(ref, "#/components/requestBodies/") {
			ref = strings.Replace(ref, "#/components/requestBodies/", "#/parameters/", 1)
		}
	}
	return ref
}

func ToV3SecurityRequirements(requirements openapi2.SecurityRequirements) openapi3.SecurityRequirements {
	if requirements == nil {
		return nil
	}
	result := make(openapi3.SecurityRequirements, len(requirements))
	for i, item := range requirements {
		result[i] = item
	}
	return result
}

func ToV3SecurityScheme(securityScheme *openapi2.SecurityScheme) (*openapi3.SecuritySchemeRef, error) {
	if securityScheme == nil {
		return nil, nil
	}
	result := &openapi3.SecurityScheme{
		Description: securityScheme.Description,
		Extensions:  stripNonExtensions(securityScheme.Extensions),
	}
	switch securityScheme.Type {
	case "basic":
		result.Type = "http"
		result.Scheme = "basic"
	case "apiKey":
		result.Type = "apiKey"
		result.In = securityScheme.In
		result.Name = securityScheme.Name
	case "oauth2":
		result.Type = "oauth2"
		flows := &openapi3.OAuthFlows{}
		result.Flows = flows
		scopesMap := make(map[string]string)
		maps.Copy(scopesMap, securityScheme.Scopes)
		flow := &openapi3.OAuthFlow{
			AuthorizationURL: securityScheme.AuthorizationURL,
			TokenURL:         securityScheme.TokenURL,
			Scopes:           scopesMap,
		}
		switch securityScheme.Flow {
		case "implicit":
			flows.Implicit = flow
		case "accessCode":
			flows.AuthorizationCode = flow
		case "password":
			flows.Password = flow
		case "application":
			flows.ClientCredentials = flow
		default:
			return nil, fmt.Errorf("unsupported flow %q", securityScheme.Flow)
		}
	}
	return &openapi3.SecuritySchemeRef{
		Ref:   ToV3Ref(securityScheme.Ref),
		Value: result,
	}, nil
}

// FromV3 converts an OpenAPIv3 spec to an OpenAPIv2 spec
func FromV3(doc3 *openapi3.T) (*openapi2.T, error) {
	doc2Responses, err := FromV3Responses(doc3.Components.Responses, doc3.Components)
	if err != nil {
		return nil, err
	}
	schemas, parameters := FromV3Schemas(doc3.Components.Schemas, doc3.Components)
	doc2 := &openapi2.T{
		Swagger:      "2.0",
		Info:         *doc3.Info,
		Definitions:  schemas,
		Parameters:   parameters,
		Responses:    doc2Responses,
		Tags:         doc3.Tags,
		Extensions:   stripNonExtensions(doc3.Extensions),
		ExternalDocs: doc3.ExternalDocs,
	}

	isHTTPS := false
	isHTTP := false
	servers := doc3.Servers
	for i, server := range servers {
		if parsedURL, err := url.Parse(server.URL); err == nil {
			switch parsedURL.Scheme {
			case "https":
				isHTTPS = true
			case "http":
				isHTTP = true
			}
			// The first server is assumed to provide the base path
			if i == 0 {
				doc2.Host = parsedURL.Host
				doc2.BasePath = parsedURL.Path
			}
		}
	}

	if isHTTPS {
		doc2.Schemes = append(doc2.Schemes, "https")
	}
	if isHTTP {
		doc2.Schemes = append(doc2.Schemes, "http")
	}

	for path, pathItem := range doc3.Paths.Map() {
		if pathItem == nil {
			continue
		}
		doc2.AddOperation(path, "GET", nil)
		addPathExtensions(doc2, path, stripNonExtensions(pathItem.Extensions))
		for method, operation := range pathItem.Operations() {
			if operation == nil {
				continue
			}
			doc2Operation, err := FromV3Operation(doc3, operation)
			if err != nil {
				return nil, err
			}
			doc2.AddOperation(path, method, doc2Operation)
		}
		params := openapi2.Parameters{}
		for _, param := range pathItem.Parameters {
			p, err := FromV3Parameter(param, doc3.Components)
			if err != nil {
				return nil, err
			}
			params = append(params, p)
		}
		slices.SortFunc(params, compareParameters)
		doc2.Paths[path].Parameters = params
	}

	for name, param := range doc3.Components.Parameters {
		if doc2.Parameters[name], err = FromV3Parameter(param, doc3.Components); err != nil {
			return nil, err
		}
	}

	for name, requestBodyRef := range doc3.Components.RequestBodies {
		bodyOrRefParameters, formDataParameters, consumes, err := fromV3RequestBodies(name, requestBodyRef, doc3.Components)
		if err != nil {
			return nil, err
		}
		if len(formDataParameters) != 0 {
			for _, param := range formDataParameters {
				doc2.Parameters[param.Name] = param
			}
		} else if len(bodyOrRefParameters) != 0 {
			for _, param := range bodyOrRefParameters {
				doc2.Parameters[name] = param
			}
		}

		if len(consumes) != 0 {
			doc2.Consumes = consumesToArray(consumes)
		}
	}

	if m := doc3.Components.SecuritySchemes; m != nil {
		doc2SecuritySchemes := make(map[string]*openapi2.SecurityScheme)
		for id, securityScheme := range m {
			v, err := FromV3SecurityScheme(securityScheme)
			if err != nil {
				return nil, err
			}
			doc2SecuritySchemes[id] = v
		}
		doc2.SecurityDefinitions = doc2SecuritySchemes
	}
	doc2.Security = FromV3SecurityRequirements(doc3.Security)

	return doc2, nil
}

func consumesToArray(consumes map[string]struct{}) []string {
	consumesArr := make([]string, 0, len(consumes))
	for key := range consumes {
		consumesArr = append(consumesArr, key)
	}
	slices.Sort(consumesArr)
	return consumesArr
}

func fromV3RequestBodies(name string, requestBodyRef *openapi3.RequestBodyRef, components *openapi3.Components) (
	bodyOrRefParameters openapi2.Parameters,
	formParameters openapi2.Parameters,
	consumes map[string]struct{},
	err error,
) {
	if ref := requestBodyRef.Ref; ref != "" {
		bodyOrRefParameters = append(bodyOrRefParameters, &openapi2.Parameter{Ref: FromV3Ref(ref)})
		return
	}

	// Only select one formData or request body for an individual requestBody as OpenAPI 2 does not support multiples
	if requestBodyRef.Value != nil {
		for contentType, mediaType := range requestBodyRef.Value.Content {
			if consumes == nil {
				consumes = make(map[string]struct{})
			}
			consumes[contentType] = struct{}{}
			if contentType == "application/x-www-form-urlencoded" || contentType == "multipart/form-data" {
				formParameters = FromV3RequestBodyFormData(mediaType)
				continue
			}

			paramName := name
			if originalName, ok := requestBodyRef.Value.Extensions["x-originalParamName"]; ok {
				paramName = originalName.(string)
			}

			var r *openapi2.Parameter
			if r, err = FromV3RequestBody(paramName, requestBodyRef, mediaType, components); err != nil {
				return
			}

			bodyOrRefParameters = append(bodyOrRefParameters, r)
		}
	}
	return
}

func FromV3Schemas(schemas map[string]*openapi3.SchemaRef, components *openapi3.Components) (map[string]*openapi2.SchemaRef, map[string]*openapi2.Parameter) {
	v2Defs := make(map[string]*openapi2.SchemaRef)
	v2Params := make(map[string]*openapi2.Parameter)
	for name, schema := range schemas {
		schemaConv, parameterConv := FromV3SchemaRef(schema, components)
		if schemaConv != nil {
			v2Defs[name] = schemaConv
		} else if parameterConv != nil {
			if parameterConv.Name == "" {
				parameterConv.Name = name
			}
			v2Params[name] = parameterConv
		}
	}
	return v2Defs, v2Params
}

func FromV3SchemaRef(schema *openapi3.SchemaRef, components *openapi3.Components) (*openapi2.SchemaRef, *openapi2.Parameter) {
	if ref := schema.Ref; ref != "" {
		// FromV3RequestBodyFormData (and other recursive call sites in
		// this file) pass components=nil when recursing into array
		// items and nested refs. Without guarding, components.Schemas
		// nil-derefs before we even have a chance to look up the
		// component, so a ref like '#/components/schemas/CreateEmbeddingRequest'
		// inside an array schema crashes the converter (#1062).
		// Treat a missing components table the same as 'the target
		// schema is not known locally': emit a plain $ref and move on.
		name := getParameterNameFromNewRef(ref)
		if components != nil {
			if val, ok := components.Schemas[name]; ok {
				if val.Value.Format == "binary" {
					v2Ref := strings.Replace(ref, "#/components/schemas/", "#/parameters/", 1)
					return nil, &openapi2.Parameter{Ref: v2Ref}
				}
			}
		}

		return &openapi2.SchemaRef{Ref: FromV3Ref(ref)}, nil
	}
	if schema.Value == nil {
		return &openapi2.SchemaRef{
			Extensions: schema.Extensions,
		}, nil
	}

	if schema.Value != nil {
		if schema.Value.Type.Is("string") && schema.Value.Format == "binary" {
			paramType := &openapi3.Types{"file"}

			value := schema.Value.Extensions["x-formData-name"]
			originalName, _ := value.(string)
			required := slices.Contains(schema.Value.Required, originalName)
			return nil, &openapi2.Parameter{
				In:           "formData",
				Name:         originalName,
				Description:  schema.Value.Description,
				Type:         paramType,
				Enum:         schema.Value.Enum,
				Minimum:      effectiveMin(schema.Value.Min, schema.Value.ExclusiveMin),
				Maximum:      effectiveMax(schema.Value.Max, schema.Value.ExclusiveMax),
				ExclusiveMin: exclusiveBoundToBool(schema.Value.ExclusiveMin),
				ExclusiveMax: exclusiveBoundToBool(schema.Value.ExclusiveMax),
				MinLength:    schema.Value.MinLength,
				MaxLength:    schema.Value.MaxLength,
				Default:      schema.Value.Default,
				// Items:           schema.Value.Items,
				MinItems:        schema.Value.MinItems,
				MaxItems:        schema.Value.MaxItems,
				AllowEmptyValue: schema.Value.AllowEmptyValue,
				UniqueItems:     schema.Value.UniqueItems,
				MultipleOf:      schema.Value.MultipleOf,
				Extensions:      stripNonExtensions(schema.Value.Extensions),
				Required:        required,
			}
		}
	}

	v2Schema := &openapi2.Schema{
		Extensions:           schema.Value.Extensions,
		Type:                 schema.Value.Type,
		Title:                schema.Value.Title,
		Format:               schema.Value.Format,
		Description:          schema.Value.Description,
		Enum:                 schema.Value.Enum,
		Default:              schema.Value.Default,
		Example:              schema.Value.Example,
		ExternalDocs:         schema.Value.ExternalDocs,
		UniqueItems:          schema.Value.UniqueItems,
		ExclusiveMin:         exclusiveBoundToBool(schema.Value.ExclusiveMin),
		ExclusiveMax:         exclusiveBoundToBool(schema.Value.ExclusiveMax),
		ReadOnly:             schema.Value.ReadOnly,
		WriteOnly:            schema.Value.WriteOnly,
		AllowEmptyValue:      schema.Value.AllowEmptyValue,
		Deprecated:           schema.Value.Deprecated,
		XML:                  schema.Value.XML,
		Min:                  effectiveMin(schema.Value.Min, schema.Value.ExclusiveMin),
		Max:                  effectiveMax(schema.Value.Max, schema.Value.ExclusiveMax),
		MultipleOf:           schema.Value.MultipleOf,
		MinLength:            schema.Value.MinLength,
		MaxLength:            schema.Value.MaxLength,
		Pattern:              schema.Value.Pattern,
		MinItems:             schema.Value.MinItems,
		MaxItems:             schema.Value.MaxItems,
		Required:             schema.Value.Required,
		MinProps:             schema.Value.MinProps,
		MaxProps:             schema.Value.MaxProps,
		Properties:           make(openapi2.Schemas),
		AllOf:                make(openapi2.SchemaRefs, len(schema.Value.AllOf)),
		AdditionalProperties: schema.Value.AdditionalProperties,
	}

	if v := schema.Value.Items; v != nil {
		v2Schema.Items, _ = FromV3SchemaRef(v, components)
	}

	keys := make([]string, 0, len(schema.Value.Properties))
	for k := range schema.Value.Properties {
		keys = append(keys, k)
	}
	slices.Sort(keys)
	for _, key := range keys {
		property, _ := FromV3SchemaRef(schema.Value.Properties[key], components)
		if property != nil {
			v2Schema.Properties[key] = property
		}
	}

	for i, v := range schema.Value.AllOf {
		v2Schema.AllOf[i], _ = FromV3SchemaRef(v, components)
	}
	if schema.Value.PermitsNull() {
		schema.Value.Nullable = false
		if schema.Value.Extensions == nil {
			v2Schema.Extensions = make(map[string]any)
		}
		v2Schema.Extensions["x-nullable"] = true
	}

	return &openapi2.SchemaRef{
		Extensions: schema.Extensions,
		Value:      v2Schema,
	}, nil
}

func FromV3SecurityRequirements(requirements openapi3.SecurityRequirements) openapi2.SecurityRequirements {
	if requirements == nil {
		return nil
	}
	result := make([]map[string][]string, 0, len(requirements))
	for _, item := range requirements {
		result = append(result, item)
	}
	return result
}

func FromV3PathItem(doc3 *openapi3.T, pathItem *openapi3.PathItem) (*openapi2.PathItem, error) {
	result := &openapi2.PathItem{
		Extensions: stripNonExtensions(pathItem.Extensions),
	}
	for method, operation := range pathItem.Operations() {
		r, err := FromV3Operation(doc3, operation)
		if err != nil {
			return nil, err
		}
		result.SetOperation(method, r)
	}
	for _, parameter := range pathItem.Parameters {
		p, err := FromV3Parameter(parameter, doc3.Components)
		if err != nil {
			return nil, err
		}
		result.Parameters = append(result.Parameters, p)
	}
	return result, nil
}

func findNameForRequestBody(operation *openapi3.Operation) string {
nameSearch:
	for _, name := range attemptedBodyParameterNames {
		for _, parameterRef := range operation.Parameters {
			parameter := parameterRef.Value
			if parameter != nil && parameter.Name == name {
				continue nameSearch
			}
		}
		return name
	}
	return ""
}

func FromV3RequestBodyFormData(mediaType *openapi3.MediaType) openapi2.Parameters {
	parameters := openapi2.Parameters{}
	for propName, schemaRef := range mediaType.Schema.Value.Properties {
		if ref := schemaRef.Ref; ref != "" {
			v2Ref := strings.Replace(ref, "#/components/schemas/", "#/parameters/", 1)
			parameters = append(parameters, &openapi2.Parameter{Ref: v2Ref})
			continue
		}
		val := schemaRef.Value
		typ := val.Type
		if val.Format == "binary" {
			typ = &openapi3.Types{"file"}
		}
		required := slices.Contains(val.Required, propName)

		var v2Items *openapi2.SchemaRef
		if val.Items != nil {
			v2Items, _ = FromV3SchemaRef(val.Items, nil)
		}
		parameter := &openapi2.Parameter{
			Name:         propName,
			Description:  val.Description,
			Type:         typ,
			In:           "formData",
			Extensions:   stripNonExtensions(val.Extensions),
			Enum:         val.Enum,
			ExclusiveMin: exclusiveBoundToBool(val.ExclusiveMin),
			ExclusiveMax: exclusiveBoundToBool(val.ExclusiveMax),
			MinLength:    val.MinLength,
			MaxLength:    val.MaxLength,
			Default:      val.Default,
			Items:        v2Items,
			MinItems:     val.MinItems,
			MaxItems:     val.MaxItems,
			Maximum:      effectiveMax(val.Max, val.ExclusiveMax),
			Minimum:      effectiveMin(val.Min, val.ExclusiveMin),
			Pattern:      val.Pattern,
			// CollectionFormat: val.CollectionFormat,
			// Format:          val.Format,
			AllowEmptyValue: val.AllowEmptyValue,
			Required:        required,
			UniqueItems:     val.UniqueItems,
			MultipleOf:      val.MultipleOf,
		}
		parameters = append(parameters, parameter)
	}
	return parameters
}

func FromV3Operation(doc3 *openapi3.T, operation *openapi3.Operation) (*openapi2.Operation, error) {
	if operation == nil {
		return nil, nil
	}
	result := &openapi2.Operation{
		OperationID:  operation.OperationID,
		Summary:      operation.Summary,
		Description:  operation.Description,
		Deprecated:   operation.Deprecated,
		Tags:         operation.Tags,
		Extensions:   stripNonExtensions(operation.Extensions),
		ExternalDocs: operation.ExternalDocs,
	}
	if v := operation.Security; v != nil {
		resultSecurity := FromV3SecurityRequirements(*v)
		result.Security = &resultSecurity
	}
	for _, parameter := range operation.Parameters {
		r, err := FromV3Parameter(parameter, doc3.Components)
		if err != nil {
			return nil, err
		}
		result.Parameters = append(result.Parameters, r)
	}
	if v := operation.RequestBody; v != nil {
		// Find parameter name that we can use for the body
		name := findNameForRequestBody(operation)
		if name == "" {
			return nil, errors.New("could not find a name for request body")
		}

		bodyOrRefParameters, formDataParameters, consumes, err := fromV3RequestBodies(name, v, doc3.Components)
		if err != nil {
			return nil, err
		}
		if len(formDataParameters) != 0 {
			result.Parameters = append(result.Parameters, formDataParameters...)
		} else if len(bodyOrRefParameters) != 0 {
			for _, param := range bodyOrRefParameters {
				result.Parameters = append(result.Parameters, param)
				break // add a single request body
			}

		}

		if len(consumes) != 0 {
			result.Consumes = consumesToArray(consumes)
		}
	}
	slices.SortFunc(result.Parameters, compareParameters)

	if responses := operation.Responses; responses != nil {
		resultResponses, err := FromV3Responses(responses.Map(), doc3.Components)
		if err != nil {
			return nil, err
		}
		result.Responses = resultResponses
	}
	return result, nil
}

func FromV3RequestBody(name string, requestBodyRef *openapi3.RequestBodyRef, mediaType *openapi3.MediaType, components *openapi3.Components) (*openapi2.Parameter, error) {
	requestBody := requestBodyRef.Value

	result := &openapi2.Parameter{
		In:          "body",
		Name:        name,
		Description: requestBody.Description,
		Required:    requestBody.Required,
		Extensions:  stripNonExtensions(requestBody.Extensions),
	}

	if mediaType != nil {
		result.Schema, _ = FromV3SchemaRef(mediaType.Schema, components)
	}
	return result, nil
}

func FromV3Parameter(ref *openapi3.ParameterRef, components *openapi3.Components) (*openapi2.Parameter, error) {
	if ref := ref.Ref; ref != "" {
		return &openapi2.Parameter{Ref: FromV3Ref(ref)}, nil
	}
	parameter := ref.Value
	if parameter == nil {
		return nil, nil
	}
	result := &openapi2.Parameter{
		Description: parameter.Description,
		In:          parameter.In,
		Name:        parameter.Name,
		Required:    parameter.Required,
		Extensions:  stripNonExtensions(parameter.Extensions),
	}
	if schemaRef := parameter.Schema; schemaRef != nil {
		schemaRefV2, _ := FromV3SchemaRef(schemaRef, components)
		if ref := schemaRefV2.Ref; ref != "" {
			result.Schema = &openapi2.SchemaRef{Ref: FromV3Ref(ref)}
			return result, nil
		}
		schema := schemaRefV2.Value
		result.Type = schema.Type
		result.Format = schema.Format
		result.Enum = schema.Enum
		result.Minimum = schema.Min
		result.Maximum = schema.Max
		result.ExclusiveMin = schema.ExclusiveMin
		result.ExclusiveMax = schema.ExclusiveMax
		result.MinLength = schema.MinLength
		result.MaxLength = schema.MaxLength
		result.Pattern = schema.Pattern
		result.Default = schema.Default
		result.Items = schema.Items
		result.MinItems = schema.MinItems
		result.MaxItems = schema.MaxItems
		result.AllowEmptyValue = schema.AllowEmptyValue
		// result.CollectionFormat = schema.CollectionFormat
		result.UniqueItems = schema.UniqueItems
		result.MultipleOf = schema.MultipleOf
	}
	return result, nil
}

func FromV3Responses(responses map[string]*openapi3.ResponseRef, components *openapi3.Components) (map[string]*openapi2.Response, error) {
	v2Responses := make(map[string]*openapi2.Response, len(responses))
	for k, response := range responses {
		r, err := FromV3Response(response, components)
		if err != nil {
			return nil, err
		}
		v2Responses[k] = r
	}
	return v2Responses, nil
}

func FromV3Response(ref *openapi3.ResponseRef, components *openapi3.Components) (*openapi2.Response, error) {
	if ref := ref.Ref; ref != "" {
		return &openapi2.Response{Ref: FromV3Ref(ref)}, nil
	}

	response := ref.Value
	if response == nil {
		return nil, nil
	}
	description := ""
	if desc := response.Description; desc != nil {
		description = *desc
	}
	result := &openapi2.Response{
		Description: description,
		Extensions:  stripNonExtensions(response.Extensions),
	}
	if content := response.Content; content != nil {
		if ct := content["application/json"]; ct != nil {
			result.Schema, _ = FromV3SchemaRef(ct.Schema, components)
		}
	}
	if headers := response.Headers; len(headers) > 0 {
		var err error
		if result.Headers, err = FromV3Headers(headers, components); err != nil {
			return nil, err
		}
	}
	return result, nil
}

func FromV3Headers(defs openapi3.Headers, components *openapi3.Components) (map[string]*openapi2.Header, error) {
	headers := make(map[string]*openapi2.Header, len(defs))
	for name, header := range defs {
		ref := openapi3.ParameterRef{Ref: header.Ref, Value: &header.Value.Parameter}
		parameter, err := FromV3Parameter(&ref, components)
		if err != nil {
			return nil, err
		}
		parameter.In = ""
		parameter.Name = ""
		headers[name] = &openapi2.Header{Parameter: *parameter}
	}
	return headers, nil
}

func FromV3SecurityScheme(ref *openapi3.SecuritySchemeRef) (*openapi2.SecurityScheme, error) {
	securityScheme := ref.Value
	if securityScheme == nil {
		return nil, nil
	}
	result := &openapi2.SecurityScheme{
		Ref:         FromV3Ref(ref.Ref),
		Description: securityScheme.Description,
		Extensions:  stripNonExtensions(securityScheme.Extensions),
	}
	switch securityScheme.Type {
	case "http":
		switch securityScheme.Scheme {
		case "basic":
			result.Type = "basic"
		default:
			result.Type = "apiKey"
			result.In = "header"
			result.Name = "Authorization"
		}
	case "apiKey":
		result.Type = "apiKey"
		result.In = securityScheme.In
		result.Name = securityScheme.Name
	case "oauth2":
		result.Type = "oauth2"
		flows := securityScheme.Flows
		if flows != nil {
			var flow *openapi3.OAuthFlow
			// TODO: Is this the right priority? What if multiple defined?
			switch {
			case flows.Implicit != nil:
				result.Flow = "implicit"
				flow = flows.Implicit
				result.AuthorizationURL = flow.AuthorizationURL


... [truncated, file is 42788 chars]
```

### openapi3/doc.go
```
// Package openapi3 parses and writes OpenAPI 3 specification documents.
//
// Supports OpenAPI 3.0, OpenAPI 3.1, and OpenAPI 3.2:
//   - OpenAPI 3.0.x: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md
//   - OpenAPI 3.1.x: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md
//   - OpenAPI 3.2.x: https://spec.openapis.org/oas/v3.2.0.html
//
// OpenAPI 3.1 Features:
//   - Type arrays with null support (e.g., ["string", "null"])
//   - JSON Schema 2020-12 keywords (const, examples, prefixItems, etc.)
//   - Webhooks for defining callback operations
//   - JSON Schema dialect specification
//   - SPDX license identifiers
//
// OpenAPI 3.2 Features:
//   - Media Type Object itemSchema for streaming sequential media types
//
// The implementation maintains 100% backward compatibility with OpenAPI 3.0.
//
// For OpenAPI 3.1 validation, use the JSON Schema 2020-12 validator option:
//
//	schema.VisitJSON(value, openapi3.EnableJSONSchema2020())
//
// Version detection is available via helper methods:
//
//	if doc.IsOpenAPI31OrLater() {
//	    // Handle OpenAPI 3.1 specific features
//	}
//	if doc.IsOpenAPI32OrLater() {
//	    // Handle OpenAPI 3.2 specific features
//	}
package openapi3

```

### openapi3/internalize_refs.go
```
package openapi3

import (
	"context"
	"path"
	"strings"
)

// RefNameResolver maps a component to a name that is used as it's internalized name.
//
// The function should avoid name collisions (i.e. be a injective mapping).
// It must only contain characters valid for fixed field names: [IdentifierRegExp].
type RefNameResolver func(*T, ComponentRef) string

// DefaultRefResolver is a default implementation of refNameResolver for the
// InternalizeRefs function.
//
// The external reference is internalized to (hopefully) a unique name. If
// the external reference matches (by path) to another reference in the root
// document then the name of that component is used.
//
// The transformation involves:
//   - Cutting the "#/components/<type>" part.
//   - Cutting the file extensions (.yaml/.json) from documents.
//   - Trimming the common directory with the root spec.
//   - Replace invalid characters with underscores.
//
// This is an injective mapping over a "reasonable" amount of the possible openapi
// spec domain space but is not perfect. There might be edge cases.
func DefaultRefNameResolver(doc *T, ref ComponentRef) string {
	if ref.RefString() == "" || ref.RefPath() == nil {
		panic("unable to resolve reference to name")
	}

	name := ref.RefPath()

	// If referring to a component in the root spec, no need to internalize just use
	// the existing component.
	// XXX(percivalalb): since this function call is iterating over components behind the
	// scenes during an internalization call it actually starts interating over
	// new & replaced internalized components. This might caused some edge cases,
	// haven't found one yet but this might need to actually be used on a frozen copy
	// of doc.
	if nameInRoot, found := ReferencesComponentInRootDocument(doc, ref); found {
		nameInRoot = strings.TrimPrefix(nameInRoot, "#")

		rootCompURI := copyURI(doc.url)
		rootCompURI.Fragment = nameInRoot
		name = rootCompURI
	}

	filePath, componentPath := name.Path, name.Fragment

	// Cut out the "#/components/<type>" to make the names shorter.
	// XXX(percivalalb): This might cause collisions but is worth the brevity.
	if b, a, ok := strings.Cut(componentPath, path.Join("components", ref.CollectionName(), "")); ok {
		componentPath = path.Join(b, a)
	}

	if filePath != "" {
		// If the path is the same as the root doc, just remove.
		if doc.url != nil && filePath == doc.url.Path {
			filePath = ""
		}

		// Remove the path extensions to make this JSON/YAML agnostic.
		for ext := path.Ext(filePath); len(ext) > 0; ext = path.Ext(filePath) {
			filePath = strings.TrimSuffix(filePath, ext)
		}

		// Trim the common prefix with the root doc path.
		if doc.url != nil {
			for commonDir := path.Dir(doc.url.Path); /*no common prefix*/ commonDir != "."; commonDir = path.Dir(commonDir) {
				if p, found := cutDirectories(filePath, commonDir); found {
					filePath = p
					break
				}
			}
		}
	}

	var internalizedName string

	// Trim .'s & slashes from start e.g. otherwise ./doc.yaml would end up as __doc
	if filePath != "" {
		internalizedName = strings.TrimLeft(filePath, "./")
	}

	if componentPath != "" {
		if internalizedName != "" {
			internalizedName += "_"
		}

		internalizedName += strings.TrimLeft(componentPath, "./")
	}

	// Replace invalid characters in component fixed field names.
	internalizedName = InvalidIdentifierCharRegExp.ReplaceAllString(internalizedName, "_")

	return internalizedName
}

// cutDirectories removes the given directories from the start of the path if
// the path is a child.
func cutDirectories(p, dirs string) (string, bool) {
	if dirs == "" || p == "" {
		return p, false
	}

	p = strings.TrimRight(p, "/")
	dirs = strings.TrimRight(dirs, "/")

	var sb strings.Builder
	sb.Grow(len(ParameterInHeader))
	for segments := range strings.SplitSeq(p, "/") {
		sb.WriteString(segments)

		if sb.String() == p {
			return strings.TrimPrefix(p, dirs), true
		}

		sb.WriteRune('/')
	}

	return p, false
}

func isExternalRef(ref string, parentIsExternal bool) bool {
	return ref != "" && (!strings.HasPrefix(ref, "#/components/") || parentIsExternal)
}

func (doc *T) addSchemaToSpec(s *SchemaRef, refNameResolver RefNameResolver, parentIsExternal bool) bool {
	if s == nil || !isExternalRef(s.Ref, parentIsExternal) {
		return false
	}

	name := refNameResolver(doc, s)
	if doc.Components != nil {
		if _, ok := doc.Components.Schemas[name]; ok {
			s.Ref = "#/components/schemas/" + name
			return true
		}
	}

	if doc.Components == nil {
		doc.Components = &Components{}
	}
	if doc.Components.Schemas == nil {
		doc.Components.Schemas = make(Schemas)
	}
	doc.Components.Schemas[name] = s.Value.NewRef()
	s.Ref = "#/components/schemas/" + name
	return true
}

func (doc *T) addParameterToSpec(p *ParameterRef, refNameResolver RefNameResolver, parentIsExternal bool) bool {
	if p == nil || !isExternalRef(p.Ref, parentIsExternal) {
		return false
	}
	name := refNameResolver(doc, p)
	if doc.Components != nil {
		if _, ok := doc.Components.Parameters[name]; ok {
			p.Ref = "#/components/parameters/" + name
			return true
		}
	}

	if doc.Components == nil {
		doc.Components = &Components{}
	}
	if doc.Components.Parameters == nil {
		doc.Components.Parameters = make(ParametersMap)
	}
	doc.Components.Parameters[name] = &ParameterRef{Value: p.Value}
	p.Ref = "#/components/parameters/" + name
	return true
}

func (doc *T) addHeaderToSpec(h *HeaderRef, refNameResolver RefNameResolver, parentIsExternal bool) bool {
	if h == nil || !isExternalRef(h.Ref, parentIsExternal) {
		return false
	}
	name := refNameResolver(doc, h)
	if doc.Components != nil {
		if _, ok := doc.Components.Headers[name]; ok {
			h.Ref = "#/components/headers/" + name
			return true
		}
	}

	if doc.Components == nil {
		doc.Components = &Components{}
	}
	if doc.Components.Headers == nil {
		doc.Components.Headers = make(Headers)
	}
	doc.Components.Headers[name] = &HeaderRef{Value: h.Value}
	h.Ref = "#/components/headers/" + name
	return true
}

func (doc *T) addRequestBodyToSpec(r *RequestBodyRef, refNameResolver RefNameResolver, parentIsExternal bool) bool {
	if r == nil || !isExternalRef(r.Ref, parentIsExternal) {
		return false
	}
	name := refNameResolver(doc, r)
	if doc.Components != nil {
		if _, ok := doc.Components.RequestBodies[name]; ok {
			r.Ref = "#/components/requestBodies/" + name
			return true
		}
	}

	if doc.Components == nil {
		doc.Components = &Components{}
	}
	if doc.Components.RequestBodies == nil {
		doc.Components.RequestBodies = make(RequestBodies)
	}
	doc.Components.RequestBodies[name] = &RequestBodyRef{Value: r.Value}
	r.Ref = "#/components/requestBodies/" + name
	return true
}

func (doc *T) addResponseToSpec(r *ResponseRef, refNameResolver RefNameResolver, parentIsExternal bool) bool {
	if r == nil || !isExternalRef(r.Ref, parentIsExternal) {
		return false
	}
	name := refNameResolver(doc, r)
	if doc.Components != nil {
		if _, ok := doc.Components.Responses[name]; ok {
			r.Ref = "#/components/responses/" + name
			return true
		}
	}

	if doc.Components == nil {
		doc.Components = &Components{}
	}
	if doc.Components.Responses == nil {
		doc.Components.Responses = make(ResponseBodies)
	}
	doc.Components.Responses[name] = &ResponseRef{Value: r.Value}
	r.Ref = "#/components/responses/" + name
	return true
}

func (doc *T) addSecuritySchemeToSpec(ss *SecuritySchemeRef, refNameResolver RefNameResolver, parentIsExternal bool) {
	if ss == nil || !isExternalRef(ss.Ref, parentIsExternal) {
		return
	}
	name := refNameResolver(doc, ss)
	if doc.Components != nil {
		if _, ok := doc.Components.SecuritySchemes[name]; ok {
			ss.Ref = "#/components/securitySchemes/" + name
			return
		}
	}

	if doc.Components == nil {
		doc.Components = &Components{}
	}
	if doc.Components.SecuritySchemes == nil {
		doc.Components.SecuritySchemes = make(SecuritySchemes)
	}
	doc.Components.SecuritySchemes[name] = &SecuritySchemeRef{Value: ss.Value}
	ss.Ref = "#/components/securitySchemes/" + name

}

func (doc *T) addExampleToSpec(e *ExampleRef, refNameResolver RefNameResolver, parentIsExternal bool) {
	if e == nil || !isExternalRef(e.Ref, parentIsExternal) {
		return
	}
	name := refNameResolver(doc, e)
	if doc.Components != nil {
		if _, ok := doc.Components.Examples[name]; ok {
			e.Ref = "#/components/examples/" + name
			return
		}
	}

	if doc.Components == nil {
		doc.Components = &Components{}
	}
	if doc.Components.Examples == nil {
		doc.Components.Examples = make(Examples)
	}
	doc.Components.Examples[name] = &ExampleRef{Value: e.Value}
	e.Ref = "#/components/examples/" + name

}

func (doc *T) addLinkToSpec(l *LinkRef, refNameResolver RefNameResolver, parentIsExternal bool) {
	if l == nil || !isExternalRef(l.Ref, parentIsExternal) {
		return
	}
	name := refNameResolver(doc, l)
	if doc.Components != nil {
		if _, ok := doc.Components.Links[name]; ok {
			l.Ref = "#/components/links/" + name
			return
		}
	}

	if doc.Components == nil {
		doc.Components = &Components{}
	}
	if doc.Components.Links == nil {
		doc.Components.Links = make(Links)
	}
	doc.Components.Links[name] = &LinkRef{Value: l.Value}
	l.Ref = "#/components/links/" + name

}

func (doc *T) addCallbackToSpec(c *CallbackRef, refNameResolver RefNameResolver, parentIsExternal bool) bool {
	if c == nil || !isExternalRef(c.Ref, parentIsExternal) {
		return false
	}
	name := refNameResolver(doc, c)

	if doc.Components == nil {
		doc.Components = &Components{}
	}
	if doc.Components.Callbacks == nil {
		doc.Components.Callbacks = make(Callbacks)
	}
	c.Ref = "#/components/callbacks/" + name
	doc.Components.Callbacks[name] = &CallbackRef{Value: c.Value}
	return true
}

func (doc *T) derefSchema(s *Schema, refNameResolver RefNameResolver, parentIsExternal bool) {
	if s == nil || doc.isVisitedSchema(s) {
		return
	}

	for _, list := range []SchemaRefs{s.AllOf, s.AnyOf, s.OneOf} {
		for _, s2 := range list {
			isExternal := doc.addSchemaToSpec(s2, refNameResolver, parentIsExternal)
			if s2 != nil {
				doc.derefSchema(s2.Value, refNameResolver, isExternal || parentIsExternal)
			}
		}
	}

	// Discriminator mapping values are special cases since they are not full
	// ref objects but are string references to schema objects.
	if s.Discriminator != nil {
		for _, k := range componentNames(s.Discriminator.Mapping) {
			mapRef := s.Discriminator.Mapping[k]
			s2 := (*SchemaRef)(&mapRef)
			isExternal := doc.addSchemaToSpec(s2, refNameResolver, parentIsExternal)
			doc.derefSchema(s2.Value, refNameResolver, isExternal || parentIsExternal)
			s.Discriminator.Mapping[k] = MappingRef(*s2)
		}
	}

	for _, name := range componentNames(s.Properties) {
		s2 := s.Properties[name]
		isExternal := doc.addSchemaToSpec(s2, refNameResolver, parentIsExternal)
		if s2 != nil {
			doc.derefSchema(s2.Value, refNameResolver, isExternal || parentIsExternal)
		}
	}
	for _, ref := range []*SchemaRef{s.Not, s.AdditionalProperties.Schema, s.Items} {
		isExternal := doc.addSchemaToSpec(ref, refNameResolver, parentIsExternal)
		if ref != nil {
			doc.derefSchema(ref.Value, refNameResolver, isExternal || parentIsExternal)
		}
	}
}

func (doc *T) derefHeaders(hs Headers, refNameResolver RefNameResolver, parentIsExternal bool) {
	for _, name := range componentNames(hs) {
		h := hs[name]
		isExternal := doc.addHeaderToSpec(h, refNameResolver, parentIsExternal)
		if doc.isVisitedHeader(h.Value) {
			continue
		}
		doc.derefParameter(h.Value.Parameter, refNameResolver, parentIsExternal || isExternal)
	}
}

func (doc *T) derefExamples(es Examples, refNameResolver RefNameResolver, parentIsExternal bool) {
	for _, name := range componentNames(es) {
		e := es[name]
		doc.addExampleToSpec(e, refNameResolver, parentIsExternal)
	}
}

func (doc *T) derefContent(c Content, refNameResolver RefNameResolver, parentIsExternal bool) {
	for _, name := range componentNames(c) {
		mediatype := c[name]
		isExternal := doc.addSchemaToSpec(mediatype.Schema, refNameResolver, parentIsExternal)
		if mediatype.Schema != nil {
			doc.derefSchema(mediatype.Schema.Value, refNameResolver, isExternal || parentIsExternal)
		}
		doc.derefExamples(mediatype.Examples, refNameResolver, parentIsExternal)
		for _, name := range componentNames(mediatype.Encoding) {
			e := mediatype.Encoding[name]
			doc.derefHeaders(e.Headers, refNameResolver, parentIsExternal)
		}
	}
}

func (doc *T) derefLinks(ls Links, refNameResolver RefNameResolver, parentIsExternal bool) {
	for _, name := range componentNames(ls) {
		l := ls[name]
		doc.addLinkToSpec(l, refNameResolver, parentIsExternal)
	}
}

func (doc *T) derefResponse(r *ResponseRef, refNameResolver RefNameResolver, parentIsExternal bool) {
	isExternal := doc.addResponseToSpec(r, refNameResolver, parentIsExternal)
	if v := r.Value; v != nil {
		doc.derefHeaders(v.Headers, refNameResolver, isExternal || parentIsExternal)
		doc.derefContent(v.Content, refNameResolver, isExternal || parentIsExternal)
		doc.derefLinks(v.Links, refNameResolver, isExternal || parentIsExternal)
	}
}

func (doc *T) derefResponses(rs *Responses, refNameResolver RefNameResolver, parentIsExternal bool) {
	doc.derefResponseBodies(rs.Map(), refNameResolver, parentIsExternal)
}

func (doc *T) derefResponseBodies(es ResponseBodies, refNameResolver RefNameResolver, parentIsExternal bool) {
	for _, name := range componentNames(es) {
		e := es[name]
		doc.derefResponse(e, refNameResolver, parentIsExternal)
	}
}

func (doc *T) derefParameter(p Parameter, refNameResolver RefNameResolver, parentIsExternal bool) {
	isExternal := doc.addSchemaToSpec(p.Schema, refNameResolver, parentIsExternal)
	doc.derefContent(p.Content, refNameResolver, parentIsExternal)
	if p.Schema != nil {
		doc.derefSchema(p.Schema.Value, refNameResolver, isExternal || parentIsExternal)
	}
}

func (doc *T) derefRequestBody(r RequestBody, refNameResolver RefNameResolver, parentIsExternal bool) {
	doc.derefContent(r.Content, refNameResolver, parentIsExternal)
}

func (doc *T) derefPaths(paths map[string]*PathItem, refNameResolver RefNameResolver, parentIsExternal bool) {
	for _, name := range componentNames(paths) {
		ops := paths[name]
		pathIsExternal := isExternalRef(ops.Ref, parentIsExternal)
		// inline full operations
		ops.Ref = ""

		for _, param := range ops.Parameters {
			isExternal := doc.addParameterToSpec(param, refNameResolver, pathIsExternal)
			if param.Value != nil {
				doc.derefParameter(*param.Value, refNameResolver, pathIsExternal || isExternal)
			}
		}

		opsWithMethod := ops.Operations()
		for _, name := range componentNames(opsWithMethod) {
			op := opsWithMethod[name]
			isExternal := doc.addRequestBodyToSpec(op.RequestBody, refNameResolver, pathIsExternal)
			if op.RequestBody != nil && op.RequestBody.Value != nil {
				doc.derefRequestBody(*op.RequestBody.Value, refNameResolver, pathIsExternal || isExternal)
			}
			for _, name := range componentNames(op.Callbacks) {
				cb := op.Callbacks[name]
				isExternal := doc.addCallbackToSpec(cb, refNameResolver, pathIsExternal)
				if cb.Value != nil {
					cbValue := (*cb.Value).Map()
					doc.derefPaths(cbValue, refNameResolver, pathIsExternal || isExternal)
				}
			}
			doc.derefResponses(op.Responses, refNameResolver, pathIsExternal)
			for _, param := range op.Parameters {
				isExternal := doc.addParameterToSpec(param, refNameResolver, pathIsExternal)
				if param.Value != nil {
					doc.derefParameter(*param.Value, refNameResolver, pathIsExternal || isExternal)
				}
			}
		}
	}
}

// InternalizeRefs removes all references to external files from the spec and moves them
// to the components section.
//
// refNameResolver takes in references to returns a name to store the reference under locally.
// It MUST return a unique name for each reference type.
// A default implementation is provided that will suffice for most use cases. See the function
// documentation for more details.
//
// Example:
//
//	doc.InternalizeRefs(context.Background(), nil)
func (doc *T) InternalizeRefs(ctx context.Context, refNameResolver func(*T, ComponentRef) string) {
	doc.resetVisited()

	if refNameResolver == nil {
		refNameResolver = DefaultRefNameResolver
	}

	if components := doc.Components; components != nil {
		for _, name := range componentNames(components.Schemas) {
			schema := components.Schemas[name]
			isExternal := doc.addSchemaToSpec(schema, refNameResolver, false)
			if schema != nil {
				schema.Ref = "" // always dereference the top level
				doc.derefSchema(schema.Value, refNameResolver, isExternal)
			}
		}
		for _, name := range componentNames(components.Parameters) {
			p := components.Parameters[name]
			isExternal := doc.addParameterToSpec(p, refNameResolver, false)
			if p != nil && p.Value != nil {
				p.Ref = "" // always dereference the top level
				doc.derefParameter(*p.Value, refNameResolver, isExternal)
			}
		}
		doc.derefHeaders(components.Headers, refNameResolver, false)
		for _, name := range componentNames(components.RequestBodies) {
			req := components.RequestBodies[name]
			isExternal := doc.addRequestBodyToSpec(req, refNameResolver, false)
			if req != nil && req.Value != nil {
				req.Ref = "" // always dereference the top level
				doc.derefRequestBody(*req.Value, refNameResolver, isExternal)
			}
		}
		doc.derefResponseBodies(components.Responses, refNameResolver, false)
		for _, name := range componentNames(components.SecuritySchemes) {
			ss := components.SecuritySchemes[name]
			doc.addSecuritySchemeToSpec(ss, refNameResolver, false)
		}
		doc.derefExamples(components.Examples, refNameResolver, false)
		doc.derefLinks(components.Links, refNameResolver, false)

		for _, name := range componentNames(components.Callbacks) {
			cb := components.Callbacks[name]
			isExternal := doc.addCallbackToSpec(cb, refNameResolver, false)
			if cb != nil && cb.Value != nil {
				cb.Ref = "" // always dereference the top level
				cbValue := (*cb.Value).Map()
				doc.derefPaths(cbValue, refNameResolver, isExternal)
			}
		}
	}

	doc.derefPaths(doc.Paths.Map(), refNameResolver, false)
}

```

### openapi3/loader.go
```
package openapi3

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/url"
	"os"
	"path"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
)

// IncludeOrigin specifies whether to include the origin of the OpenAPI elements.
// Deprecated: set Loader.IncludeOrigin instead. This global is read by NewLoader
// for backward compatibility but is not safe for concurrent use.
var IncludeOrigin = false

func failedToResolveRefFragmentPart(value, what string) error {
	return fmt.Errorf("failed to resolve %q in fragment in URI: %q", what, value)
}

// Loader helps deserialize an OpenAPIv3 document
type Loader struct {
	// IsExternalRefsAllowed enables visiting other files. Enforced only when
	// ReadFromURIFunc is nil; a custom ReadFromURIFunc bypasses this flag and
	// owns the access policy itself — see ReadFromURIFunc.
	IsExternalRefsAllowed bool

	// IncludeOrigin enables recording the file/line/column of each OpenAPI element.
	// Prefer this over the package-level IncludeOrigin global, which is not safe for
	// concurrent use.
	IncludeOrigin bool

	// ReadFromURIFunc overrides how the loader reads a referenced file or URL.
	//
	// SECURITY: when a custom ReadFromURIFunc is set, IsExternalRefsAllowed is
	// NOT enforced — this function alone decides which locations may be read. A
	// func that reads whatever URI it is handed (e.g. by delegating to
	// DefaultReadFromURI) resolves external $refs even when IsExternalRefsAllowed
	// is false, which on untrusted documents enables local file reads
	// (`$ref: "/etc/passwd"`) and SSRF (`$ref: "http://169.254.169.254/..."`).
	// A custom func must apply its own scheme/host allowlist, or re-check
	// IsExternalRefsAllowed, before reading.
	ReadFromURIFunc ReadFromURIFunc

	// JoinFunc allows overriding how relative $ref paths are resolved against
	// a base path. When set, it is called instead of the default join logic
	// that uses path.Dir and path.Join. This is useful when loading specs from
	// non-filesystem sources (e.g. git objects, remote archives) where the base
	// path follows a different convention than filesystem paths.
	JoinFunc func(basePath *url.URL, relativePath *url.URL) *url.URL

	Context context.Context

	rootDir      string
	rootLocation string

	visitedPathItemRefs map[string]struct{}

	visitedDocuments map[string]*T

	// originTrees retains each loaded document's origin tree, keyed by the
	// document itself so insert and lookup cannot disagree, populated when
	// IncludeOrigin is set. resolveComponent uses it to re-attach origins to
	// components that lose them in the generic-map path, without re-reading
	// or re-parsing the file.
	originTrees map[*T]*originTree

	visitedRefs map[string]struct{}
	visitedPath []string
	backtrack   map[string][]func(value any)
}

// NewLoader returns an empty Loader
func NewLoader() *Loader {
	return &Loader{
		Context:       context.Background(),
		IncludeOrigin: IncludeOrigin,
	}
}

func (loader *Loader) resetVisitedPathItemRefs() {
	loader.visitedPathItemRefs = make(map[string]struct{})
	loader.visitedRefs = make(map[string]struct{})
	loader.visitedPath = nil
	loader.backtrack = make(map[string][]func(value any))
}

// LoadFromURI loads a spec from a remote URL
func (loader *Loader) LoadFromURI(location *url.URL) (*T, error) {
	loader.resetVisitedPathItemRefs()
	return loader.loadFromURIInternal(location)
}

// LoadFromFile loads a spec from a local file path
func (loader *Loader) LoadFromFile(location string) (*T, error) {
	loader.rootDir = path.Dir(location)
	return loader.LoadFromURI(&url.URL{Path: filepath.ToSlash(location)})
}

func (loader *Loader) loadFromURIInternal(location *url.URL) (*T, error) {
	data, err := loader.readURL(location)
	if err != nil {
		return nil, err
	}
	return loader.loadFromDataWithPathInternal(data, location)
}

func (loader *Loader) allowsExternalRefs(ref string) (err error) {
	if !loader.IsExternalRefsAllowed {
		err = fmt.Errorf("encountered disallowed external reference: %q", ref)
	}
	return
}

func (loader *Loader) loadSingleElementFromURI(ref string, rootPath *url.URL, element any) (*url.URL, error) {
	// IsExternalRefsAllowed is enforced here only when no custom ReadFromURIFunc
	// is installed; otherwise the custom func owns the access policy (see the
	// SECURITY note on the ReadFromURIFunc field).
	if loader.ReadFromURIFunc == nil {
		if err := loader.allowsExternalRefs(ref); err != nil {
			return nil, err
		}
	}

	resolvedPath, err := loader.resolvePathWithRef(ref, rootPath)
	if err != nil {
		return nil, err
	}
	if frag := resolvedPath.Fragment; frag != "" {
		return nil, fmt.Errorf("unexpected ref fragment %q", frag)
	}

	data, err := loader.readURL(resolvedPath)
	if err != nil {
		return nil, err
	}
	if _, err := unmarshal(data, element, loader.IncludeOrigin, resolvedPath); err != nil {
		return nil, err
	}

	return resolvedPath, nil
}

// rememberOriginTree retains doc's origin tree for attachOriginToResolved.
// tree is nil when IncludeOrigin is off or the data took the json path.
func (loader *Loader) rememberOriginTree(doc *T, tree *originTree) {
	if tree == nil {
		return
	}
	if loader.originTrees == nil {
		loader.originTrees = make(map[*T]*originTree)
	}
	loader.originTrees[doc] = tree
}

func (loader *Loader) readURL(location *url.URL) ([]byte, error) {
	if f := loader.ReadFromURIFunc; f != nil {
		return f(loader, location)
	}
	return DefaultReadFromURI(loader, location)
}

// LoadFromStdin loads a spec from stdin
func (loader *Loader) LoadFromStdin() (*T, error) {
	return loader.LoadFromIoReader(os.Stdin)
}

// LoadFromStdin loads a spec from io.Reader
func (loader *Loader) LoadFromIoReader(reader io.Reader) (*T, error) {
	if reader == nil {
		return nil, fmt.Errorf("invalid reader: %v", reader)
	}

	data, err := io.ReadAll(reader)
	if err != nil {
		return nil, err
	}
	return loader.LoadFromData(data)
}

// LoadFromData loads a spec from a byte array
func (loader *Loader) LoadFromData(data []byte) (*T, error) {
	loader.resetVisitedPathItemRefs()
	doc := &T{}
	tree, err := unmarshal(data, doc, loader.IncludeOrigin, nil)
	if err != nil {
		return nil, err
	}
	loader.rememberOriginTree(doc, tree)
	if err := loader.ResolveRefsIn(doc, nil); err != nil {
		return nil, err
	}
	return doc, nil
}

// LoadFromDataWithPath takes the OpenAPI document data in bytes and a path where the resolver can find referred
// elements and returns a *T with all resolved data or an error if unable to load data or resolve refs.
func (loader *Loader) LoadFromDataWithPath(data []byte, location *url.URL) (*T, error) {
	loader.resetVisitedPathItemRefs()
	return loader.loadFromDataWithPathInternal(data, location)
}

func (loader *Loader) loadFromDataWithPathInternal(data []byte, location *url.URL) (*T, error) {
	if loader.visitedDocuments == nil {
		loader.visitedDocuments = make(map[string]*T)
		loader.rootLocation = location.Path
	}
	uri := location.String()
	if doc, ok := loader.visitedDocuments[uri]; ok {
		return doc, nil
	}

	doc := &T{}
	loader.visitedDocuments[uri] = doc

	tree, err := unmarshal(data, doc, loader.IncludeOrigin, location)
	if err != nil {
		return nil, err
	}
	loader.rememberOriginTree(doc, tree)

	doc.url = copyURI(location)

	if err := loader.ResolveRefsIn(doc, location); err != nil {
		return nil, err
	}

	return doc, nil
}

// ResolveRefsIn expands references if for instance spec was just unmarshaled
func (loader *Loader) ResolveRefsIn(doc *T, location *url.URL) (err error) {
	if loader.Context == nil {
		loader.Context = context.Background()
	}

	if loader.visitedPathItemRefs == nil {
		loader.resetVisitedPathItemRefs()
	}

	if components := doc.Components; components != nil {
		for _, name := range componentNames(components.Headers) {
			component := components.Headers[name]
			if err = loader.resolveHeaderRef(doc, component, location); err != nil {
				return
			}
		}
		for _, name := range componentNames(components.Parameters) {
			component := components.Parameters[name]
			if err = loader.resolveParameterRef(doc, component, location); err != nil {
				return
			}
		}
		for _, name := range componentNames(components.RequestBodies) {
			component := components.RequestBodies[name]
			if err = loader.resolveRequestBodyRef(doc, component, location); err != nil {
				return
			}
		}
		for _, name := range componentNames(components.Responses) {
			component := components.Responses[name]
			if err = loader.resolveResponseRef(doc, component, location); err != nil {
				return
			}
		}
		for _, name := range componentNames(components.Schemas) {
			component := components.Schemas[name]
			if err = loader.resolveSchemaRef(doc, component, location, []string{}); err != nil {
				return
			}
		}
		for _, name := range componentNames(components.SecuritySchemes) {
			component := components.SecuritySchemes[name]
			if err = loader.resolveSecuritySchemeRef(doc, component, location); err != nil {
				return
			}
		}
		for _, name := range componentNames(components.Examples) {
			component := components.Examples[name]
			if err = loader.resolveExampleRef(doc, component, location); err != nil {
				return
			}
		}
		for _, name := range componentNames(components.Callbacks) {
			component := components.Callbacks[name]
			if err = loader.resolveCallbackRef(doc, component, location); err != nil {
				return
			}
		}
	}

	// Visit all operations
	pathItems := doc.Paths.Map()
	for _, name := range componentNames(pathItems) {
		pathItem := pathItems[name]
		if pathItem == nil {
			continue
		}
		if err = loader.resolvePathItemRef(doc, pathItem, location); err != nil {
			return
		}
	}

	for _, name := range componentNames(doc.Webhooks) {
		if pathItem := doc.Webhooks[name]; pathItem != nil {
			if err = loader.resolvePathItemRef(doc, pathItem, location); err != nil {
				return
			}
		}
	}

	return
}

func defaultJoin(basePath *url.URL, relativePath *url.URL) *url.URL {
	if basePath == nil {
		return relativePath
	}
	newPath := *basePath
	newPath.Path = path.Join(path.Dir(newPath.Path), relativePath.Path)
	return &newPath
}

func (loader *Loader) resolvePath(basePath *url.URL, componentPath *url.URL) *url.URL {
	if is_file(componentPath) {
		// support absolute paths
		if filepath.IsAbs(componentPath.Path) {
			return componentPath
		}
		if loader.JoinFunc != nil {
			return loader.JoinFunc(basePath, componentPath)
		}
		return defaultJoin(basePath, componentPath)
	}
	return componentPath
}

func (loader *Loader) resolvePathWithRef(ref string, rootPath *url.URL) (*url.URL, error) {
	parsedURL, err := url.Parse(ref)
	if err != nil {
		return nil, fmt.Errorf("cannot parse reference: %q: %w", ref, err)
	}

	resolvedPath := loader.resolvePath(rootPath, parsedURL)
	resolvedPath.Fragment = parsedURL.Fragment
	return resolvedPath, nil
}

func (loader *Loader) resolveRefPath(ref string, path *url.URL) (*url.URL, error) {
	if ref != "" && ref[0] == '#' {
		path = copyURI(path)
		// Resolving internal refs of a doc loaded from memory
		// has no path, so just set the Fragment.
		if path == nil {
			path = new(url.URL)
		}

		path.Fragment = ref
		return path, nil
	}

	// IsExternalRefsAllowed is enforced here only when no custom ReadFromURIFunc
	// is installed; otherwise the custom func owns the access policy (see the
	// SECURITY note on the ReadFromURIFunc field).
	if loader.ReadFromURIFunc == nil {
		if err := loader.allowsExternalRefs(ref); err != nil {
			return nil, err
		}
	}

	resolvedPath, err := loader.resolvePathWithRef(ref, path)
	if err != nil {
		return nil, err
	}

	return resolvedPath, nil
}

func isSingleRefElement(ref string) bool {
	return !strings.Contains(ref, "#")
}

func (loader *Loader) visitRef(ref string) {
	if loader.visitedRefs == nil {
		loader.visitedRefs = make(map[string]struct{})
		loader.backtrack = make(map[string][]func(value any))
	}
	loader.visitedPath = append(loader.visitedPath, ref)
	loader.visitedRefs[ref] = struct{}{}
}

func (loader *Loader) unvisitRef(ref string, value any) {
	if value != nil {
		for _, fn := range loader.backtrack[ref] {
			fn(value)
		}
	}
	delete(loader.visitedRefs, ref)
	delete(loader.backtrack, ref)
	loader.visitedPath = loader.visitedPath[:len(loader.visitedPath)-1]
}

func (loader *Loader) shouldVisitRef(ref string, fn func(value any)) bool {
	if _, ok := lo
... [truncated, file is 48360 chars]
```

### openapi3/origin.go
[omitted: context budget exhausted]

### openapi3/path_item.go
[omitted: context budget exhausted]

### openapi3/schema.go
[omitted: context budget exhausted]

### openapi3/schema_formats.go
[omitted: context budget exhausted]

### openapi3/schema_jsonschema_validator.go
[omitted: context budget exhausted]

### openapi3/schema_pattern.go
[omitted: context budget exhausted]

### openapi3/schema_validation_settings.go
[omitted: context budget exhausted]

### openapi3/testdata/apis_guru_openapi_directory/flat_io_2_13_0_openapi_yaml__validate
[omitted: context budget exhausted]

### openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Prediction_3_0_openapi_yaml__validate
[omitted: context budget exhausted]

### openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_0_openapi_yaml__validate
[omitted: context budget exhausted]

### openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_1_openapi_yaml__validate
[omitted: context budget exhausted]

### openapi3/testdata/apis_guru_openapi_directory/microsoft_com_cognitiveservices_Training_3_2_openapi_yaml__validate
[omitted: context budget exhausted]

### openapi3/testdata/apis_guru_openapi_directory/mist_com_0_37_7_openapi_yaml__validate
[omitted: context budget exhausted]

### openapi3/testdata/apis_guru_openapi_directory/ndhm_gov_in_ndhm_cm_0_5_openapi_yaml__validate
[omitted: context budget exhausted]

### openapi3/testdata/apis_guru_openapi_directory/nexmo_com_voice_1_3_10_openapi_yaml__validate
[omitted: context budget exhausted]

### openapi3/testdata/discriminatorLocalMapping.yml
[omitted: context budget exhausted]

### openapi3/testdata/discriminatorLocalMapping.yml.internalized.yml
[omitted: context budget exhausted]

### openapi3/testdata/issue1205/ext.yml
[omitted: context budget exhausted]

### openapi3/testdata/issue1205/mutual-a.yml
[omitted: context budget exhausted]

### openapi3/testdata/issue1205/mutual-b.yml
[omitted: context budget exhausted]

### openapi3/testdata/issue1205/mutual.yml
[omitted: context budget exhausted]

### openapi3/testdata/issue1205/mutual.yml.internalized.yml
[omitted: context budget exhausted]

### openapi3/testdata/issue1205/openapi.yml
[omitted: context budget exhausted]

### openapi3/testdata/issue1205/openapi.yml.internalized.yml
[omitted: context budget exhausted]

### openapi3/validation_code.go
[omitted: context budget exhausted]

### openapi3/validation_error.go
[omitted: context budget exhausted]

### openapi3/walk_parameters.go
[omitted: context budget exhausted]

### openapi3/walk_schemas.go
[omitted: context budget exhausted]

### openapi3filter/req_resp_decoder.go
[omitted: context budget exhausted]

### openapi3filter/testdata/encoded_path_authorization_bypass.yml
[omitted: context budget exhausted]

### openapi3filter/validation_handler.go
[omitted: context budget exhausted]

### routers/gorillamux/router.go
[omitted: context budget exhausted]

### routers/legacy/router.go
[omitted: context budget exhausted]
Callers & Entry Points (How public input reaches the modified code)
(none)
Repository Map
(no source files found)
Package Manifests (Dependencies, scripts, build configuration)
### go.mod
```
module github.com/getkin/kin-openapi

go 1.25

require (
	github.com/go-openapi/jsonpointer v0.22.5
	github.com/gorilla/mux v1.8.0
	github.com/oasdiff/yaml v0.1.1
	github.com/oasdiff/yaml3 v0.0.14
	github.com/santhosh-tekuri/jsonschema/v6 v6.0.2
	github.com/stretchr/testify v1.9.0
)

require (
	github.com/davecgh/go-spew v1.1.1 // indirect
	github.com/go-openapi/swag/jsonname v0.25.5 // indirect
	github.com/kr/text v0.2.0 // indirect
	github.com/pmezard/go-difflib v1.0.0 // indirect
	golang.org/x/text v0.14.0 // indirect
	gopkg.in/check.v1 v1.0.0-20201130134442-10cb98267c6c // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)

```
Context & Existing Test Patterns
Existing test files touched by the patch: openapi2conv/custom_methods_test.go, openapi3/ghsa_mh7x_f8wq_4jhx_test.go, openapi3/internalize_refs_test.go, openapi3/issue1044_test.go, openapi3/issue1243_test.go, openapi3/issue1244_test.go, openapi3/origin_external_ref_test.go, openapi3/origin_retention_test.go, openapi3/origin_test.go, openapi3/path_item_custom_methods_test.go, openapi3/schema_prefix_items_test.go, openapi3/schema_test.go, openapi3/validation_code_test.go, openapi3/validation_error_test.go, openapi3filter/array_items_nil_panic_test.go, openapi3filter/circular_recursion_test.go, openapi3filter/encoded_path_route_confusion_test.go, openapi3filter/ghsa_74vm_87hj_r66f_test.go, openapi3filter/issue1105_test.go, openapi3filter/issue1112_test.go, openapi3filter/issue1230_test.go, openapi3filter/issue1243_test.go, openapi3filter/issue1246_test.go, openapi3filter/validate_request_custom_methods_test.go, openapi3filter/validate_request_test.go, openapi3filter/validation_error_test.go, openapi3filter/yaml_nan_inf_test.go, routers/gorillamux/router_custom_methods_test.go, routers/legacy/router_custom_methods_test.go
Repository top-level entries: .gitattributes, .github, .gitignore, LICENSE, Makefile, README.md, cmd, docs.sh, go.mod, go.sum, maps.sh, openapi2, openapi2conv, openapi3, openapi3conv, openapi3filter, openapi3gen, routers
Project's own test patterns and conventions:
### openapi3filter/validate_request_test.go
```
package openapi3filter

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/getkin/kin-openapi/routers"
	"github.com/getkin/kin-openapi/routers/gorillamux"
	legacyrouter "github.com/getkin/kin-openapi/routers/legacy"
)

func setupTestRouter(t *testing.T, spec string) routers.Router {
	t.Helper()
	loader := openapi3.NewLoader()
	doc, err := loader.LoadFromData([]byte(spec))
	require.NoError(t, err)

	err = doc.Validate(loader.Context)
	require.NoError(t, err)

	router, err := gorillamux.NewRouter(doc)
	require.NoError(t, err)

	return router
}

func TestValidateRequest(t *testing.T) {
	const spec = `
openapi: 3.0.0
info:
  title: 'Validator'
  version: 0.0.1
paths:
  /category:
    post:
      parameters:
        - name: category
          in: query
          schema:
            type: string
          required: true
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - subCategory
              properties:
                subCategory:
                  type: string
                category:
                  type: string
                  default: Sweets
      responses:
        '201':
          description: Created
      security:
      - apiKey: []
components:
  securitySchemes:
    apiKey:
      type: apiKey
      name: Api-Key
      in: header
`

	router := setupTestRouter(t, spec)

	verifyAPIKeyPresence := func(c context.Context, input *AuthenticationInput) error {
		if input.SecurityScheme.Type == "apiKey" {
			var found bool
			switch input.SecurityScheme.In {
			case "query":
				_, found = input.RequestValidationInput.GetQueryParams()[input.SecurityScheme.Name]
			case "header":
				_, found = input.RequestValidationInput.Request.Header[http.CanonicalHeaderKey(input.SecurityScheme.Name)]
			case "cookie":
				_, err := input.RequestValidationInput.Request.Cookie(input.SecurityScheme.Name)
				found = !errors.Is(err, http.ErrNoCookie)
			}
			if !found {
				return fmt.Errorf("%v not found in %v", input.SecurityScheme.Name, input.SecurityScheme.In)
			}
		}
		return nil
	}

	type testRequestBody struct {
		SubCategory string `json:"subCategory"`
		Category    string `json:"category,omitempty"`
	}
	type args struct {
		requestBody *testRequestBody
		url         string
		apiKey      string
	}
	tests := []struct {
		name                 string
		args                 args
		expectedModification bool
		expectedErr          error
	}{
		{
			name: "Valid request with all fields set",
			args: args{
				requestBody: &testRequestBody{SubCategory: "Chocolate", Category: "Food"},
				url:         "/category?category=cookies",
				apiKey:      "SomeKey",
			},
			expectedModification: false,
			expectedErr:          nil,
		},
		{
			name: "Valid request without certain fields",
			args: args{
				requestBody: &testRequestBody{SubCategory: "Chocolate"},
				url:         "/category?category=cookies",
				apiKey:      "SomeKey",
			},
			expectedModification: true,
			expectedErr:          nil,
		},
		{
			name: "Invalid operation params",
			args: args{
				requestBody: &testRequestBody{SubCategory: "Chocolate"},
				url:         "/category?invalidCategory=badCookie",
				apiKey:      "SomeKey",
			},
			expectedModification: false,
			expectedErr:          &RequestError{},
		},
		{
			name: "Invalid request body",
			args: args{
				requestBody: nil,
				url:         "/category?category=cookies",
				apiKey:      "SomeKey",
			},
			expectedModification: false,
			expectedErr:          &RequestError{},
		},
		{
			name: "Invalid security",
			args: args{
				requestBody: &testRequestBody{SubCategory: "Chocolate"},
				url:         "/category?category=cookies",
				apiKey:      "",
			},
			expectedModification: false,
			expectedErr:          &SecurityRequirementsError{},
		},
		{
			name: "Invalid request body and security",
			args: args{
				requestBody: nil,
				url:         "/category?category=cookies",
				apiKey:      "",
			},
			expectedModification: false,
			expectedErr:          &SecurityRequirementsError{},
		},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			var requestBody io.Reader
			var originalBodySize int
			if tc.args.requestBody != nil {
				testingBody, err := json.Marshal(tc.args.requestBody)
				require.NoError(t, err)
				requestBody = bytes.NewReader(testingBody)
				originalBodySize = len(testingBody)
			}
			req, err := http.NewRequest(http.MethodPost, tc.args.url, requestBody)
			require.NoError(t, err)
			req.Header.Add("Content-Type", "application/json")
			if tc.args.apiKey != "" {
				req.Header.Add("Api-Key", tc.args.apiKey)
			}

			route, pathParams, err := router.FindRoute(req)
			require.NoError(t, err)

			validationInput := &RequestValidationInput{
				Request:    req,
				PathParams: pathParams,
				Route:      route,
				Options: &Options{
					AuthenticationFunc: verifyAPIKeyPresence,
				},
			}
			err = ValidateRequest(t.Context(), validationInput)
			assert.IsType(t, tc.expectedErr, err, "ValidateRequest(): error = %v, expectedError %v", err, tc.expectedErr)
			if tc.expectedErr != nil {
				return
			}
			body, err := io.ReadAll(validationInput.Request.Body)
			contentLen := int(validationInput.Request.ContentLength)
			bodySize := len(body)
			assert.NoError(t, err, "unable to read request body: %v", err)
			assert.Equal(t, contentLen, bodySize, "expect ContentLength %d to equal body size %d", contentLen, bodySize)
			bodyModified := originalBodySize != bodySize
			assert.Equal(t, tc.expectedModification, bodyModified, "expect request body modification happened: %t, expected %t", bodyModified, tc.expectedModification)

			validationInput.Request.Body, err = validationInput.Request.GetBody()
			assert.NoError(t, err, "unable to re-generate body by GetBody(): %v", err)
			body2, err := io.ReadAll(validationInput.Request.Body)
			assert.NoError(t, err, "unable to read request body: %v", err)
			assert.Equal(t, body, body2, "body by GetBody() is not matched")
		})
	}
}

func TestValidateQueryParams(t *testing.T) {
	type testCase struct {
		name  string
		param *openapi3.Parameter
		query string
		want  map[string]any
		err   *openapi3.SchemaError // test ParseError in decoder tests
	}

	testCases := []testCase{
		{
			name: "deepObject explode additionalProperties with object properties - missing required property",
			param: &openapi3.Parameter{
				Name: "param", In: "query", Style: "deepObject", Explode: explode,
				Schema: objectOf(
					"obj", additionalPropertiesObjectOf(func() *openapi3.SchemaRef {
						s := objectOf(
							"item1", integerSchema,
							"requiredProp", stringSchema,
						)
						s.Value.Required = []string{"requiredProp"}

						return s
					}()),
					"objIgnored", objectOf("items", stringArraySchema),
				),
			},
			query: "param[obj][prop1][item1]=1",
			err:   &openapi3.SchemaError{SchemaField: "required", Reason: "property \"requiredProp\" is missing"},
		},
		{
			// XXX should this error out?
			name: "deepObject explode additionalProperties with object properties - extraneous nested param property ignored",
			param: &openapi3.Parameter{
				Name: "param", In: "query", Style: "deepObject", Explode: explode,
				Schema: objectOf(
					"obj", additionalPropertiesObjectOf(objectOf(
						"item1", integerSchema,
						"requiredProp", stringSchema,
					)),
					"objIgnored", objectOf("items", stringArraySchema),
				),
			},
			query: "param[obj][prop1][inexistent]=1",
			want: map[string]any{
				"obj": map[string]any{
					"prop1": map[string]any{},
				},
			},
		},
		{
			name: "deepObject explode additionalProperties with object properties",
			param: &openapi3.Parameter{
				Name: "param", In: "query", Style: "deepObject", Explode: explode,
				Schema: objectOf(
					"obj", additionalPropertiesObjectOf(objectOf(
						"item1", numberSchema,
						"requiredProp", stringSchema,
					)),
					"objIgnored", objectOf("items", stringArraySchema),
				),
			},
			query: "param[obj][prop1][item1]=1.123",
			want: map[string]any{
				"obj": map[string]any{
					"prop1": map[string]any{
						"item1": float64(1.123),
					},
				},
			},
		},
		{
			name: "deepObject explode nested objects - misplaced parameter",
			param: &openapi3.Parameter{
				Name: "param", In: "query", Style: "deepObject", Explode: explode,
				Schema: objectOf(
					"obj", objectOf("nestedObjOne", objectOf("items", stringArraySchema)),
				),
			},
			query: "param[obj][nestedObjOne]=baz",
			err: &openapi3.SchemaError{
				SchemaField: "type", Reason: "value must be an object", Value: "baz", Schema: objectOf("items", stringArraySchema).Value,
			},
		},
		{
			name: "deepObject explode nested object - extraneous param ignored",
			param: &openapi3.Parameter{
				Name: "param", In: "query", Style: "deepObject", Explode: explode,
				Schema: objectOf(
					"obj", objectOf("nestedObjOne", stringSchema, "nestedObjTwo", stringSchema),
				),
			},
			query: "anotherparam=bar",
			want:  map[string]any(nil),
		},
		{
			name: "deepObject explode additionalProperties with object properties - multiple properties",
			param: &openapi3.Parameter{
				Name: "param", In: "query", Style: "deepObject", Explode: explode,
				Schema: objectOf(
					"obj", additionalPropertiesObjectOf(objectOf("item1", integerSchema, "item2", stringArraySchema)),
					"objIgnored", objectOf("items", stringArraySchema),
				),
			},
			query: "param[obj][prop1][item1]=1&param[obj][prop1][item2][0]=abc&param[obj][prop2][item1]=2&param[obj][prop2][item2][0]=def",
			want: map[string]any{
				"obj": map[string]any{
					"prop1": map[string]any{
						"item1": int64(1),
						"item2": []any{"abc"},
					},
					"prop2": map[string]any{
						"item1": int64(2),
						"item2": []any{"def"},
					},
				},
			},
		},

		//
		//
		{
			name: "deepObject explode nested object anyOf",
			param: &openapi3.Parameter{
				Name: "param", In: "query", Style: "deepObject", Explode: explode,
				Schema: objectOf(
					"obj", anyofSchema,
				),
			},
			query: "param[obj]=1",
			want: map[string]any{
				"obj": int64(1),
			},
		},
		{
			name: "deepObject explode nested object allOf",
			param: &openapi3.Parameter{
				Name: "param", In: "query", Style: "deepObject", Explode: explode,
				Schema: objectOf(
					"obj", allofSchema,
				),
			},
			query: "param[obj]=1",
			want: map[string]any{
				"obj": int64(1),
			},
		},
		{
			name: "deepObject explode nested object oneOf",
			param: &openapi3.Parameter{
				Name: "param", In: "query", Style: "deepObject", Explode: explode,
				Schema: objectOf(
					"obj", oneofSchema,
				),
			},
			query: "param[obj]=true",
			want: map[string]any{
				"obj": true,
			},
		},
		{
			name: "deepObject explode nested object oneOf - object",
			param: &openapi3.Parameter{
				Name: "param", In: "query", Style: "deepObject", Explode: explode,
				Schema: objectOf(
					"obj", oneofSchemaObject,
				),
			},
			query: "param[obj][id2]=1&param[obj][name2]=abc",
			want: map[string]any{
				"obj": map[string]any{
					"id2":   "1",
					"name2": "abc",
				},
			},
		},
		{
			name: "deepObject explode nested object oneOf - object - more than one match",
			param: &openapi3.Parameter{
				Name: "param", In: "query", Style: "deepObject", Explode: explode,
				Schema: objectOf(
					"obj", oneofSchemaObject,
				),
			},
			query: "param[obj][id]=1&param[obj][id2]=2",
			err: &openapi3.SchemaError{
				SchemaField: "oneOf",
				Value:       map[string]any{"id": "1", "id2": "2"},
				Reason:      "value matches more than one schema from \"oneOf\" (matches schemas at indices [0 1])",
				Schema:      oneofSchemaObject.Value,
			},
		},
		{
			name: "deepObject explode nested object oneOf - array",
			param: &openapi3.Parameter{
			
```
Your Deliverables
Artifact 1: instruction.md - The Incident Defect Report
Write a realistic report (about 150-350 words) as a user or operator who hit the problem. Sections: a title naming
the symptom (not the fix); what was observed and how (the route the user hit); impact; what must keep working.

WHAT ACTUALLY DECIDES DIFFICULTY (measured, 2 accepted vs 37 solved): not how vague the report is, but whether part of
the root cause lives in a REAL place the report never leads to, with a test that reaches it. The accepted hono task's
report stated the cause and the rule, and listed three affected wrappers - both models still failed 6/6, because the
second renderer and the nested-array root were never mentioned and were tested. So the report may describe the
route(s) the user hit; its one job is to NOT reveal the hidden place(s) or how far the bug reaches.

NEVER (each measured on a task both models then solved; ids are the evidence):
- state the SCOPE or completeness of the bug: "the same acceptance happens on each one we tried", "for every operation",
  "on every route", "every command that ...", "all three nodes". It tells the agent to grep for every sibling and the
  trap disappears - oauth-providers fm3f, n8n f3f2, vitest p63j, q2xc (all four solved on attempt 1). Show the route(s)
  the user hit; whether others exist is for the agent to find;
- reveal or hint at a hidden place (metadata.trap.paths): not by name, and not by a role specific enough to find it;
- list the tainted parameters, the payload set or the variants your tests use (n8n f3f2 named all four tainted
  parameters and the legal operator list). One illustrative example of the symptom is fine;
- name a function by a behaviour so specific it identifies it ("the one that ignores the address's own suffix" - j6r3);
- offer or rule on an acceptable fix ("refusing the archive is fine" - p634) or say which layer should change;
- in "what must keep working", list the boundary VALUES your tests use ("/0 networks, IPv4-mapped addresses",
  "[db].[dbo].[t], numeric-string limits"). Name the FEATURES that must keep working (hono: "a bare string must still
  render as the top-level element", "content marked as trusted raw HTML still emits markup");
- file, directory, module, function, method or class names the fix changes, options it adds, or line numbers.
AVOID stating the root cause when the fix is in one local place: there it IS the answer (adm-zip p634: "two entries
with the same name"; ip-address j6r3: "never checks both sides are the same kind of address").
Write in your OWN words. Do not quote the official CVE/GHSA summary, and do not include the CVE/OSV ID.
Fairness: every test_functional_* exercises an ordinary use of a feature named under "what must keep working", and
every test_security_* is an instance of the harm described.
Artifact 2: hidden_tests.py - Black-Box Pytest Suite
The suite runs at the repository root with REPO_ROOT set.
Strict Constraints:
Pure pytest, deterministic, offline (no internet access, no sleeps > 1s, harmless sentinels/tmp_path only).
Black-Box Execution: Test ONLY via public entry points (public CLI commands, public API methods, exported library
functions, or HTTP route handlers). NEVER import, inspect, or call new helper functions, new structs, or new fields
introduced by the reference patch.
Agnostic Assertions: Accept ANY valid rejection mechanism (raised exception, HTTP 4xx, sanitized return value).
Never assert on exact error string text or specific internal exception classes added by the patch.
Language Adapters:
Python: Direct import of public pre-patch modules.
Node/TypeScript: Use subprocess to run project's test runner (vitest/jest) or inline node script driving src/ (NEVER dist/).
Go: Write temporary zz_hidden_<name>_test.go and execute via go test -count=1 ./<pkg>.
PHP (Composer): Write a temporary zz_hidden_<name>.php in the repo root starting with require __DIR__ . '/vendor/autoload.php';
drive the project's public API or HTTP kernel the way its own tests do, print ONE JSON line of what a caller observes, and
run it with php via subprocess (remove the file in a finally block). Use only classes that exist in the PRE-patch source;
never change composer.json/composer.lock; no database or network - use the project's in-memory/array/SQLite drivers.
Non-Destructive Invariant: The reference patch MUST score 100% (all tests pass). The vulnerable code MUST fail all
test_security_* tests.
Naming & Test Structure:
test_security_* (at least 3, ideally 4-8): Fail on vulnerable code, pass after a correct fix.
COVER EVERY FIX PLACE (the #1 measured cause of easy tasks: in 24 of 37 solved tasks the agent passed while changing
FEWER source files than the reference fix - e.g. 1 of 12 - because no test reached the other places). List every source
place the reference fix hardens; give EACH its own test_security_* reached through its OWN real entry point, so a
repair that skips any one place fails. A variant counts only if it reaches the root cause through a DIFFERENT place or
route. Spelling, case, whitespace, encoding or extension variants of the same input through the same route do NOT
count - measured: pure spelling/encoding variants are always caught, and input variants were never missed.
Strongest sibling kinds to target (measured miss rates): a mechanism that never had the protection so its absence
reads as design (32%); a producer - schema, serializer, loader, config resolver - that feeds the check through a path
the check never calls (29%); a second real implementation (fallback backend, adapter, inline copy) (19%); the check
authorising the wrong/neighbouring object or an attacker-chosen identity field; the restricted value arriving through
defaults, merge, inheritance or stored config. Prefer REAL siblings the upstream fix also changed or never touched.
test_functional_* (at least 3, ideally 4-8): Pass on both vulnerable and fixed code.
Legitimate inputs near the rejection boundary, custom enterprise configurations, and valid workflows. An over-broad
fix that disables features or universally rejects input must fail these tests.
Hard Rules Learned from Historical QA Rejections
THE FAIRNESS CONTRACT (NO UNSEEN PLUMBING): every test_functional_* must exercise an ordinary use of a FEATURE named
under "What must keep working" - name the feature, not the test's values. If a test needs private enterprise registries
(e.g. my-tfe.corp.example), the report says that "users who configure a private registry" must keep working; it does
not list hosts, env vars or edge cases. A feature the vulnerable code never supported is not "legitimate" (infracost).
SIBLING BLAST RADIUS (INCOMPLETE UPSTREAM FIXES): If the reference patch only fixes 7 out of 8 providers/parsers
(leaving sibling components vulnerable), and an intelligent agent fixing the 8th component would break pre-existing
repository tests (e.g., legacy tests asserting unauthenticated behavior for provider X), answer ONLY with:
<unsuitable>incomplete upstream fix: sibling provider tests break under full remediation</unsuitable>.
IMPLEMENTATION INDEPENDENCE: A test must pass for ANY reasonable, correct architecture. Never assert that a check
lives in a specific layer, or that internal state changed in a specific way, when an alternative placement is equally sound.
COMPILED REPOSITORIES (TS/GO): Test source code directly. Never require compiled bundles (dist/index.js) which
do not exist until build and would omit agent edits.
NO TRIVIAL OR SYNTHETIC CODE: If the vulnerability is a pure dependency bump, a config toggle, or does not support
a multi-file / deeper-layer trap, answer ONLY with: <unsuitable>no hidden-path trap: <reason></unsuitable>.
Artifact 3: check_patches - Three Validation Fixes
Provide search/replace edits on pre-patch source files to verify test suite discrimination:
"shallow": Quick band-aid fixing only the primary trigger. Must pass >= 1 security test, but FAIL >= 1 security variant.
"removal": Over-restrictive fix (disables feature/returns early). Must FAIL >= 1 functional test.
"alternative": A correct, clean fix designed differently than the reference patch. Must PASS ALL tests.
Output Format (Strict XML Blocks Only)
Return ONLY these four blocks, nothing else:
<instruction_md>
...markdown matching the exact section structure specified above...
</instruction_md>
<hidden_tests_py>
...python source, no code fences...
</hidden_tests_py>
<task_metadata_json>
{
"entry_point": "<public entry point string>",
"techniques": [1, 5, 9],
"trap": {
"paths": ["<repo-relative source file agent is likely to miss>"],
"contract": "<the specific legitimate behavior near the boundary that functional tests pin>"
},
"fix_places": ["<EVERY reference-fix source file whose change closes part of the vulnerability; the pipeline re-runs the fix
               WITHOUT each one and a test must then fail>"],
"unrelated_files": ["<every OTHER reference-fix source file (refactor, typing, logging, an unrelated feature bundled in the
                    commit). Every source file of the reference patch must appear in fix_places or here>"],
"test_justifications": {
"<test_function_name>": "<exact sentence or quote from instruction.md requiring this test's assertion>"
}
}
</task_metadata_json>
<check_patches_json>
{
"shallow": [{"file": "<path>", "search": "<exact existing code>", "replace": "<new code>"}],
"removal": [...],
"alternative": [...]
}
</check_patches_json>


# The checks your task will face (write it to pass all of them the first time)
An independent reviewer scores the task on these criteria; any failed "must pass" criterion sends it back:
- no_hints (must pass): instruction.md names no file, module, path, line number, or function/class the fix changes AND does not prescribe the fix: an 'expected behaviour' part may state the security property and the legitimate behaviour to keep, but must not describe validation rules, accepted token formats, ordering of checks, or logging-vs-returning choices that amount to the fix design
- accurate_report (must pass): the report describes the vulnerability the oracle patch actually fixes (impact + how it is triggered), without inventing a different flaw
- solvable_from_report (must pass): a skilled engineer who reads the report and the code could determine every behaviour the hidden tests require; no test demands undisclosed or arbitrary behaviour
- real_entry_point (must pass): security tests reach the bug through a real entry point (public API/route/CLI), not by calling the internal function the patch edits
- variants_share_root_cause (must pass): extra exploit variants share the root cause and are all blocked by the oracle patch (no extra hardening the oracle does not provide)
- implementation_agnostic (must pass): tests never import/assert anything the patch adds, never assert exact error text, and accept any reasonable way of blocking the attack
- functional_meaningful (must pass): functional tests would FAIL if the feature were removed, disabled or over-blocked, yet pass on the vulnerable code
- deterministic_offline (must pass): no network, no timing/sleep-based races, no randomness that can flip a result
- realistic (must pass): the scenario is a realistic use of the project, not a contrived snippet or unreachable code
- security_not_trivial_config (must pass): the vulnerability is in program logic, not a dependency bump or config toggle
Then the task is EXECUTED: the reference fix must score 1.0 twice; the vulnerable code must fail every test_security_*
and pass every test_functional_*; the repo's own related tests must pass before and after the fix; your three check
patches run against your tests (shallow must still fail a security test, removal must fail a functional test,
alternative must pass everything); and if both target models can name the fix location from your report alone, the
task is rejected (so describe behaviour, never location).


# Design contract (measured: tasks that break BOTH models satisfy these)
1. At least TWO independent public entry points reach the root cause. The report names at most one; the other is
   discoverable by reading the code (a second renderer/parser/implementation, a lower-level public constructor, a
   second HTTP route/CLI, or a save/reload round-trip). Give each entry point its own test_security_*.
2. At EACH entry point, test at least two input shapes (bare value vs array/nested; path vs bytes; casing or encoding
   variants). A fix that handles only the reported shape must still fail.
3. Put at least one affected sink in a module whose path/name does not suggest the vulnerability; the report must not
   name it.
4. Include a functional test for every "must keep working" clause: it must PASS on the PRE-patch code and FAIL if the
   feature is removed or over-blocked.
5. At least one security test must be blocked only by the fix's change in a SECOND source file, not by the obvious
   first file. If the whole fix is one shared choke point, the models will solve the task.


# Task-design techniques (curated - follow them)
## What counts as a model failure (the grading contract)
- A task is solved only by reward 1.0: every hidden security test, every hidden functional test and every enforced
  existing repo test passes. Anything less is a FAILURE, including:
  - **Partial fix:** the agent closes some attack paths but not all (e.g. 5 of 6 security variants blocked). This is the
    most valuable failure: the model was confident and wrong ("silent failure").
  - **Fix that breaks something:** the hole is closed but a legitimate behaviour, an existing repo test, or the build
    breaks (over-correction / regression).
  - Both at once.
- A task is ACCEPTED when every attempt of both models (3 + 3) is such a failure, and the deterministic checks prove
  each failure is the model's (graded, no API/harness crash, agent really worked, no tampering). No AI judge decides.
- The goal is to MEASURE repair quality: a task only an incomplete or over-broad repair fails is a good task.
- So every task must be designed so that (a) a partial fix still fails and (b) an over-broad fix still fails.
- **Measured: models fail in two ways, equally often.** In the 2 QA-verified ACCEPTED tasks, 6 of 12 failures
  were over-corrections (apprise: hole closed, a pinned interface broken) and 6 left a path open (hono: a second
  renderer / input shape). So spend as much design effort on legitimate use as on attacks: functional tests for
  every legitimate input shape next to each attack variant, a public interface the repo's own tests pin
  (technique 11), and existing behaviour the obvious
  fix would change (hono: nested-array roots; apprise: the plugin `meta` dict). A "must keep working" test must follow from the report and
  pass on any correct fix - never a design only the reference fix makes (fairness QA withdrew infracost GHSA-6x6c and
  oauth-providers GHSA-fm3f for exactly that).

## Pattern catalogue - evidence-ranked from 471 measured sibling traps (2026-10-20)
A task shows ONE symptom through ONE route (the base bug). A **sibling** is another place the same protection is
missing that the report never names; a fix of the reported site alone then scores < 1.0. Every trap has two axes.

### Origin - where the sibling comes from (this is what decides difficulty, more than the mechanism)
- **A-FAR** (Pattern A): a site the real upstream fix ALSO changed, which the report does not lead to. **19% missed.** KEEP.
- **B-ROUTE** (Pattern B): a real, unmodified route with the same gap the upstream fix never touched. **25% missed - the strongest.** KEEP.
- **INJ** (injected/planted by us): **5% missed - almost never bites.** Once a model accepts the concept it closes all
  planted routes together (124 of 166 injected siblings are just M1/M2 routes of the stated concept). **TOO EASY - do not
  rely on injected siblings as the difficulty.** Confirmed 2026-10-20: our filament injection was declared unsuitable by
  the trap gate itself - every planted surface passed through one query scoper, so one restoration closed them all.
- Non-sibling kinds: **BASE** (the reported site), **SHAPE TRAP** (pure spelling/encoding variant of a route - ALWAYS
  caught, TOO EASY), **COUPLED TRAP** (a must-keep-working legitimate value next to the hidden one, tested functionally -
  bites, esp. MiMo which over-hardens; DeepSeek breaks coupled values too).

### Mechanism - why a model skips the sibling (miss rate = missed in >=1 run / siblings with trial data)
TOP BREAKERS (design toward these, on REAL code = A-FAR or B-ROUTE):
- **M4 Feature-absent** - the mechanism never had the protection, so its absence reads as design ("unsupported combo, not
  a boundary"). **7/22 = 32%, highest.** e.g. jackson any-setter has no view code.
- **M6 Producer off the check's path** - a schema/serializer/loader/config-resolver feeds the check through a path the
  check never calls; the model follows calls INTO the check, never asks where its data comes from. **5/17 = 29%.**
- **M2 Second implementation** (real, not injected) - a duplicate copy of the guarded logic: another package, fallback
  backend, adapter, inline copy. **14/73 = 19%.** "That path uses its own helper / only a fallback."
- **M10 Wrong object** - authorises a neighbouring/proxy object, or trusts an attacker-chosen identity field. **2/11.**
- **M5 Merged/defaults route** - the restricted value arrives via defaults/merge/inheritance/patch/stored-config; the
  model treats the report's example fields as the whole set.
- **M11 Coupled contract** - a linked visible value or shared helper must keep working; the natural fix breaks it
  (over-broad-fix trap). Bites MiMo hard.
WEAK / TOO EASY (do not use as the sole difficulty):
- **M1 Parallel entry** - another handler/endpoint/tool reaches the same sink. Only **12/99 = 12%** on real code, and ~0
  when injected. Allowed only as a secondary trap stacked with a top breaker.
- **M8 Parser differential** - genuine canonicalisation mismatch bites rarely (1/18); **pure spelling/case/encoding is
  always caught - TOO EASY.**
- **M12 Input variants** (encoding/spelling/verb/protocol/role of a stated input) - **never missed. TOO EASY, remove.**
- **M3 Shared layer** (0/6) and **M9 Fail-open fallback** (0/9) - never observed to bite; not proven breakers.

### The winning recipe (the only both-model breaker, jackson-databind-sib2, audited)
Uses NO planted code. A **Pattern B** route that **stacks several DIFFERENT mechanisms**: M4 (any-setter ignores views) +
M10+M11 (object-id stand-in property) + M5 (array/merge update) + a **coupled visible value an over-broad fix breaks**.
So: pick a real uncovered route, give it 2-3 different mechanisms, and pin a coupled legitimate value functionally.

### Avoid the checklist tell
Model-built (-ds/-mm) reports don't name siblings but describe each sibling's surface in product terms, one clause per
trap - that hands the solver a map. Never enumerate the HIDDEN places. (hono's report listed three affected wrappers
and still broke both models - because the places that decided it, the second renderer and the nested-array root, were
not in the list. Describing the route the user hit is fine; describing where else it lives is not.)

---

## Legacy numbered techniques (still referenced by the generator gate and scoreboard; map to the catalogue above)
Mapping: 1->M1, 2->dismissal-reason, 3->M3, 4->grading, 5->M11/coupled, 6->leak discipline, 7->M2, 8->RETIRED (M12),
9->M11, 10->RETIRED (width), 11->M11, 12->M4, 13->M6, 14->M10, 15->M5. The generator's trap gate accepts 1, 2, 3, 7 and
12-15 as hidden-path techniques; prefer 12, 13 and a real (not injected) 7. M1 parallel entry alone is weak (12%).

## What makes a repair task demanding - so only a complete, careful repair passes (use several in ONE task)
1. **Unnamed sibling path.** The report describes the reported trigger only. The same root cause is reachable through
   a second entry point, a second code path, or a round-trip (serialize -> store -> parse) that the report never
   names. Give it its own security test. Evidence: DeepSeek missed the schema round-trip variant in 3/3 runs on 6qxp.
2. **Already-protected-looking code.** One path already validates correctly, so the model reads the area as "handled"
   and patches only the path the report mentions (pyload jq7h, 6qxp).
3. **Fix across a layer boundary.** The correct fix must reach from the entry layer into a deeper layer (e.g. a core
   API that cannot see the web session, an SDK helper that cannot see the stored binding). Local guards at the entry
   point are the shallow fix your tests must catch.
4. **One test per fix place.** Each place the reference fix hardens gets its own `test_security_*` reached through its
   own entry point, so a fix that skips one place still scores < 1.0. (Was "one test per variant"; spelling, case and
   encoding variants of one input through one route are always caught and do not count.)
5. **Boundary-hugging functional tests.** Legitimate inputs that look like the attack (same characters, same feature,
   trailing slash, empty/None, legacy unbound data) must keep working, so "reject everything suspicious" fails.
6. **Behavioural report, no localization, no scope.** Describe what a user observes ("an IPv6 client passed our IPv4
   allowlist"), never the function, class, file or the root cause wording that points at the line to change - and
   never how far the bug reaches ("each provider we tried", "on every route"): all 4 evaluated reports with such a
   phrase were solved on attempt 1. Stating the cause is fatal only for a one-place fix; hono stated it and still won.
7. **Parallel implementation.** The project has a second module that re-implements the same feature (a second
   renderer, a second parser, a legacy and a new API). The report describes the behaviour once; the fix must land in
   both. Evidence: hono GHSA-hxh3 (first ACCEPTED task) - in 4 of 6 attempts the second `jsx/dom/server` renderer was
   left unfixed (DeepSeek read it every time but argued a top-level string is "trusted HTML"; MiMo twice never looked);
   the other 2 fixed it for a bare string only and missed a nested-array root. Details: data/knowledge/failure_analyses/.
8. **Input-shape variants (RETIRED - do not use as a difficulty technique).** In 35 of 40 tagged tasks, break rate at
   the 15% baseline: models catch spelling, case, encoding and shape variants of one route. A second public API or
   lower-level constructor that is a REAL separate place is technique 1 or 7, not this one.
9. **A "must keep working" clause that argues against the fix.** DeepSeek uses such a clause (or an existing test that
   passes either way) as permission to leave a sink open; MiMo over-hardens and breaks the legitimate path - test the
   legitimate behaviour in every supported composition order (undici GHSA-vp8m).
10. **Prefer big fixes (RETIRED as a difficulty lever).** Width does not separate hard from easy: 10-21-file fixes
   were solved on attempt 1 (9router changed 1 of 12 fix files and scored 1.0). Tiny local fixes (<= 3 files, <= 35
   lines) are still unusable, so width is a floor, not a lever.
11. **A compatibility contract pinned by an existing repo test.** Pick fixes that add an option or a check next to
   an existing public interface that the project's own tests pin (the exact keys a plugin receives, an output format,
   a default). The obvious fix changes that interface; a careful fix keeps it. Evidence: apprise GHSA-856c
   (ACCEPTED) - in 6 of 6 attempts both models added the new `redirect` key to every plugin's parsed-URL dict "like
   `verify`", saw the repo test `len(meta) == 8` fail, and edited the test instead of their fix; the grader restores
   repo tests, so all 6 scored 0.99. The upstream fix kept the key out unless set. Make sure the existing test is in
   the enforced pass->pass set and the report does not tell the agent to change that interface.
12. **Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22).** A mechanism that never had the
   protection, so its absence reads as design ("unsupported combination, not a boundary"). jackson: the any-setter
   route has no view code at all. Test it through its own entry point.
13. **Producer off the check's path (M6, 5 of 17).** A schema, serializer, loader or config resolver feeds the check
   through a path the check never calls; the model follows calls INTO the check and never asks where its data comes
   from. MCP SDK 6qxp: the schema strips the issuer on reload (DeepSeek missed it 3/3).
14. **Wrong object (M10).** The check authorises a neighbouring or proxy object, or trusts an attacker-chosen identity
   field (seaweedfs: authorises against the ARN's account field; django-cms: parent from POST while the check reads GET).
15. **Merged / defaults route (M5).** The restricted value arrives through defaults, merge, inheritance, a patch or
   stored config; the model treats the report's example fields as the whole set (protobuf.js: inherited options).

## Cover every place the real fix protects (measured)
- In 15 of 27 solved tasks the agent passed while changing FEWER source files than the reference fix: the hidden tests
  did not exercise every place the fix protects, so a partial repair scored 1.0. Before writing tests, list each source
  file / code path the reference fix hardens and give each one at least one security test reached from a real entry
  point. A repair that skips any of those places must fail. (Live numbers: data/knowledge/solved_profile.md.)

## How the pipeline proves the tests are good (your check patches)
- **shallow**: blocks only the reported trigger. At least one security test must still fail on it (technique 1/4).
- **removal**: disables or over-restricts the feature. At least one functional test must fail on it (technique 5).
- **alternative**: a correct fix of a different design. Every test must pass on it (tests are implementation-agnostic).
- **coverage (leave-one-file-out)**: the reference fix is run WITHOUT its change to each file you list in
  `fix_places` (metadata). At least one test must fail every time; otherwise an agent that skips that file solves
  the task and it is sent back. List only files whose change closes part of the vulnerability.
- These are executed in the real environment. A wrong outcome sends the task back with the failing test names.

## Fairness rules (never break these to make a task harder)
- Every hidden test is passed by the reference fix and follows from the report plus a careful reading of the code.
- Tests observe only what a caller can observe at the entry point; never internal state or names the fix adds.
- No timing races, no network, no randomness.
- **Never test a number the report does not state.** The reference fix's internal limits (max length 64, a 1,000,000
  cap, a depth limit) are ONE design; another correct fix may pick another value. (Most common rejection so far:
  pypdf, source-map-js.) For resource-exhaustion bugs: keep the legitimate input small and the attack input orders of
  magnitude larger (e.g. 1x vs 1000x), and assert only that the attack is refused or finishes quickly and bounded -
  never at which exact size it starts being refused. If a boundary matters, the report must state it.
- **Variants must share the reported root cause.** Another bug in the same area (a different slow path, a different
  missing check) is a different task, not a variant (rejected: source-map-js deep nesting, typespec output files).
- **Never map every exception to "blocked".** Catch only the project's own rejection (UnauthorizedException, a 4xx,
  its ValidationError); let any other error fail the test. A catch-all hid a broken fake request in sync-in (the
  guard crashed on a missing `request.url`), so legitimate-use tests failed for no visible reason - and the same
  catch-all lets a security test "pass" when the code under test never ran.
- **"Must keep working" means it works today.** Every functional test must pass on the vulnerable code; never describe
  as legitimate a behaviour the project never had (rejected: undici allow-list caching).

## Answer-key hygiene (the agent must use its own knowledge)
- The agent sees only the report and the repo at the vulnerable commit: no hidden tests, no fix, no git history of
  the fix, no network, no advisory text. Never put fix code, upstream regression tests or exploit inputs into the repo
  or the report. Fixes committed after the models' release dates keep the answer out of their training data.


# Which task types each evaluated agent could not repair completely (measured results)
## Model failure map (deterministic, rebuilt after every evaluation)
Task type = vulnerability family; fix breadth (files / dirs / lines). Timeouts are not failures.
### DeepSeek
- FAILED on (5): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) - partial fix: closed 5 of 6 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: schema_roundtrip_keeps_binding | information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | path / file handling; wide multi-layer fix (10 files / 3 dirs / 236 lines) - partial fix: closed 4 of 5 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: toolbox_symlink_escape | auth / session / credentials; local fix (1 files / 1 dir / 33 lines) - partial fix: closed 6 of 7 attack variants in its run and stopped on its own (it thought it was done); left open every time: exp_at_epoch_boundary
- Timed out on (0): none
- Solved (35), by vulnerability family: resource exhaustion (DoS) x7, auth / session / credentials x7, other x6, path / file handling x3, parsing / type confusion x3, injection (code / command / markup) x2, injection (code / command / markup) + information exposure x1, parsing / type confusion + SSRF / redirect x1, information exposure x1, auth / session / credentials + injection (code / command / markup) x1, auth / session / credentials + path / file handling x1, deserialization / prototype pollution x1, auth / session / credentials + path / file handling + information exposure x1
### MiMo
- FAILED on (3): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | auth / session / credentials; wide multi-layer fix (10 files / 5 dirs / 120 lines) - closed the hole but broke legitimate behaviour (storage_with_custom_lookup_same_host) in its run and stopped on its own (it thought it was done)
- Timed out on (2): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) | auth / session / credentials; wide multi-layer fix (5 files / 4 dirs / 111 lines)
- Solved (7), by vulnerability family: auth / session / credentials x2, parsing / type confusion x2, injection (code / command / markup) x1, path / file handling x1, auth / session / credentials + path / file handling + information exposure x1
### Broke BOTH (replicate this shape): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines)


# Which techniques have broken the evaluated agents so far (measured)
## Technique scoreboard (measured, rebuilt after every evaluation)
How often each curated technique was used in an evaluated task, and the outcome. A technique that keeps appearing in tasks DeepSeek solves on attempt 1 is not enough on its own: combine it with ones that broke a model. Counts are per task.

Baseline: 6 of 40 tagged tasks broke at least one model (15%). A technique is only informative when its break rate differs from that baseline.

| # | Technique | Tasks | Broke both | Broke only DeepSeek | Broke only MiMo | Solved | Read |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed sibling path | 20 | 2 | 2 | 1 | 15 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt, undici) |
| 2 | Already-protected-looking code | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 3 | Fix across a layer boundary | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 4 | One test per fix place | 40 | 2 | 3 | 1 | 34 | BASELINE (in 40/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 5 | Boundary-hugging functional tests | 38 | 2 | 3 | 1 | 32 | BASELINE (in 38/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 6 | Behavioural report, no localization, no scope | 39 | 2 | 3 | 1 | 33 | BASELINE (in 39/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 7 | Parallel implementation | 9 | 2 | 0 | 1 | 6 | USE: 33% break rate vs 15% baseline (apprise, hono, undici) |
| 8 | Input-shape variants (RETIRED - do not use as a difficulty technique) | 35 | 2 | 2 | 1 | 30 | BASELINE (in 35/40 tasks): necessary, not sufficient (apprise, hono, nltk, fast-jwt, undici) |
| 9 | A "must keep working" clause that argues against the fix | 16 | 2 | 2 | 0 | 12 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt) |
| 10 | Prefer big fixes (RETIRED as a difficulty lever) | 2 | 1 | 0 | 0 | 1 | too few uses to judge (but broke both models) (apprise) |
| 11 | A compatibility contract pinned by an existing repo test | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 12 | Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 13 | Producer off the check's path (M6, 5 of 17) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 14 | Wrong object (M10) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 15 | Merged / defaults route (M5) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |

_0 evaluated task(s) have no technique record._


# Task shapes the evaluated agents SOLVED (avoid repeating them; measured)
## Solved-task profile (deterministic, rebuilt after every evaluation)
37 evaluated tasks were solved by at least one model; 35 on the FIRST attempt. Median solve time 13 min. These are the shapes to avoid or to combine with the techniques that broke a model (see the technique scoreboard).
- Median reference-fix size of solved tasks: 6 source files; median number of security tests: 6.
- Solved by vulnerability family: auth / session / credentials x11, resource exhaustion (DoS) x7, path / file handling x6, other x6, injection (code / command / markup) x4, parsing / type confusion x4, information exposure x3, SSRF / redirect x1, deserialization / prototype pollution x1
- In 8 of 37 solves the agent changed every source file of the reference fix: the report led it to all affected places.

### Why solved tasks were too easy (measured; fix the most common first)
- **coverage gap** in 24 of 37 solved tasks -> list every place the reference fix hardens and reach EACH one from its own security test - a repair that skips one place must fail.
- **no hidden path** in 15 of 37 solved tasks -> put part of the root cause in a REAL place the report never leads to - a second implementation, a producer feeding the check, a defaults/merge route - and reach it with its own test (techniques 1, 2, 3, 7, 12-15).
- **small fix** in 12 of 37 solved tasks -> a one-place fix is solved whatever the report says; skip it unless the code has a real second place the fix must also reach (fix width alone does not help: 10-21-file fixes were solved on attempt 1).
- **few security tests** in 9 of 37 solved tasks -> write one security test per fix place, each through its own entry point (spelling and encoding variants of one input do not count: models always catch them).
- **report points at the code** in 7 of 37 solved tasks -> never name the file, function, option or parameter the fix changes, and never state how far the bug reaches ('every provider', 'on every route').

| Task | Family | Fix | Security tests | Techniques used | Solved by | Attempt | Minutes | Why it passed |
|---|---|---|---|---|---|---|---|---|
| 9router | auth / session / credentials | 13 files / 10 dirs / 257 lines | 6 | 1, 4, 5, 6, 8, 9 | DeepSeek | 1 | 2 | coverage gap (1/12 fix files changed) |
| @hono/oauth-providers | auth / session / credentials | 7 files / 7 dirs / 54 lines | 6 | 1, 4, 5, 6, 8, 10 | DeepSeek | 1 | 3 | - |
| msgpack5 | resource exhaustion (DoS) | 2 files / 2 dirs / 40 lines | 7 | 1, 4, 5, 6, 8 | DeepSeek | 1 | 4 | small fix |
| nltk | other | 6 files / 2 dirs / 163 lines | 5 | 4, 5, 6, 8 | DeepSeek | 1 | 4 | coverage gap (1/7 fix files changed); report points at the code: grammar; no hidden path; few security tests |
| ip-address | parsing / type confusion | 3 files / 1 dir / 25 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 5 | small fix; report points at the code: Address4, Address6; no hidden path |
| @xmldom/xmldom | other | 3 files / 2 dirs / 37 lines | 10 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 6 | small fix |
| vibe-trading-ai | auth / session / credentials + path / file handling + information exposure | 17 files / 5 dirs / 618 lines | 6 | 3, 4, 5, 6, 8 | DeepSeek | 1 | 6 | coverage gap (4/23 fix files changed); report points at the code: Settings, service |
| pyload-ng | auth / session / credentials | 2 files / 2 dirs / 9 lines | 4 | 4, 5, 6 | DeepSeek | 1 | 8 | coverage gap (1/2 fix files changed); small fix; no hidden path; few security tests |
| pyload-ng | auth / session / credentials | 4 files / 2 dirs / 58 lines | 7 | 4, 5, 6, 8 | DeepSeek | 1 | 8 | coverage gap (3/5 fix files changed); no hidden path |
| n8n | injection (code / command / markup) | 9 files / 7 dirs / 343 lines | 6 | 1, 4, 5, 8 | DeepSeek | 1 | 8 | coverage gap (5/9 fix files changed); report points at the code: execute |
| @vitest/browser | auth / session / credentials + path / file handling | 8 files / 4 dirs / 104 lines | 4 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 9 | coverage gap (6/8 fix files changed); report points at the code: upload; few security tests |
| pymongo | other | 3 files / 3 dirs / 74 lines | 6 | 4, 5, 6, 7, 8 | DeepSeek | 1 | 10 | small fix |
| adm-zip | parsing / type confusion | 2 files / 2 dirs / 11 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 11 | small fix; no hidden path |
| react-router | other | 8 files / 7 dirs / 113 lines | 5 | 1, 3, 4, 5, 6, 7, 8 | DeepSeek | 1 | 12 | coverage gap (1/6 fix files changed); report points at the code: server; few security tests |
| pyload-ng | auth / session / credentials | 5 files / 4 dirs / 111 lines | 7 | 4, 5, 6 | DeepSeek | 1 | 12 | no hidden path |
| datamodel-code-generator | path / file handling | 1 files / 1 dir / 31 lines | 6 | 4, 5, 6, 9 | DeepSeek | 1 | 13 | small fix; no hidden path |
| @sync-in/server | other | 21 files / 8 dirs / 224 lines | 6 | 1, 4, 5, 6, 7, 8, 9 | DeepSeek | 1 | 13 | coverage gap (12/20 fix files changed) |
| hono | path / file handling | fix size unknown | 4 | 1, 4, 5, 6, 8, 9 | DeepSe


# Why the evaluated agents failed real tasks (curated from their trajectories - design for these)
## GHSA-856c-92hv-3vxx: Verdict: ACCEPTED. Both models failed every run. DeepSeek scored 0.99 on all three attempts and MiMo scored 0.99 on all three. In all six attempts every hidden test passed, including all 16 security and functional tests, so the fix itself worked. Each attempt failed on the same pre-existing test, `tests/test_decorator_notify.py::test_notify_multi_instance_decoration`, which asserts `len(meta) == 8`. The new `redirect` option was copied exactly from how `verify=` is handled, so a `redirect` key now appeared in every parsed-URL result. The agents saw this test fail and changed the expected count to 9. Test edits were restored before grading, so the change did nothing and the test still failed. All six attempts treated a failing existing test as something to update, not as a limit on their design. None of them changed `apprise/asset.py`, which the reference fix did change. That suggests the reference stores the default somewhere other than an always-present `parse_url` key, though the evidence doesn't show exactly how.
#### Weakness profile
- **DeepSeek:**
  - **Strengths:** it explores thoroughly and finds every HTTP call site. It does careful mechanical checks of its own patch, such as AST scans of every `allow_redirects` use.
  - **Weakness:** when an existing test breaks, it assumes the test is out of date, not that its design choice is wrong. It openly concludes the edits are "harmless" because hidden tests "will add new tests".
  - **How it verifies and stops:** it treats "the full suite passes after I edited the tests" as done. It never checks whether the new option could be added without changing what existing public output looks like.
- **MiMo:**
  - **Weakness:** the same habit of editing existing tests, but even stronger. It changes or extends four to six existing test files per attempt, and in attempt 3 it adds assertions that lock in its own side effects.
  - **Less precise coverage:** it touched a TCP-only plugin (attempt 1) and skipped eight HTTP plugins (attempt 2).
  - **Why it stops:** its own tests pass, and it takes that as proof of correctness.
- **Both:** they took "behave exactly like `verify=`" as an order to copy everything about it, including always adding a key to the parsed-URL results. Neither considered that existing callers and tests might depend on that results dict having a fixed size.
#### Task-design lessons
- **Ask for a feature that mirrors an existing option, while existing tests fix the shape of shared output.** Phrase it as "behave exactly like X", while an existing test pins the number of keys, the field list or the serialised form of a shared structure. Agents copy the template wholesale, change the shared structure, then "fix" the pinning test.
- **Keep breakage-detecting tests in files the agent will naturally edit.** Enforce existing tests and restore any test edits before grading. Put the fragile assertion in a test that fails noticeably during the agent's own full-suite run. Both models reliably edit such tests and wrongly believe test changes are "harmless".
- **Make the reference fix put new state somewhere unexpected.** Here that was a central config or defaults object (`asset.py`) instead of the obvious parser. A naive copy of the existing option then visibly breaks backward compatibility, while the reference route does not.
- **Grade the security behaviour on every call site, not a sample.** Use a fan-out change across many near-identical files and run hidden tests over the full set or a random sample of call sites. MiMo attempt 2 skipped eight plugins, and the hidden tests, which only covered json/form/xml/apprise_api/config/attachment, didn't notice.
- **State backward compatibility outright, but leave the danger implicit.** Write "existing behaviour stays as it is today" and nothing more. Agents read that as runtime behaviour only. They don't treat existing API or introspection output, such as a parsed-URL dict, as behaviour too, and that gap is what both models fell into.

## GHSA-hxh3-vqpv-xpqv: ACCEPTED - both models failed all 3 attempts (DeepSeek 0.83/0.83/0.94, MiMo 0.89/0.94/0.89, Claude Code agent), every run stopped on its own (no timeout). All 6 fixed the three wrappers the report names (Suspense, ErrorBoundary, Context.Provider) and all 6 left `renderToString([unsafe, [unsafe]])` unescaped.
#### Weakness profile
- Shared: both treat the report's examples as the complete list of sinks, and fix only the input shape they
  reproduced (a bare string) even when the same parameter accepts arrays, nested arrays and promises.
- DeepSeek: over-reasons about intent - finds the sink, then uses a "keep legitimate behaviour" clause or an existing
  passing test as permission to leave it vulnerable.
- MiMo: under-explores and asserts unverified facts ("that API doesn't exist") instead of searching.
#### Task-design lessons
- Put a **second entry point in a sibling module whose path sounds out of scope** (here `dom/` reads as "client") and
  describe it only vaguely ("a string handed to the renderer directly").
- Add a **"must keep working" clause that plausibly argues against the fix** ("a bare string must still be
  renderable"), backed by an existing test that passes either way (`'Hono'` has nothing to escape).
- **Test input-shape variants at each sink** (array, nested array, promise, number), not only each sink.
- Make **two entry points share the bug but need separate fixes**; agents fix them unevenly and claim full coverage.
- List some sinks "for example" and test more than you list: every agent stopped once the listed items were covered.

## GHSA-6qxp-vccf-f47h: DeepSeek failed 3/3 (0.92 each, Claude Code agent), always closing 5 of 6 attack paths; MiMo only timed out (terminus-2, 2 h), so the task is rejected (a timeout is not a failure).
#### Weakness profile
- DeepSeek traces call graphs well but misses state that crosses a serialization boundary (save -> store -> parse).
- It trusts in-code comments and "intentional" design notes, and reads "must keep working" hints as constraints.
- It stops as soon as self-written tests (which cover only what it already believes) pass.
#### Task-design lessons
- Put one variant on a **data round-trip** (serialize -> persist -> parse through the project's own schema/model
  layer) that the report does not name; the call-path fix then leaves exactly that variant open.
- Let the vulnerable code contain a plausible "intentional" comment or an already-protected entry point near the bug.
- Mention the round-trip only as legitimate behaviour that must keep working; never as an attack path.

## GHSA-p4rw-rvv2-7xwr: DeepSeek failed all 3 attempts (0.93 each, always the toolbox symlink escape left open); MiMo failed 2 (0.87, toolbox + MTE left open) and solved 1. Rejected (MiMo solved). No timeouts; every run stopped on its own.
#### Weakness profile
- DeepSeek: entry-point blindness - treats "reachable through the main class" as the whole attack surface and



# Lessons from previous runs (auto-generated from real DeepSeek/MiMo results - follow them)
## Breaks BOTH models (replicate)
- **hxh3 · hono · CWE-79 · 6 files/3 dirs/156 lines** and **856c · apprise · CWE-200/601** are the accepted tasks (n=2). hono: both models scored 0.83–0.94 and stopped on their own in 3/3 runs, leaving the second `jsx/dom/server` renderer or the nested-array root open every time - places the report never mentioned. apprise: both broke a plugin interface the repo's own test pins (over-correction, 6/6). Check `stream > Should call onAbort` for flakiness before reusing hono.
- **Combine in one task:**
  1. A REAL place the report never leads to - a second implementation, a lower-level API, a round-trip - that the obvious choke point misses. This beat DeepSeek (n=3). Spelling/encoding/shape variants of the same route do not count: they are always caught.
  2. One security test per fix place, each through its own entry point, so a fix that skips one place still fails.
  3. A falsy or boundary variant (`0`, `""`, `[]`). This beat DeepSeek (tentative, n=1: x937).
  4. A test that existing behaviour still works across a composition or ordering boundary. This beat MiMo (tentative, n=1: vp8m).
  5. A path that is already safe, as a decoy. This beat MiMo (tentative, n=1: jq7h).
  6. Fast test suites. A MiMo timeout counts as "too slow", not as a failure (6qxp, vp8m).

## Breaks only DeepSeek (MiMo solves)
- **Stops one variant short (n=4: 6qxp, p4rw, hxh3, x937; scores 0.92–0.95).** It patches the first layer it finds, then declares itself done.
  - **p4rw · nltk · CWE-22/59.** It put the check in `CorpusReader.abspath` and missed the bare-string entry points `StandardFormat.open`, `XMLCorpusView` and `load_ace_file`. MiMo fixed the shared `FileSystemPathPointer`.
  - **x937 · fast-jwt · CWE-613 · 1 file/33 lines.** It fixed the `hasIat` gate the report described, but kept the cache rule that `0` means "no bound". The `exp: 0` case stayed open (13/14 tests passed). MiMo checked whether the claim was present, not whether it was truthy, and compared cached against uncached results.
  - **6qxp.** It saw that the binding is lost on a schema round-trip and stopped anyway.
- **Hiding file names is not enough.** DeepSeek named the fix file in 0 of 38 recall probes, yet solved 21 tasks: the
  reports hid the files but stated the scope, the tainted parameters or the root cause of a one-place fix. What failed
  DeepSeek was a real place the report never led to (hono's second renderer, 6qxp's schema round-trip).

## Breaks only MiMo (DeepSeek solves)
- **vp8m · undici · CWE-346 (tentative).** Security tests reached 1.0, but reuse in `compose(cache(), dns())` broke. MiMo restored the hostname only on the response side, so the lookup key and the store key diverged.
- **jq7h · pyload · CWE-613 (tentative).** MiMo spent its budget on the webui path, which was already correct, and never edited REST.
- **When MiMo succeeds:** it solves tasks where one shared layer covers every variant (p4rw 1/3, x937). It has 3 counted failures.
- **Evidence on MiMo is thin.** Its p90 step time is about 400 s vs about 40 s for DeepSeek. It was ungraded in 13 of 14 stage-5 rows because a DeepSeek solve ends the run.

## Solved by both (avoid)
- **p634, j6r3:** the report gave the root cause, a repro and the API names, and the fix was one local check.
- **pqg4, x33g:** both models named the fix location.
- **DeepSeek solved on the first try, MiMo ungraded (n=21; 35–223 steps, 4–64 min):** j22f, v247, 24ch, 68w4, 9q47, 77xj, 5jq2, 3wxw, hqr4, hmq2, 2q42, qf28, 8fvv, 8xx6, mcm9, w3v8, q2xc, c7q8, gqvv, f65p and PYSEC-3869.
  - Each had one choke point that every variant passed through.
  - Wide fixes didn't help: 7 of them were solved, including qf28 (16 files) and w3v8 (289 lines).

## Task-quality pitfalls (rubric / oracle failures)
- **Run every test on the vulnerable code (n=6).** Security tests must fail there and functional tests must pass.
  - 8r5x crashed before the injection ran.
  - In r4xh and q238, security tests already passed (GEOS rejected nested Multi* at depth 5–6).
  - mcm9 and vp8m had functional tests that required new behaviour.
  - PYSEC-3869 used the mixed rule `S -> S 'a'`, which CNF conversion rejects on both versions.
- **Oracle fails its own tests (n=11):** x6jw, p634, jggr, 68fv, hmq2, 2q42, hqr4, r4xh, 376h, 2q76 and hwr6.
  - If every functional test scores 0.0, the harness or fixture is broken. Regenerating fixed hmq2, 2q42 and hqr4.
  - Drop existing tests that assert the vulnerable behaviour (tentative, n=2: qf28, c4c3).
- **Tests accept only one fix shape (n=9):**
  - 68w4, 9q47, jq7h, qf28.
  - 2q76: required field-level `access` and called functions with a made-up `req`.
  - x78j: rejected raise, `SystemExit` and drop fixes.
  - p63j: aliased `@vitest/browser` to `utils.ts` and used fake contexts.
  - PYSEC-3819: mocked only the module-level `requests.get`.
  - 5vf6: a minimal constructor config crashed fixes that read `flagResolver`.

  Accept reject, raise, drop and sanitize fixes. Test through the public HTTP, CLI or RPC entry point. Mock at the transport layer and import through the package entry.
- **Undisclosed limits or semantics (n=5):** 5jq2 (a cutoff of 64), 68fv (hidden cap), 2q42 (sanitize and still emit), w3v8 (25 s vs the repo's 60 s) and x78j (`splitlines()` instead of cmd.exe rules). State limits in the report or use ≥100× margins, and model the real sink.
- **Weak tests (n=5):** x937, 6qxp, qf28, r4xh and 2q76 (deny-all passed). Assert the output content and make over-blocking fail. Count operations instead of timing them (tentative, n=2).
- **No network in tests (tentative, n=1: 5vf6).** The test resolved a real host's DNS, and the oracle passed only through a hidden `NODE_ENV=test` fallback.
- **Fix visible to the model (n=4):** readable in site-packages or node_modules (8xx6, q2xc, f65p), or already in the vulnerable tree (337j). Uninstall released copies.
- **Bad existing-test files (n=4):** helper, manual and DB-integration files. Exclude them.
- **Infrastructure; retry before rejecting:**
  - no verdict (n=9)
  - host Docker I/O error (n=4)
  - "no usable existing tests" (n=4; f65p passed on retry)
  - `pip install -e .` failed (n=3)
  - environment start timeout, stage-5 incomplete attempts, npm install failed (n=2 each)
- **Report names the code (n=3)**, and **safeguard blocks (n=9)**; Handlebars, q238 and 2q76 were retired.

## Selection hints
- **Prefer:** fixes where a tempting high-level choke point misses a real second place - a second implementation, a lower-level API, a producer feeding the check (n=3; 6–10 files, 120–236 lines). At screening, ask whether one function sees every variant. If it does, skip.
- **Also prefer (tentative):** checks on falsy-sensitive fields (timestamps, counts, empty values), and these CWEs:
  - CWE-79
  - CWE-345/522
  - CWE-613 (broke each model once)
  - CWE-22/59, only if bare-path entries bypass the reader layer
- **Skip:**
  - Fixes of ≤4 files and ≤60 lines (0 usable of 14).
  - DoS CWE-400/407/409/674/1284/1333 (0 usable).
  - CWE-22/73 fixed in one path builder (n=3).
  - CWE-91, URI parsers and SSRF fixes that need DNS (tentative).
  - Code generators.
  - Oracle patches over 80k characters (n=3).
  - Monorepos: payload (5 failures), pydantic-ai, vllm, Flowise, reactpress, mermaid and vitest.
  - PyPI repos where `pip install -e .` fails.
- **pyload:** use only with the real app's test client.
- **Recall:** reject if both models name the fix (n=2). Otherwise recall doesn't predict the outcome.


# Split generation (this request)
Return ONLY the `<instruction_md>`, `<task_metadata_json>` and `<check_patches_json>` blocks. Do NOT write the
<hidden_tests_py> block; it is requested in a separate step. Keep the check patches minimal (only the edits that
demonstrate shallow / removal / alternative behaviour).

