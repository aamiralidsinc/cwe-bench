package hidden_test

import (
	"time"

	"cosmossdk.io/math"
	sdk "github.com/cosmos/cosmos-sdk/types"

	"github.com/ixofoundation/ixo-blockchain/v7/app/apptesting"
	bondstypes "github.com/ixofoundation/ixo-blockchain/v7/x/bonds/types"
	claimstypes "github.com/ixofoundation/ixo-blockchain/v7/x/claims/types"
	iidtypes "github.com/ixofoundation/ixo-blockchain/v7/x/iid/types"
)

type vm struct {
	id   string
	addr sdk.AccAddress
	rels []string
}

// seedDoc stores a DID document with the supplied verification methods and
// relationships.
func seedDoc(s *apptesting.KeeperTestHelper, did string, vms ...vm) {
	now := s.Ctx.BlockTime()
	doc := iidtypes.IidDocument{Id: did, Metadata: &iidtypes.IidMetadata{Created: &now, VersionId: "v1"}}
	for _, spec := range vms {
		v := iidtypes.NewVerificationMethod(spec.id, iidtypes.DID(did), iidtypes.NewBlockchainAccountID(spec.addr.String()))
		doc.VerificationMethod = append(doc.VerificationMethod, &v)
		for _, rel := range spec.rels {
			switch rel {
			case iidtypes.Authentication:
				doc.Authentication = append(doc.Authentication, spec.id)
			case iidtypes.AssertionMethod:
				doc.AssertionMethod = append(doc.AssertionMethod, spec.id)
			}
		}
	}
	s.App.IidKeeper.SetDidDocument(s.Ctx, []byte(did), doc)
}

type bondOpts struct {
	did              string
	token            string
	creator          string
	controller       string
	oracle           string
	fnType           string
	reserves         []string
	exitFee          math.LegacyDec
	available        sdk.Coins
	state            string
	alphaBond        bool
	allowWithdrawals bool
}

func defaultBondOpts(did string) bondOpts {
	return bondOpts{
		did:              did,
		token:            "abctok",
		creator:          "did:ixo:creator",
		controller:       "did:ixo:controller",
		oracle:           "did:ixo:controller",
		fnType:           bondstypes.SwapperFunction,
		reserves:         []string{"uixo"},
		exitFee:          math.LegacyZeroDec(),
		available:        sdk.NewCoins(),
		state:            bondstypes.OpenState.String(),
		alphaBond:        false,
		allowWithdrawals: false,
	}
}

// seedBond writes a bond and an empty batch directly, so the handler under
// test only performs the operation being examined.
func seedBond(s *apptesting.KeeperTestHelper, opts bondOpts) string {
	b := bondstypes.Bond{
		Token:                        opts.token,
		Name:                         "bond",
		Description:                  "bond",
		FeeAddress:                   apptesting.RandomAccountAddress().String(),
		ReserveWithdrawalAddress:     apptesting.RandomAccountAddress().String(),
		ReserveTokens:                opts.reserves,
		FunctionType:                 opts.fnType,
		MaxSupply:                    sdk.NewCoin(opts.token, math.NewInt(1000000)),
		CurrentSupply:                sdk.NewCoin(opts.token, math.ZeroInt()),
		CurrentReserve:               sdk.NewCoins(),
		AvailableReserve:             opts.available,
		CurrentOutcomePaymentReserve: sdk.NewCoins(),
		AllowSells:                   true,
		AllowReserveWithdrawals:      opts.allowWithdrawals,
		AlphaBond:                    opts.alphaBond,
		State:                        opts.state,
		BondDid:                      opts.did,
		CreatorDid:                   iidtypes.DIDFragment(opts.creator),
		ControllerDid:                iidtypes.DIDFragment(opts.controller),
		OracleDid:                    iidtypes.DIDFragment(opts.oracle),
		TxFeePercentage:              math.LegacyZeroDec(),
		ExitFeePercentage:            opts.exitFee,
		SanityRate:                   math.LegacyZeroDec(),
		SanityMarginPercentage:       math.LegacyZeroDec(),
		BatchBlocks:                  math.NewUint(1),
		OutcomePayment:               math.NewInt(1000),
	}
	s.App.BondsKeeper.SetBond(s.Ctx, opts.did, b)
	s.App.BondsKeeper.SetBondDid(s.Ctx, opts.token, opts.did)
	s.App.BondsKeeper.SetBatch(s.Ctx, opts.did, bondstypes.NewBatch(opts.did, opts.token, math.NewUint(5)))
	return opts.did
}

func uixo(s *apptesting.KeeperTestHelper, a sdk.AccAddress) math.Int {
	return s.App.BankKeeper.GetBalance(s.Ctx, a, "uixo").Amount
}

func seedCollection(s *apptesting.KeeperTestHelper, id, admin string, deposit math.Int) {
	now := s.Ctx.BlockTime()
	start := now.Add(-time.Hour)
	end := now.Add(24 * time.Hour)
	s.App.ClaimsKeeper.SetCollection(s.Ctx, claimstypes.Collection{
		Id:        id,
		Entity:    "did:ixo:entity-claims",
		Admin:     admin,
		Protocol:  "did:ixo:protocol-claims",
		State:     claimstypes.CollectionState_open,
		StartDate: &start,
		EndDate:   &end,
		Payments: &claimstypes.Payments{
			Submission: &claimstypes.Payment{},
			Evaluation: &claimstypes.Payment{},
			Approval:   &claimstypes.Payment{},
			Rejection:  &claimstypes.Payment{},
		},
		EscrowAccount:        apptesting.RandomAccountAddress().String(),
		DisputeDepositAmount: sdk.NewCoins(sdk.NewCoin("uixo", deposit)),
		Adjudicators:         []*claimstypes.AdjudicationDid{{Did: "did:ixo:adjudicator", RewardPercentage: math.LegacyNewDec(10)}},
	})
}
