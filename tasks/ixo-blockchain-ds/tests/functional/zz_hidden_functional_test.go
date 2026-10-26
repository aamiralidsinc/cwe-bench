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

// Each test here exercises a legitimate request that must keep working:
// the signer controls the DID it acts for (or is the party the record
// belongs to), and the request must succeed unchanged.
type FunctionalSuite struct {
	apptesting.KeeperTestHelper
}

func TestFunctionalSuite(t *testing.T) { suite.Run(t, new(FunctionalSuite)) }

func (s *FunctionalSuite) SetupTest() { s.Setup() }

// The payer names its own verification method; the coins move from its own
// account even when another verification method is present on the document.
func (s *FunctionalSuite) TestOutcomePayment_OwnDid() {
	payer := apptesting.RandomAccountAddress()
	s.FundAcc(payer, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000))))
	did := "did:ixo:payer-outcome"
	other := apptesting.RandomAccountAddress()
	seedDoc(&s.KeeperTestHelper, did,
		vm{id: did + "#key-1", addr: payer, rels: []string{iidtypes.Authentication}},
		vm{id: did + "#recovery", addr: other, rels: []string{iidtypes.Authentication}},
	)
	o := defaultBondOpts("did:ixo:bond-fun-1")
	o.creator, o.controller, o.oracle = did, did, did
	bondDid := seedBond(&s.KeeperTestHelper, o)

	before := uixo(&s.KeeperTestHelper, payer)
	_, err := s.RunMsg(&bondstypes.MsgMakeOutcomePayment{
		SenderDid:     iidtypes.DIDFragment(did + "#key-1"),
		Amount:        math.NewInt(500),
		BondDid:       bondDid,
		SenderAddress: payer.String(),
	})
	s.Require().NoError(err)
	s.Require().Equal(before.Sub(math.NewInt(500)), uixo(&s.KeeperTestHelper, payer))
}

func (s *FunctionalSuite) TestBuy_OwnDid() {
	buyer := apptesting.RandomAccountAddress()
	s.FundAcc(buyer, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000)), sdk.NewCoin("uatom", math.NewInt(100000))))
	did := "did:ixo:payer-buy"
	seedDoc(&s.KeeperTestHelper, did, vm{id: did + "#key-1", addr: buyer, rels: []string{iidtypes.Authentication}})
	o := defaultBondOpts("did:ixo:bond-fun-2")
	o.creator, o.controller, o.oracle = did, did, did
	o.reserves = []string{"uixo", "uatom"}
	o.state = bondstypes.HatchState.String()
	bondDid := seedBond(&s.KeeperTestHelper, o)

	before := uixo(&s.KeeperTestHelper, buyer)
	_, err := s.RunMsg(&bondstypes.MsgBuy{
		BuyerDid:     iidtypes.DIDFragment(did + "#key-1"),
		Amount:       sdk.NewCoin("abctok", math.NewInt(100)),
		MaxPrices:    sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(1000)), sdk.NewCoin("uatom", math.NewInt(1000))),
		BondDid:      bondDid,
		BuyerAddress: buyer.String(),
	})
	s.Require().NoError(err)
	s.Require().Equal(before.Sub(math.NewInt(1000)), uixo(&s.KeeperTestHelper, buyer))
	s.Require().Equal(math.NewInt(100), s.App.BankKeeper.GetBalance(s.Ctx, buyer, "abctok").Amount)
}

func (s *FunctionalSuite) TestSwap_OwnDid() {
	swapper := apptesting.RandomAccountAddress()
	s.FundAcc(swapper, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000)), sdk.NewCoin("uatom", math.NewInt(100000))))
	did := "did:ixo:payer-swap"
	seedDoc(&s.KeeperTestHelper, did, vm{id: did + "#key-1", addr: swapper, rels: []string{iidtypes.Authentication}})
	o := defaultBondOpts("did:ixo:bond-fun-3")
	o.creator, o.controller, o.oracle = did, did, did
	o.reserves = []string{"uixo", "uatom"}
	bondDid := seedBond(&s.KeeperTestHelper, o)
	b := s.App.BondsKeeper.MustGetBond(s.Ctx, bondDid)
	b.CurrentSupply = sdk.NewCoin("abctok", math.NewInt(1000))
	b.CurrentReserve = sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000)), sdk.NewCoin("uatom", math.NewInt(100000)))
	s.App.BondsKeeper.SetBond(s.Ctx, bondDid, b)

	before := uixo(&s.KeeperTestHelper, swapper)
	_, err := s.RunMsg(&bondstypes.MsgSwap{
		SwapperDid:     iidtypes.DIDFragment(did + "#key-1"),
		From:           sdk.NewCoin("uixo", math.NewInt(700)),
		ToToken:        "uatom",
		BondDid:        bondDid,
		SwapperAddress: swapper.String(),
	})
	s.Require().NoError(err)
	s.Require().Equal(before.Sub(math.NewInt(700)), uixo(&s.KeeperTestHelper, swapper))
}

