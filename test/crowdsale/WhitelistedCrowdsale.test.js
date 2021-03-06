const { ether } = require('../../node_modules/zeppelin-solidity/test/helpers/ether');
const { expectThrow } = require('../../node_modules/zeppelin-solidity/test/helpers/expectThrow');
const { increaseTimeTo, duration } = require('../../node_modules/zeppelin-solidity/test/helpers/increaseTime');
const { latestTime } = require('../../node_modules/zeppelin-solidity/test/helpers/latestTime');
const { advanceBlock } = require('../../node_modules/zeppelin-solidity/test/helpers/advanceToBlock');


const BigNumber = web3.BigNumber;

require('chai')
  .should();

const WhitelistedCrowdsale = artifacts.require('ICO');
const SimpleToken = artifacts.require('SimpleToken');

contract('WhitelistedCrowdsale', function ([_, wallet, authorized, unauthorized, anotherAuthorized]) {
  const rate = 1;
  const value = ether(42);
  const tokenSupply = new BigNumber('1e22');
  const cap = ether(10000);

  describe('single user whitelisting', function () {

    beforeEach(async function () {
      await advanceBlock();
      this.token = await SimpleToken.new();
      this.openingTime = (await latestTime());
      this.closingTime = this.openingTime + duration.weeks(1);
    
      this.crowdsale = await WhitelistedCrowdsale.new(rate, wallet, this.token.address, 1, this.openingTime, this.closingTime, cap);
      await this.token.transfer(this.crowdsale.address, tokenSupply);
      await this.crowdsale.addAddressToWhitelist(authorized);
      await this.crowdsale.setUserCap(authorized, cap)
    });

    describe('accepting payments', function () {
      it('should accept payments to whitelisted (from whichever buyers)', async function () {
        await this.crowdsale.sendTransaction({ value, from: authorized });
        await this.crowdsale.buyTokens(authorized, { value: value, from: authorized });
        await this.crowdsale.buyTokens(authorized, { value: value, from: unauthorized });
      });

      it('should reject payments to not whitelisted (from whichever buyers)', async function () {
        await expectThrow(this.crowdsale.sendTransaction({ value, from: unauthorized }));
        await expectThrow(this.crowdsale.buyTokens(unauthorized, { value: value, from: unauthorized }));
        await expectThrow(this.crowdsale.buyTokens(unauthorized, { value: value, from: authorized }));
      });

      it('should reject payments to addresses removed from whitelist', async function () {
        await this.crowdsale.removeAddressFromWhitelist(authorized);
        await expectThrow(this.crowdsale.buyTokens(authorized, { value: value, from: authorized }));
      });
    });

    describe('reporting whitelisted', function () {
      it('should correctly report whitelisted addresses', async function () {
        const isAuthorized = await this.crowdsale.whitelist(authorized);
        isAuthorized.should.equal(true);
        const isntAuthorized = await this.crowdsale.whitelist(unauthorized);
        isntAuthorized.should.equal(false);
      });
    });
  });

  describe('many user whitelisting', function () {

 
    beforeEach(async function () {
      await advanceBlock();
      this.token = await SimpleToken.new();
      this.openingTime = (await latestTime());
      this.closingTime = this.openingTime + duration.weeks(1);
      this.crowdsale = await WhitelistedCrowdsale.new(rate, wallet, this.token.address, 1, this.openingTime, this.closingTime, cap);
      await this.token.transfer(this.crowdsale.address, tokenSupply);
      await this.crowdsale.addAddressesToWhitelist([authorized, anotherAuthorized]);
      await this.crowdsale.setGroupCap([authorized, anotherAuthorized], cap);

    });

    describe('accepting payments', function () {
      it('should accept payments to whitelisted (from whichever buyers)', async function () {
        await this.crowdsale.buyTokens(authorized, { value: value, from: authorized });
        await this.crowdsale.buyTokens(authorized, { value: value, from: unauthorized });
        await this.crowdsale.buyTokens(anotherAuthorized, { value: value, from: authorized });
        await this.crowdsale.buyTokens(anotherAuthorized, { value: value, from: unauthorized });
      });

      it('should reject payments to not whitelisted (with whichever buyers)', async function () {
        await expectThrow(this.crowdsale.send(value));
        await expectThrow(this.crowdsale.buyTokens(unauthorized, { value: value, from: unauthorized }));
        await expectThrow(this.crowdsale.buyTokens(unauthorized, { value: value, from: authorized }));
      });

      it('should reject payments to addresses removed from whitelist', async function () {
        await this.crowdsale.removeAddressFromWhitelist(anotherAuthorized);
        await this.crowdsale.buyTokens(authorized, { value: value, from: authorized });
        await expectThrow(this.crowdsale.buyTokens(anotherAuthorized, { value: value, from: authorized }));
      });
    });

    describe('reporting whitelisted', function () {
      it('should correctly report whitelisted addresses', async function () {
        const isAuthorized = await this.crowdsale.whitelist(authorized);
        isAuthorized.should.equal(true);
        const isAnotherAuthorized = await this.crowdsale.whitelist(anotherAuthorized);
        isAnotherAuthorized.should.equal(true);
        const isntAuthorized = await this.crowdsale.whitelist(unauthorized);
        isntAuthorized.should.equal(false);
      });
    });
  });
});
