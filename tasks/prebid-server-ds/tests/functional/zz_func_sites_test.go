package vtesting

import (
	"strings"
	"testing"
)

// Legitimate values must keep producing exactly the destination they produce today,
// including values the server normalises before use and optional values that are empty.
func funcCase(t *testing.T, bidder string, factory Factory, params map[string]interface{}, want string) {
	t.Helper()
	reqs, errs := Requests(t, bidder, factory, params)
	WantsUri(t, reqs, errs, want)
}

func TestFuncAcuityAds(t *testing.T) {
	t.Run("label", func(t *testing.T) {
		funcCase(t, "acuityads", fAcuity,
			map[string]interface{}{"host": "ep1", "accountid": "hash"},
			"http://ep1.admanmedia.com/bid?token=hash")
	})
	t.Run("mixed-case-fqdn", func(t *testing.T) {
		funcCase(t, "acuityads", fAcuity,
			map[string]interface{}{"host": "Host.Example.com", "accountid": "hash"},
			"http://Host.Example.com.admanmedia.com/bid?token=hash")
	})
}

func TestFuncAdhese(t *testing.T) {
	funcCase(t, "adhese", fAdhese,
		map[string]interface{}{"account": "demo", "location": "loc1", "format": "for1"},
		"https://ads-demo.adhese.com/openrtb2")
}

func TestFuncBidmachine(t *testing.T) {
	funcCase(t, "bidmachine", fBidmachine,
		map[string]interface{}{"host": "api-eu", "path": "auction/rtb/v2", "seller_id": "1"},
		"https://api-eu.bidmachine.io/auction/rtb/v2/1")
}

func TestFuncKayzen(t *testing.T) {
	funcCase(t, "kayzen", fKayzen,
		map[string]interface{}{"zone": "dc", "exchange": "ex"},
		"https://bids-dc.bidder.kayzen.io/?exchange=ex")
}

func TestFuncRediads(t *testing.T) {
	t.Run("default-endpoint", func(t *testing.T) {
		funcCase(t, "rediads", fRediads,
			map[string]interface{}{"account_id": "123", "slot": "12345"},
			"https://bidding.rediads.com/openrtb2/auction")
	})
	t.Run("named-endpoint", func(t *testing.T) {
		funcCase(t, "rediads", fRediads,
			map[string]interface{}{"account_id": "123", "endpoint": "custom"},
			"https://custom.rediads.com/openrtb2/auction")
	})
}

func TestFuncRelevantDigital(t *testing.T) {
	base := map[string]interface{}{"accountId": "acct", "placementId": "placement"}
	for name, host := range map[string]string{
		"bare":  "foo",
		"https": "https://foo.relevant-digital.com",
		"http":  "http://foo.relevant-digital.com",
		"fqdn":  "foo.relevant-digital.com",
	} {
		t.Run(name, func(t *testing.T) {
			funcCase(t, "relevantdigital", fRelevant,
				copyParams(base, map[string]interface{}{"pbsHost": host}),
				"https://foo.relevant-digital.com/openrtb2/auction")
		})
	}
}

func TestFuncSmartyAds(t *testing.T) {
	funcCase(t, "smartyads", fSmartyads,
		map[string]interface{}{"host": "ep1", "sourceid": "partner", "accountid": "hash"},
		"http://ep1.smartyads.com/bid?rtb_seat_id=partner&secret_key=hash")
}

func TestFuncTradPlus(t *testing.T) {
	t.Run("empty-zone", func(t *testing.T) {
		funcCase(t, "tradplus", fTradplus,
			map[string]interface{}{"accountId": "11233", "zoneId": ""},
			"https://adx.tradplusad.com/11233/pserver")
	})
	t.Run("absent-zone", func(t *testing.T) {
		funcCase(t, "tradplus", fTradplus,
			map[string]interface{}{"accountId": "11233"},
			"https://adx.tradplusad.com/11233/pserver")
	})
	t.Run("zone", func(t *testing.T) {
		funcCase(t, "tradplus", fTradplus,
			map[string]interface{}{"accountId": "11233", "zoneId": "us"},
			"https://usadx.tradplusad.com/11233/pserver")
	})
}

