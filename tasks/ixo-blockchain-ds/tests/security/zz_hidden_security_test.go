package hidden_test

import (
	"testing"
	"time"

	"cosmossdk.io/math"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/stretchr/testify/suite"

	"github.com/ixofoundation/ixo-blockchain/v7/app/apptesting"
	bondstypes "github.com/ixofoundation/ixo-blockchain/v7/x/bonds/types"
	claimstypes "github.com/ixofoundation/ixo-blockchain/v7/x/claims/types"
	entitytypes "github.com/ixofoundation/ixo-blockchain/v7/x/entity/types"
	iidtypes "github.com/ixofoundation/ixo-blockchain/v7/x/iid/types"
)

// Each test in this suite drives a real message through the application's
// message service router (the path taken by contract-dispatched and delegated
// messages) and asserts the protected account or record is unchanged.
type SecuritySuite struct {
	apptesting.KeeperTestHelper
}

func TestSecuritySuite(t *testing.T) { suite.Run(t, new(SecuritySuite)) }

func (s *SecuritySuite) SetupTest() { s.Setup() }

// ---------------------------------------------------------------------------
// Funds may only move out of an account the request signer holds.
// ---------------------------------------------------------------------------

// The signer names a DID it does not control; the coins must stay put.
func (s *SecuritySuite) TestOutcomePayment_OtherDid() {
	victim := apptesting.RandomAccountAddress()
	attacker := apptesting.RandomAccountAddress()
	s.FundAcc(victim, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000))))
	victimDid := "did:ixo:victim-outcome"
	seedDoc(&s.KeeperTestHelper, victimDid, vm{id: victimDid + "#key-1", addr: victim, rels: []string{iidtypes.Authentication}})

	o := defaultBondOpts("did:ixo:bond-sec-1")
	bondDid := seedBond(&s.KeeperTestHelper, o)

	before := uixo(&s.KeeperTestHelper, victim)
	_, _ = s.RunMsg(&bondstypes.MsgMakeOutcomePayment{
		SenderDid:     iidtypes.DIDFragment(victimDid + "#key-1"),
		Amount:        math.NewInt(500),
		BondDid:       bondDid,
		SenderAddress: attacker.String(),
	})
	s.Require().Equal(before, uixo(&s.KeeperTestHelper, victim), "coins must not leave an account the signer does not hold")
}

// The signer's own DID document lists another account's address as a
// verification method. Naming that method must not debit the other account.
func (s *SecuritySuite) TestOutcomePayment_ForeignVerificationMethod() {
	victim := apptesting.RandomAccountAddress()
	attacker := apptesting.RandomAccountAddress()
	s.FundAcc(victim, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000))))
	attackerDid := "did:ixo:attacker-outcome"
	seedDoc(&s.KeeperTestHelper, attackerDid,
		vm{id: attackerDid + "#own", addr: attacker, rels: []string{iidtypes.Authentication}},
		vm{id: attackerDid + "#shared", addr: victim, rels: []string{iidtypes.Authentication}},
	)

	o := defaultBondOpts("did:ixo:bond-sec-2")
	o.creator, o.controller, o.oracle = attackerDid, attackerDid, attackerDid
	bondDid := seedBond(&s.KeeperTestHelper, o)

	before := uixo(&s.KeeperTestHelper, victim)
	_, _ = s.RunMsg(&bondstypes.MsgMakeOutcomePayment{
		SenderDid:     iidtypes.DIDFragment(attackerDid + "#shared"),
		Amount:        math.NewInt(500),
		BondDid:       bondDid,
		SenderAddress: attacker.String(),
	})
	s.Require().Equal(before, uixo(&s.KeeperTestHelper, victim), "a verification method entry must not make another account the signer's")
}

// An omitted signer address cannot be treated as authorisation.
func (s *SecuritySuite) TestOutcomePayment_EmptySigner() {
	victim := apptesting.RandomAccountAddress()
	s.FundAcc(victim, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000))))
	victimDid := "did:ixo:victim-empty"
	seedDoc(&s.KeeperTestHelper, victimDid, vm{id: victimDid + "#key-1", addr: victim, rels: []string{iidtypes.Authentication}})
	o := defaultBondOpts("did:ixo:bond-sec-3")
	bondDid := seedBond(&s.KeeperTestHelper, o)

	before := uixo(&s.KeeperTestHelper, victim)
	_, _ = s.RunMsg(&bondstypes.MsgMakeOutcomePayment{
		SenderDid: iidtypes.DIDFragment(victimDid + "#key-1"),
		Amount:    math.NewInt(200),
		BondDid:   bondDid,
	})
	s.Require().Equal(before, uixo(&s.KeeperTestHelper, victim), "an empty signer authorises nothing")
}

