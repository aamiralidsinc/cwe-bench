package vtesting

import (
	"testing"

	"github.com/prebid/prebid-server/v4/adapters"
	"github.com/prebid/prebid-server/v4/adapters/acuityads"
	"github.com/prebid/prebid-server/v4/adapters/adhese"
	"github.com/prebid/prebid-server/v4/adapters/between"
	"github.com/prebid/prebid-server/v4/adapters/bidmachine"
	"github.com/prebid/prebid-server/v4/adapters/clydo"
	"github.com/prebid/prebid-server/v4/adapters/kayzen"
	"github.com/prebid/prebid-server/v4/adapters/rediads"
	"github.com/prebid/prebid-server/v4/adapters/relevantdigital"
	"github.com/prebid/prebid-server/v4/adapters/rtbstack"
	"github.com/prebid/prebid-server/v4/adapters/silvermob"
	"github.com/prebid/prebid-server/v4/adapters/smartyads"
	"github.com/prebid/prebid-server/v4/adapters/tappx"
	"github.com/prebid/prebid-server/v4/adapters/tradplus"
	"github.com/prebid/prebid-server/v4/adapters/trafficgate"
	"github.com/prebid/prebid-server/v4/adapters/zeroclickfraud"
	"github.com/prebid/prebid-server/v4/config"
)

func fAcuity(c config.Adapter) (adapters.Bidder, error) {
	return acuityads.Builder("acuityads", c, config.Server{})
}
func fAdhese(c config.Adapter) (adapters.Bidder, error) {
	return adhese.Builder("adhese", c, config.Server{})
}
func fBetween(c config.Adapter) (adapters.Bidder, error) {
	return between.Builder("between", c, config.Server{})
}
func fBidmachine(c config.Adapter) (adapters.Bidder, error) {
	return bidmachine.Builder("bidmachine", c, config.Server{})
}
func fClydo(c config.Adapter) (adapters.Bidder, error) {
	return clydo.Builder("clydo", c, config.Server{})
}
func fKayzen(c config.Adapter) (adapters.Bidder, error) {
	return kayzen.Builder("kayzen", c, config.Server{})
}
func fRediads(c config.Adapter) (adapters.Bidder, error) {
	return rediads.Builder("rediads", c, config.Server{})
}
func fRelevant(c config.Adapter) (adapters.Bidder, error) {
	return relevantdigital.Builder("relevantdigital", c, config.Server{})
}
func fRtbstack(c config.Adapter) (adapters.Bidder, error) {
	return rtbstack.Builder("rtbstack", c, config.Server{})
}
func fSilvermob(c config.Adapter) (adapters.Bidder, error) {
	return silvermob.Builder("silvermob", c, config.Server{})
}
func fSmartyads(c config.Adapter) (adapters.Bidder, error) {
	return smartyads.Builder("smartyads", c, config.Server{})
}
func fTappx(c config.Adapter) (adapters.Bidder, error) {
	return tappx.Builder("tappx", c, config.Server{})
}
func fTradplus(c config.Adapter) (adapters.Bidder, error) {
	return tradplus.Builder("tradplus", c, config.Server{})
}
func fTrafficgate(c config.Adapter) (adapters.Bidder, error) {
	return trafficgate.Builder("trafficgate", c, config.Server{})
}
func fZeroclick(c config.Adapter) (adapters.Bidder, error) {
	return zeroclickfraud.Builder("zeroclickfraud", c, config.Server{})
}

// Every case below supplies a value that, on the vulnerable tree, rewrites the
// destination authority of the outbound bid request. A refused value must yield
// a client-visible error and no outbound request at all.
func secCase(t *testing.T, bidder string, factory Factory, params map[string]interface{}) {
	t.Helper()
	reqs, errs := Requests(t, bidder, factory, params)
	Refused(t, reqs, errs)
}

func TestSecAcuityAds(t *testing.T) {
	base := map[string]interface{}{"host": "ep1", "accountid": "hash"}
	for name, value := range map[string]string{
		"path":     "evil.example/path",
		"query":    "evil.example?x=1",
		"fragment": "evil.example#frag",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "acuityads", fAcuity, copyParams(base, map[string]interface{}{"host": value}))
		})
	}
}

func TestSecAdhese(t *testing.T) {
	base := map[string]interface{}{"account": "demo", "location": "loc1", "format": "for1"}
	for name, value := range map[string]string{
		"path":  "evil.example/path",
		"query": "evil.example?x=1",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "adhese", fAdhese, copyParams(base, map[string]interface{}{"account": value}))
		})
	}
}