func TestFuncTrafficGate(t *testing.T) {
	funcCase(t, "trafficgate", fTrafficgate,
		map[string]interface{}{"placementId": "11", "host": "example"},
		"http://example.bc-plugin.com/?c=o&m=rtb")
}

func TestFuncZeroClickFraud(t *testing.T) {
	t.Run("localhost-port", func(t *testing.T) {
		funcCase(t, "zeroclickfraud", fZeroclick,
			map[string]interface{}{"host": "localhost:3000", "sourceId": 1},
			"http://localhost:3000/openrtb2?sid=1")
	})
	t.Run("numeric-port", func(t *testing.T) {
		funcCase(t, "zeroclickfraud", fZeroclick,
			map[string]interface{}{"host": "127.0.0.1:6060", "sourceId": 1},
			"http://127.0.0.1:6060/openrtb2?sid=1")
	})
	t.Run("mixed-case-fqdn", func(t *testing.T) {
		funcCase(t, "zeroclickfraud", fZeroclick,
			map[string]interface{}{"host": "Bid.Example.COM", "sourceId": 1},
			"http://Bid.Example.COM/openrtb2?sid=1")
	})
}

func TestFuncBetween(t *testing.T) {
	funcCase(t, "between", fBetween,
		map[string]interface{}{"host": "lbs-us-east1.ads", "publisher_id": "pub"},
		"http://lbs-us-east1.ads.betweendigital.com/openrtb_bid?sspId=pub")
}

func TestFuncClydo(t *testing.T) {
	t.Run("default-region", func(t *testing.T) {
		funcCase(t, "clydo", fClydo,
			map[string]interface{}{"partnerId": "partner"},
			"http://us.clydo.io/partner")
	})
	t.Run("explicit-region", func(t *testing.T) {
		funcCase(t, "clydo", fClydo,
			map[string]interface{}{"partnerId": "partner", "region": "eu"},
			"http://eu.clydo.io/partner")
	})
}

func TestFuncSilverMob(t *testing.T) {
	for _, host := range []string{"eu", "us", "apac", "global"} {
		t.Run(host, func(t *testing.T) {
			funcCase(t, "silvermob", fSilvermob,
				map[string]interface{}{"host": host, "zoneid": "zone"},
				"http://"+host+".silvermob.com/marketplace/api/dsp/bid/zone")
		})
	}
}

func TestFuncRTBStack(t *testing.T) {
	t.Run("host-label", func(t *testing.T) {
		funcCase(t, "rtbstack", fRtbstack,
			map[string]interface{}{"route": "https://us-adx-admixer.rtb-stack.com/pbs?ssp=s&endpoint=e&client=c", "tagId": "tag"},
			"https://us-adx-admixer.rtb-stack.com/pbs?ssp=s&endpoint=e&client=c")
	})
	t.Run("explicit-region", func(t *testing.T) {
		funcCase(t, "rtbstack", fRtbstack,
			map[string]interface{}{"route": "https://example.com/pbs?ssp=s&endpoint=e&client=c&region=eu", "tagId": "tag"},
			"https://eu-adx-admixer.rtb-stack.com/pbs?ssp=s&endpoint=e&client=c")
	})
}

func TestFuncTappx(t *testing.T) {
	reqs, errs := Requests(t, "tappx", fTappx,
		map[string]interface{}{"tappxkey": "pub-12345-android-9876", "endpoint": "ZZ1INTERNALTEST149147915"})
	if len(errs) != 0 {
		t.Fatalf("unexpected errors: %v", errs)
	}
	if len(reqs) != 1 {
		t.Fatalf("expected 1 outbound request, got %d", len(reqs))
	}
	const want = "http://ssp.api.tappx.com/rtb/v2/ZZ1INTERNALTEST149147915?tappxkey=pub-12345-android-9876"
	if !strings.HasPrefix(reqs[0].Uri, want) {
		t.Fatalf("destination = %q, want prefix %q", reqs[0].Uri, want)
	}
}