func (s *FunctionalSuite) TestEditBond_CreatorKey() {
	creator := apptesting.RandomAccountAddress()
	did := "did:ixo:creator-fun"
	seedDoc(&s.KeeperTestHelper, did, vm{id: did + "#key-1", addr: creator, rels: []string{iidtypes.Authentication}})
	o := defaultBondOpts("did:ixo:bond-fun-4")
	o.creator, o.controller, o.oracle = did, did, did
	bondDid := seedBond(&s.KeeperTestHelper, o)

	_, err := s.RunMsg(&bondstypes.MsgEditBond{
		BondDid:                bondDid,
		Name:                   "renamed",
		Description:            bondstypes.DoNotModifyField,
		OrderQuantityLimits:    bondstypes.DoNotModifyField,
		SanityRate:             bondstypes.DoNotModifyField,
		SanityMarginPercentage: bondstypes.DoNotModifyField,
		EditorDid:              iidtypes.DIDFragment(did),
		EditorAddress:          creator.String(),
	})
	s.Require().NoError(err)
	s.Require().Equal("renamed", s.App.BondsKeeper.MustGetBond(s.Ctx, bondDid).Name)
}

// A controller key registered under the assertion-method relationship is
// equally able to act for the DID.
func (s *FunctionalSuite) TestEditBond_AssertionMethodKey() {
	creator := apptesting.RandomAccountAddress()
	did := "did:ixo:creator-assertion"
	seedDoc(&s.KeeperTestHelper, did, vm{id: did + "#assert-1", addr: creator, rels: []string{iidtypes.AssertionMethod}})
	o := defaultBondOpts("did:ixo:bond-fun-5")
	o.creator, o.controller, o.oracle = did, did, did
	bondDid := seedBond(&s.KeeperTestHelper, o)

	_, err := s.RunMsg(&bondstypes.MsgEditBond{
		BondDid:                bondDid,
		Name:                   "renamed-assertion",
		Description:            bondstypes.DoNotModifyField,
		OrderQuantityLimits:    bondstypes.DoNotModifyField,
		SanityRate:             bondstypes.DoNotModifyField,
		SanityMarginPercentage: bondstypes.DoNotModifyField,
		EditorDid:              iidtypes.DIDFragment(did),
		EditorAddress:          creator.String(),
	})
	s.Require().NoError(err)
	s.Require().Equal("renamed-assertion", s.App.BondsKeeper.MustGetBond(s.Ctx, bondDid).Name)
}

func (s *FunctionalSuite) TestUpdateBondState_ControllerKey() {
	controller := apptesting.RandomAccountAddress()
	did := "did:ixo:controller-fun"
	seedDoc(&s.KeeperTestHelper, did, vm{id: did + "#key-1", addr: controller, rels: []string{iidtypes.Authentication}})
	o := defaultBondOpts("did:ixo:bond-fun-6")
	o.creator, o.controller, o.oracle = "did:ixo:creator-fun6", did, did
	o.fnType = bondstypes.AugmentedFunction
	bondDid := seedBond(&s.KeeperTestHelper, o)

	_, err := s.RunMsg(&bondstypes.MsgUpdateBondState{
		BondDid:       bondDid,
		State:         bondstypes.SettleState.String(),
		EditorDid:     iidtypes.DIDFragment(did),
		EditorAddress: controller.String(),
	})
	s.Require().NoError(err)
	s.Require().Equal(bondstypes.SettleState.String(), s.App.BondsKeeper.MustGetBond(s.Ctx, bondDid).State)
}

func (s *FunctionalSuite) TestWithdrawReserve_ControllerKey() {
	controller := apptesting.RandomAccountAddress()
	s.FundAcc(controller, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000))))
	did := "did:ixo:controller-fun7"
	frag := did + "#key-1"
	seedDoc(&s.KeeperTestHelper, did, vm{id: frag, addr: controller, rels: []string{iidtypes.Authentication}})
	o := defaultBondOpts("did:ixo:bond-fun-7")
	o.creator, o.controller, o.oracle = "did:ixo:creator-fun7", frag, frag
	o.fnType = bondstypes.AugmentedFunction
	o.alphaBond = true
	o.allowWithdrawals = true
	o.exitFee = math.LegacyMustNewDecFromStr("10")
	o.available = sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(5000)))
	bondDid := seedBond(&s.KeeperTestHelper, o)
	s.FundModuleAcc(bondstypes.BondsReserveAccount, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(5000))))

	before := uixo(&s.KeeperTestHelper, controller)
	_, err := s.RunMsg(&bondstypes.MsgWithdrawReserve{
		BondDid:           bondDid,
		Amount:            sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(1000))),
		WithdrawerDid:     iidtypes.DIDFragment(frag),
		WithdrawerAddress: controller.String(),
	})
	s.Require().NoError(err)
	s.Require().Equal(before.Sub(math.NewInt(100)), uixo(&s.KeeperTestHelper, controller), "the exit fee comes from the controller's own account")
	s.Require().Equal(math.NewInt(4000), s.App.BondsKeeper.MustGetBond(s.Ctx, bondDid).AvailableReserve.AmountOf("uixo"))
}

