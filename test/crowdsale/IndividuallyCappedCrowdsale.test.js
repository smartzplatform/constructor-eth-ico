
const { ether } = require('../../node_modules/zeppelin-solidity/test/helpers/ether');
const { expectThrow } = require('../../node_modules/zeppelin-solidity/test/helpers/expectThrow');
const { EVMRevert } = require('../../node_modules/zeppelin-solidity/test/helpers/EVMRevert');
const { increaseTimeTo, duration } = require('../../node_modules/zeppelin-solidity/test/helpers/increaseTime');
const { latestTime } = require('../../node_modules/zeppelin-solidity/test/helpers/latestTime');
const { advanceBlock } = require('../../node_modules/zeppelin-solidity/test/helpers/advanceToBlock');


const BigNumber = web3.BigNumber;

require('chai')
  .use(require('chai-bignumber')(BigNumber))
  .should();

const CappedCrowdsale = artifacts.require('ICO');
const SimpleToken = artifacts.require('SimpleToken');

contract('IndividuallyCappedCrowdsale', function ([_, wallet, alice, bob, charlie]) {
  const rate = new BigNumber(1);
  const capAlice = ether(10);
  const capBob = ether(2);
  const lessThanCapAlice = ether(6);
  const lessThanCapBoth = ether(1);
  const tokenSupply = new BigNumber('1e22');
  const cap = ether(10000);


  describe('individual capping', function () {
    beforeEach(async function () {
      await advanceBlock();

      this.token = await SimpleToken.new();
      this.openingTime = (await latestTime());
      this.closingTime = this.openingTime + duration.weeks(1);
      this.crowdsale = await CappedCrowdsale.new(rate, wallet, this.token.address, 1, this.openingTime, this.closingTime, cap);
      await this.crowdsale.addAddressesToWhitelist([alice, bob, charlie]);

      await this.crowdsale.setUserCap(alice, capAlice);
      await this.crowdsale.setUserCap(bob, capBob);
      await this.token.transfer(this.crowdsale.address, tokenSupply); 
    });

    describe('accepting payments', function () {
      it('should accept payments within cap', async function () {
        await this.crowdsale.buyTokens(alice, { value: lessThanCapAlice });
        await this.crowdsale.buyTokens(bob, { value: lessThanCapBoth });
      });

      it('should reject payments outside cap', async function () {
        await this.crowdsale.buyTokens(alice, { value: capAlice });
        await expectThrow(this.crowdsale.buyTokens(alice, { value: 1 }), EVMRevert);
      });

      it('should reject payments that exceed cap', async function () {
        await expectThrow(this.crowdsale.buyTokens(alice, { value: capAlice.plus(1) }), EVMRevert);
        await expectThrow(this.crowdsale.buyTokens(bob, { value: capBob.plus(1) }), EVMRevert);
      });

      it('should manage independent caps', async function () {
        await this.crowdsale.buyTokens(alice, { value: lessThanCapAlice });
        await expectThrow(this.crowdsale.buyTokens(bob, { value: lessThanCapAlice }), EVMRevert);
      });

      it('should default to a cap of zero', async function () {
        await expectThrow(this.crowdsale.buyTokens(charlie, { value: lessThanCapBoth }), EVMRevert);
      });
    });

    describe('reporting state', function () {
      it('should report correct cap', async function () {
        const retrievedCap = await this.crowdsale.getUserCap(alice);
        retrievedCap.should.be.bignumber.equal(capAlice);
      });

      it('should report actual contribution', async function () {
        await this.crowdsale.buyTokens(alice, { value: lessThanCapAlice });
        const retrievedContribution = await this.crowdsale.getUserContribution(alice);
        retrievedContribution.should.be.bignumber.equal(lessThanCapAlice);
      });
    });
  });

  describe('group capping', function () {
    beforeEach(async function () {
      await advanceBlock();

      this.token = await SimpleToken.new();
      this.openingTime = (await latestTime());
      this.closingTime = this.openingTime + duration.weeks(1);
      this.crowdsale = await CappedCrowdsale.new(rate, wallet, this.token.address, 1, this.openingTime, this.closingTime, cap);
      await this.crowdsale.addAddressesToWhitelist([alice, bob, charlie]);
      await this.crowdsale.setGroupCap([bob, charlie], capBob);
      await this.token.transfer(this.crowdsale.address, tokenSupply);
    });

    describe('accepting payments', function () {
      it('should accept payments within cap', async function () {
        await this.crowdsale.buyTokens(bob, { value: lessThanCapBoth });
        await this.crowdsale.buyTokens(charlie, { value: lessThanCapBoth });
      });

      it('should reject payments outside cap', async function () {
        await this.crowdsale.buyTokens(bob, { value: capBob });
        await expectThrow(this.crowdsale.buyTokens(bob, { value: 1 }), EVMRevert);
        await this.crowdsale.buyTokens(charlie, { value: capBob });
        await expectThrow(this.crowdsale.buyTokens(charlie, { value: 1 }), EVMRevert);
      });

      it('should reject payments that exceed cap', async function () {
        await expectThrow(this.crowdsale.buyTokens(bob, { value: capBob.plus(1) }), EVMRevert);
        await expectThrow(this.crowdsale.buyTokens(charlie, { value: capBob.plus(1) }), EVMRevert);
      });
    });

    describe('reporting state', function () {
      it('should report correct cap', async function () {
        const retrievedCapBob = await this.crowdsale.getUserCap(bob);
        retrievedCapBob.should.be.bignumber.equal(capBob);
        const retrievedCapCharlie = await this.crowdsale.getUserCap(charlie);
        retrievedCapCharlie.should.be.bignumber.equal(capBob);
      });
    });
  });
});