func TestSecBidmachine(t *testing.T) {
	base := map[string]interface{}{"host": "api-eu", "path": "auction/rtb/v2", "seller_id": "1"}
	for name, value := range map[string]string{
		"path":     "evil.example/path",
		"fragment": "evil.example#frag",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "bidmachine", fBidmachine, copyParams(base, map[string]interface{}{"host": value}))
		})
	}
}

func TestSecKayzen(t *testing.T) {
	base := map[string]interface{}{"zone": "dc", "exchange": "ex"}
	for name, value := range map[string]string{
		"path":  "evil.example/path",
		"query": "evil.example?x=1",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "kayzen", fKayzen, copyParams(base, map[string]interface{}{"zone": value}))
		})
	}
}

func TestSecRediads(t *testing.T) {
	base := map[string]interface{}{"account_id": "123", "slot": "12345"}
	for name, value := range map[string]string{
		"path":     "evil.example/path",
		"portpath": "evil.example:8080/path",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "rediads", fRediads, copyParams(base, map[string]interface{}{"endpoint": value}))
		})
	}
}

func TestSecRelevantDigital(t *testing.T) {
	base := map[string]interface{}{"accountId": "acct", "placementId": "placement"}
	for name, value := range map[string]string{
		"path":          "evil.example/path",
		"vendor-suffix": "evil.example/path.relevant-digital.com",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "relevantdigital", fRelevant, copyParams(base, map[string]interface{}{"pbsHost": value}))
		})
	}
}

func TestSecSmartyAds(t *testing.T) {
	base := map[string]interface{}{"host": "ep1", "sourceid": "partner", "accountid": "hash"}
	for name, value := range map[string]string{
		"path":  "evil.example/path",
		"query": "evil.example?x=1",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "smartyads", fSmartyads, copyParams(base, map[string]interface{}{"host": value}))
		})
	}
}

func TestSecTradPlus(t *testing.T) {
	base := map[string]interface{}{"accountId": "11233"}
	for name, value := range map[string]string{
		"path":     "evil.example/path",
		"fragment": "evil.example#frag",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "tradplus", fTradplus, copyParams(base, map[string]interface{}{"zoneId": value}))
		})
	}
}

func TestSecTrafficGate(t *testing.T) {
	base := map[string]interface{}{"placementId": "11"}
	for name, value := range map[string]string{
		"path":  "evil.example/path",
		"query": "evil.example?x=1",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "trafficgate", fTrafficgate, copyParams(base, map[string]interface{}{"host": value}))
		})
	}
}

func TestSecZeroClickFraud(t *testing.T) {
	base := map[string]interface{}{"sourceId": 1}
	for name, value := range map[string]string{
		"path":     "evil.example/path",
		"query":    "evil.example?x=1",
		"fragment": "evil.example#frag",
		"userinfo": "user@evil.example",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "zeroclickfraud", fZeroclick, copyParams(base, map[string]interface{}{"host": value}))
		})
	}
}

func TestSecBetween(t *testing.T) {
	base := map[string]interface{}{"publisher_id": "pub"}
	for name, value := range map[string]string{
		"path":  "evil.example/path",
		"query": "evil.example?x=1",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "between", fBetween, copyParams(base, map[string]interface{}{"host": value}))
		})
	}
}

func TestSecClydo(t *testing.T) {
	base := map[string]interface{}{"partnerId": "partner"}
	for name, value := range map[string]string{
		"path":  "evil.example/path",
		"query": "evil.example?x=1",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "clydo", fClydo, copyParams(base, map[string]interface{}{"region": value}))
		})
	}
}

func TestSecSilverMob(t *testing.T) {
	base := map[string]interface{}{"zoneid": "zone"}
	for name, value := range map[string]string{
		"path": "evil.example/path.silvermob.com",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "silvermob", fSilvermob, copyParams(base, map[string]interface{}{"host": value}))
		})
	}
}

func TestSecRTBStack(t *testing.T) {
	base := map[string]interface{}{"tagId": "tag"}
	for name, route := range map[string]string{
		"query-region": "https://example.com/pbs?ssp=s&endpoint=e&client=c&region=evil.example/path",
	} {
		t.Run(name, func(t *testing.T) {
			secCase(t, "rtbstack", fRtbstack, copyParams(base, map[string]interface{}{"route": route}))
		})
	}
}