func (s *FunctionalSuite) seedEntity(entityDid, controllerDid, relayerDid string) {
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

func (s *FunctionalSuite) TestUpdateEntity_ControllerKey() {
	controller := apptesting.RandomAccountAddress()
	controllerDid := "did:ixo:controller-fun8"
	seedDoc(&s.KeeperTestHelper, controllerDid, vm{id: controllerDid + "#key-1", addr: controller, rels: []string{iidtypes.Authentication}})
	entityDid := "did:ixo:entity:fun-update"
	s.seedEntity(entityDid, controllerDid, "did:ixo:relayer-fun8")

	now := s.Ctx.BlockTime()
	end := now.Add(time.Hour)
	_, err := s.RunMsg(&entitytypes.MsgUpdateEntity{
		Id:                entityDid,
		EntityStatus:      2,
		StartDate:         &now,
		EndDate:           &end,
		Credentials:       []string{"credential"},
		ControllerDid:     iidtypes.DIDFragment(controllerDid + "#key-1"),
		ControllerAddress: controller.String(),
	})
	s.Require().NoError(err)
	got, _ := s.App.EntityKeeper.GetEntity(s.Ctx, []byte(entityDid))
	s.Require().Equal(int32(2), got.Status)
}

func (s *FunctionalSuite) TestUpdateEntityVerified_RelayerKey() {
	relayer := apptesting.RandomAccountAddress()
	relayerDid := "did:ixo:relayer-fun9"
	seedDoc(&s.KeeperTestHelper, relayerDid, vm{id: relayerDid + "#key-1", addr: relayer, rels: []string{iidtypes.Authentication}})
	entityDid := "did:ixo:entity:fun-verify"
	s.seedEntity(entityDid, "did:ixo:controller-fun9", relayerDid)

	_, err := s.RunMsg(&entitytypes.MsgUpdateEntityVerified{
		Id:                 entityDid,
		EntityVerified:     true,
		RelayerNodeDid:     iidtypes.DIDFragment(relayerDid + "#key-1"),
		RelayerNodeAddress: relayer.String(),
	})
	s.Require().NoError(err)
	got, _ := s.App.EntityKeeper.GetEntity(s.Ctx, []byte(entityDid))
	s.Require().True(got.EntityVerified)
}

// An admin submits a claim on behalf of a service agent: the agent DID named
// on the record is a different party and must not need to sign.
func (s *FunctionalSuite) TestSubmitClaim_DelegatedAttribution() {
	admin := apptesting.RandomAccountAddress()
	agent := apptesting.RandomAccountAddress()
	agentDid := "did:ixo:claim-agent-fun"
	seedDoc(&s.KeeperTestHelper, agentDid, vm{id: agentDid + "#key-1", addr: agent, rels: []string{iidtypes.Authentication}})
	seedCollection(&s.KeeperTestHelper, "fun-submit", admin.String(), math.ZeroInt())

	_, err := s.RunMsg(&claimstypes.MsgSubmitClaim{
		CollectionId: "fun-submit",
		ClaimId:      "claim-fun-1",
		AgentDid:     iidtypes.DIDFragment(agentDid + "#key-1"),
		AgentAddress: agent.String(),
		AdminAddress: admin.String(),
	})
	s.Require().NoError(err)
	_, err = s.App.ClaimsKeeper.GetClaim(s.Ctx, "claim-fun-1")
	s.Require().NoError(err)
}

// A disputer stakes its own deposit from its own DID's account.
func (s *FunctionalSuite) TestDisputeClaim_OwnDid() {
	agent := apptesting.RandomAccountAddress()
	s.FundAcc(agent, sdk.NewCoins(sdk.NewCoin("uixo", math.NewInt(100000))))
	agentDid := "did:ixo:disputer-fun"
	seedDoc(&s.KeeperTestHelper, agentDid, vm{id: agentDid + "#key-1", addr: agent, rels: []string{iidtypes.Authentication}})
	seedCollection(&s.KeeperTestHelper, "fun-dispute", apptesting.RandomAccountAddress().String(), math.NewInt(250))
	s.App.ClaimsKeeper.SetClaim(s.Ctx, claimstypes.Claim{
		CollectionId: "fun-dispute",
		ClaimId:      "claim-fun-2",
		AgentDid:     "did:ixo:claim-agent-fun2",
		AgentAddress: apptesting.RandomAccountAddress().String(),
	})

	before := uixo(&s.KeeperTestHelper, agent)
	_, err := s.RunMsg(&claimstypes.MsgDisputeClaim{
		SubjectId:    "claim-fun-2",
		AgentDid:     iidtypes.DIDFragment(agentDid + "#key-1"),
		AgentAddress: agent.String(),
		Data:         &claimstypes.DisputeData{Uri: "uri", Type: "type", Proof: "proof-fun-2"},
		TargetRole:   claimstypes.DisputeTargetRole_target_submitter,
	})
	s.Require().NoError(err)
	s.Require().Equal(before.Sub(math.NewInt(250)), uixo(&s.KeeperTestHelper, agent))
}
