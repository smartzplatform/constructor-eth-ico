const { shouldBehaveLikeMintedCrowdsale } = require('./MintedCrowdsale.behaviour');
const { ether } = require('../helpers/ether');
const { advanceBlock } = require('../helpers/advanceToBlock');
const { increaseTimeTo, duration } = require('../helpers/increaseTime');
const { latestTime } = require('../helpers/latestTime');

const BigNumber = web3.BigNumber;

const MintedCrowdsale = artifacts.require('MintedIco');
const MintableToken = artifacts.require('MintableToken');
//const RBACMintableToken = artifacts.require('RBACMintableToken');

contract('MintedCrowdsale', function ([_, investor, wallet, purchaser]) {
  const rate = new BigNumber(1000);
  const value = ether(5);
  const cap = ether(10000);

  describe('using MintableToken', function () {
    beforeEach(async function () {
      this.token = await MintableToken.new();
      this.openingTime = (await latestTime());
      this.closingTime = this.openingTime + duration.weeks(1);
  
      this.crowdsale = await MintedCrowdsale.new(
        rate, wallet, this.token.address, 1, this.openingTime, this.closingTime, cap
      );
      await this.crowdsale.addAddressesToWhitelist([investor, purchaser, wallet, web3.eth.accounts[0]]);
      await this.crowdsale.setGroupCap([investor, purchaser, wallet, web3.eth.accounts[0]], cap);
      await this.token.transferOwnership(this.crowdsale.address);
  
    });

    it('should be token owner', async function () {
      const owner = await this.token.owner();
      owner.should.equal(this.crowdsale.address);
    });

    shouldBehaveLikeMintedCrowdsale([_, investor, wallet, purchaser], rate, value);
  });

 /*  describe('using RBACMintableToken', function () {
    const ROLE_MINTER = 'minter';

    beforeEach(async function () {
      this.token = await RBACMintableToken.new();
      this.crowdsale = await MintedCrowdsale.new(rate, wallet, this.token.address);
      await this.token.addMinter(this.crowdsale.address);
    });

    it('should have minter role on token', async function () {
      const isMinter = await this.token.hasRole(this.crowdsale.address, ROLE_MINTER);
      isMinter.should.equal(true);
    });

    shouldBehaveLikeMintedCrowdsale([_, investor, wallet, purchaser], rate, value);
  }); */
});