func (s *SecuritySuite) TestBuy_ForeignVerificationMethod() {
	victim := apptesting.RandomAccountAddress()
	attacker := apptesting.RandomAccountAddress()
	s.FundAcc(victim, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000)), sdk.NewCoin("uatom", math.NewInt(100000))))
	attackerDid := "did:ixo:attacker-buy"
	seedDoc(&s.KeeperTestHelper, attackerDid,
		vm{id: attackerDid + "#own", addr: attacker, rels: []string{iidtypes.Authentication}},
		vm{id: attackerDid + "#shared", addr: victim, rels: []string{iidtypes.Authentication}},
	)
	o := defaultBondOpts("did:ixo:bond-sec-4")
	o.creator, o.controller, o.oracle = attackerDid, attackerDid, attackerDid
	o.reserves = []string{"uixo", "uatom"}
	o.state = bondstypes.HatchState.String()
	bondDid := seedBond(&s.KeeperTestHelper, o)

	before := uixo(&s.KeeperTestHelper, victim)
	_, _ = s.RunMsg(&bondstypes.MsgBuy{
		BuyerDid:  iidtypes.DIDFragment(attackerDid + "#shared"),
		Amount:    sdk.NewCoin("abctok", math.NewInt(100)),
		MaxPrices: sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(1000)), sdk.NewCoin("uatom", math.NewInt(1000))),
		BondDid:   bondDid,
		BuyerAddress: attacker.String(),
	})
	s.Require().Equal(before, uixo(&s.KeeperTestHelper, victim), "coins must not leave an account the signer does not hold")
}

func (s *SecuritySuite) TestSwap_ForeignVerificationMethod() {
	victim := apptesting.RandomAccountAddress()
	attacker := apptesting.RandomAccountAddress()
	s.FundAcc(victim, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000)), sdk.NewCoin("uatom", math.NewInt(100000))))
	attackerDid := "did:ixo:attacker-swap"
	seedDoc(&s.KeeperTestHelper, attackerDid,
		vm{id: attackerDid + "#own", addr: attacker, rels: []string{iidtypes.Authentication}},
		vm{id: attackerDid + "#shared", addr: victim, rels: []string{iidtypes.Authentication}},
	)
	o := defaultBondOpts("did:ixo:bond-sec-5")
	o.creator, o.controller, o.oracle = attackerDid, attackerDid, attackerDid
	o.reserves = []string{"uixo", "uatom"}
	bondDid := seedBond(&s.KeeperTestHelper, o)
	b := s.App.BondsKeeper.MustGetBond(s.Ctx, bondDid)
	b.CurrentSupply = sdk.NewCoin("abctok", math.NewInt(1000))
	b.CurrentReserve = sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000)), sdk.NewCoin("uatom", math.NewInt(100000)))
	s.App.BondsKeeper.SetBond(s.Ctx, bondDid, b)

	before := uixo(&s.KeeperTestHelper, victim)
	_, _ = s.RunMsg(&bondstypes.MsgSwap{
		SwapperDid:    iidtypes.DIDFragment(attackerDid + "#shared"),
		From:          sdk.NewCoin("uixo", math.NewInt(700)),
		ToToken:       "uatom",
		BondDid:       bondDid,
		SwapperAddress: attacker.String(),
	})
	s.Require().Equal(before, uixo(&s.KeeperTestHelper, victim), "coins must not leave an account the signer does not hold")
}

// ---------------------------------------------------------------------------
// Records that belong to a DID may only change for that DID's controllers.
// ---------------------------------------------------------------------------

func (s *SecuritySuite) TestEditBond_UnauthorizedSigner() {
	attacker := apptesting.RandomAccountAddress()
	creatorDid := "did:ixo:creator-edit"
	o := defaultBondOpts("did:ixo:bond-sec-6")
	o.creator, o.controller, o.oracle = creatorDid, creatorDid, creatorDid
	bondDid := seedBond(&s.KeeperTestHelper, o)

	_, _ = s.RunMsg(&bondstypes.MsgEditBond{
		BondDid:             bondDid,
		Name:                "hijacked",
		Description:         bondstypes.DoNotModifyField,
		OrderQuantityLimits: bondstypes.DoNotModifyField,
		SanityRate:          bondstypes.DoNotModifyField,
		SanityMarginPercentage: bondstypes.DoNotModifyField,
		EditorDid:           iidtypes.DIDFragment(creatorDid),
		EditorAddress:       attacker.String(),
	})
	got := s.App.BondsKeeper.MustGetBond(s.Ctx, bondDid)
	s.Require().NotEqual("hijacked", got.Name, "bond records must only change for the DID's controllers")
}

