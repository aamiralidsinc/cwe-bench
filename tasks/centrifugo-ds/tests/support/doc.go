// Package vtesting holds the hidden behavioural tests for the centrifugo-ds task.
//
// Every test drives product code directly: the proxy handlers the server's client
// handler calls, the client connect handler itself, and the proxy builders they use.
// HTTP proxy backends are in-process httptest servers; gRPC proxy backends are
// in-process bufconn servers. Nothing here reaches the network or starts Centrifugo.
package vtesting