func (s *SecuritySuite) TestUpdateBondState_UnauthorizedSigner() {
	attacker := apptesting.RandomAccountAddress()
	controllerDid := "did:ixo:controller-state"
	o := defaultBondOpts("did:ixo:bond-sec-7")
	o.creator, o.controller, o.oracle = "did:ixo:creator-state", controllerDid, controllerDid
	o.fnType = bondstypes.AugmentedFunction
	bondDid := seedBond(&s.KeeperTestHelper, o)

	_, _ = s.RunMsg(&bondstypes.MsgUpdateBondState{
		BondDid:       bondDid,
		State:         bondstypes.SettleState.String(),
		EditorDid:     iidtypes.DIDFragment(controllerDid),
		EditorAddress: attacker.String(),
	})
	got := s.App.BondsKeeper.MustGetBond(s.Ctx, bondDid)
	s.Require().Equal(bondstypes.OpenState.String(), got.State, "bond state must only change for the DID's controllers")
}

func (s *SecuritySuite) TestWithdrawReserve_UnauthorizedSigner() {
	attacker := apptesting.RandomAccountAddress()
	controllerDid := "did:ixo:controller-reserve"
	o := defaultBondOpts("did:ixo:bond-sec-8")
	o.creator, o.controller, o.oracle = "did:ixo:creator-reserve", controllerDid, controllerDid
	o.fnType = bondstypes.AugmentedFunction
	o.alphaBond = true
	o.allowWithdrawals = true
	o.available = sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(5000)))
	bondDid := seedBond(&s.KeeperTestHelper, o)
	s.FundModuleAcc(bondstypes.BondsReserveAccount, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(5000))))

	_, _ = s.RunMsg(&bondstypes.MsgWithdrawReserve{
		BondDid:           bondDid,
		Amount:            sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(1000))),
		WithdrawerDid:     iidtypes.DIDFragment(controllerDid),
		WithdrawerAddress: attacker.String(),
	})
	got := s.App.BondsKeeper.MustGetBond(s.Ctx, bondDid)
	s.Require().Equal(o.available.String(), got.AvailableReserve.String(), "the bond reserve must only move for the controller")
}

// The bond's stored controller DID resolves, through a verification method
// the signer controls the DID document for, to another account. The fee debit
// must not follow that entry.
func (s *SecuritySuite) TestWithdrawReserve_FeeForeignVerificationMethod() {
	victim := apptesting.RandomAccountAddress()
	attacker := apptesting.RandomAccountAddress()
	s.FundAcc(victim, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000))))
	attackerDid := "did:ixo:attacker-reserve"
	seedDoc(&s.KeeperTestHelper, attackerDid,
		vm{id: attackerDid + "#own", addr: attacker, rels: []string{iidtypes.Authentication}},
		vm{id: attackerDid + "#shared", addr: victim, rels: []string{iidtypes.Authentication}},
	)
	o := defaultBondOpts("did:ixo:bond-sec-9")
	o.creator, o.controller, o.oracle = attackerDid, attackerDid+"#shared", attackerDid
	o.fnType = bondstypes.AugmentedFunction
	o.alphaBond = true
	o.allowWithdrawals = true
	o.exitFee = math.LegacyMustNewDecFromStr("10")
	o.available = sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(5000)))
	bondDid := seedBond(&s.KeeperTestHelper, o)
	s.FundModuleAcc(bondstypes.BondsReserveAccount, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(5000))))

	before := uixo(&s.KeeperTestHelper, victim)
	_, _ = s.RunMsg(&bondstypes.MsgWithdrawReserve{
		BondDid:           bondDid,
		Amount:            sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(1000))),
		WithdrawerDid:     iidtypes.DIDFragment(attackerDid + "#shared"),
		WithdrawerAddress: attacker.String(),
	})
	s.Require().Equal(before, uixo(&s.KeeperTestHelper, victim), "a verification method entry must not make another account the signer's")
}

func (s *SecuritySuite) seedEntity(entityDid, controllerDid, relayerDid string) {
	now := s.Ctx.BlockTime()
	s.App.IidKeeper.SetDidDocument(s.Ctx, []byte(entityDid), iidtypes.IidDocument{
		Id:         entityDid,
		Controller: []string{entityDid, controllerDid},
		Metadata:   &iidtypes.IidMetadata{Created: &now, VersionId: "v1"},
	})
	meta := entitytypes.NewEntityMetadata(s.Ctx.TxBytes(), now)
	s.App.EntityKeeper.SetEntity(s.Ctx, []byte(entityDid), entitytypes.Entity{
		Id:          entityDid,
		Type:        "asset",
		Status:      1,
		Metadata:    &meta,
		StartDate:   &now,
		RelayerNode: relayerDid,
	})
}

func (s *SecuritySuite) TestUpdateEntity_UnauthorizedSigner() {
	victim := apptesting.RandomAccountAddress()
	attacker := apptesting.RandomAccountAddress()
	controllerDid := "did:ixo:controller-entity"
	seedDoc(&s.KeeperTestHelper, controllerDid, vm{id: controllerDid + "#key-1", addr: victim, rels: []string{iidtypes.Authentication}})
	entityDid := "did:ixo:entity:sec-update"
	s.seedEntity(entityDid, controllerDid, "did:ixo:relayer-entity")

	now := s.Ctx.BlockTime()
	end := now.Add(time.Hour)
	_, _ = s.RunMsg(&entitytypes.MsgUpdateEntity{
		Id:                entityDid,
		EntityStatus:      9,
		StartDate:         &now,
		EndDate:           &end,
		Credentials:       []string{"forged"},
		ControllerDid:     iidtypes.DIDFragment(controllerDid),
		ControllerAddress: attacker.String(),
	})
	got, found := s.App.EntityKeeper.GetEntity(s.Ctx, []byte(entityDid))
	s.Require().True(found)
	s.Require().Equal(int32(1), got.Status, "entity records must only change for the controller DID's key")
}

func (s *SecuritySuite) TestUpdateEntityVerified_UnauthorizedSigner() {
	victim := apptesting.RandomAccountAddress()
	attacker := apptesting.RandomAccountAddress()
	relayerDid := "did:ixo:relayer-verify"
	seedDoc(&s.KeeperTestHelper, relayerDid, vm{id: relayerDid + "#key-1", addr: victim, rels: []string{iidtypes.Authentication}})
	entityDid := "did:ixo:entity:sec-verify"
	s.seedEntity(entityDid, "did:ixo:controller-verify", relayerDid)

	_, _ = s.RunMsg(&entitytypes.MsgUpdateEntityVerified{
		Id:                 entityDid,
		EntityVerified:     true,
		RelayerNodeDid:     iidtypes.DIDFragment(relayerDid),
		RelayerNodeAddress: attacker.String(),
	})
	got, _ := s.App.EntityKeeper.GetEntity(s.Ctx, []byte(entityDid))
	s.Require().False(got.EntityVerified, "the verified flag must only change for the relayer DID's key")
}

// The dispute deposit is funded from the account the DID document registers.
// That account must belong to the signer.
func (s *SecuritySuite) TestDisputeClaim_DepositForeignVerificationMethod() {
	victim := apptesting.RandomAccountAddress()
	attacker := apptesting.RandomAccountAddress()
	s.FundAcc(victim, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000))))
	attackerDid := "did:ixo:attacker-dispute"
	seedDoc(&s.KeeperTestHelper, attackerDid,
		vm{id: attackerDid + "#own", addr: attacker, rels: []string{iidtypes.Authentication}},
		vm{id: attackerDid + "#shared", addr: victim, rels: []string{iidtypes.Authentication}},
	)
	seedCollection(&s.KeeperTestHelper, "dispute-sec", apptesting.RandomAccountAddress().String(), math.NewInt(250))
	s.App.ClaimsKeeper.SetClaim(s.Ctx, claimstypes.Claim{
		CollectionId: "dispute-sec",
		ClaimId:      "claim-sec-1",
		AgentDid:     "did:ixo:claim-agent",
		AgentAddress: apptesting.RandomAccountAddress().String(),
	})

	before := uixo(&s.KeeperTestHelper, victim)
	_, _ = s.RunMsg(&claimstypes.MsgDisputeClaim{
		SubjectId:    "claim-sec-1",
		AgentDid:     iidtypes.DIDFragment(attackerDid + "#shared"),
		AgentAddress: attacker.String(),
		Data:         &claimstypes.DisputeData{Uri: "uri", Type: "type", Proof: "proof-sec-1"},
		TargetRole:   claimstypes.DisputeTargetRole_target_submitter,
	})
	s.Require().Equal(before, uixo(&s.KeeperTestHelper, victim), "the deposit must not be taken from another account")
}
