const { ether } = require('../../node_modules/zeppelin-solidity/test/helpers/ether');
const { advanceBlock } = require('../../node_modules/zeppelin-solidity/test/helpers/advanceToBlock');
const { increaseTimeTo, duration } = require('../../node_modules/zeppelin-solidity/test/helpers/increaseTime');
const { latestTime } = require('../../node_modules/zeppelin-solidity/test/helpers/latestTime');
const { expectThrow } = require('../../node_modules/zeppelin-solidity/test/helpers/expectThrow');
const { EVMRevert } = require('../../node_modules/zeppelin-solidity/test/helpers/EVMRevert');
const { ethGetBalance } = require('../../node_modules/zeppelin-solidity/test/helpers/web3');

const BigNumber = web3.BigNumber;

require('chai')
  .use(require('chai-bignumber')(BigNumber))
  .should();

const RefundableCrowdsale = artifacts.require('ICO');
const SimpleToken = artifacts.require('SimpleToken');

contract('RefundableCrowdsale', function ([_, owner, wallet, investor, purchaser]) {
  const rate = new BigNumber(1);
  const goal = ether(50);
  const lessThanGoal = ether(45);
  const tokenSupply = new BigNumber('1e22');
  const cap = ether(10000);



  beforeEach(async function () {
    await advanceBlock();
    this.openingTime = (await latestTime()) + duration.weeks(1);
    this.closingTime = this.openingTime + duration.weeks(1);
    this.afterClosingTime = this.closingTime + duration.seconds(1);

    this.token = await SimpleToken.new();
    this.crowdsale = await RefundableCrowdsale.new(
      rate, wallet, this.token.address, goal, this.openingTime, this.closingTime, cap, { from: owner }
    );
    await this.crowdsale.addAddressesToWhitelist([investor, owner, wallet, purchaser], { from: owner });
    await this.crowdsale.setGroupCap([investor, owner, wallet, purchaser], cap,{ from: owner });

    await this.token.transfer(this.crowdsale.address, tokenSupply);
  });

  describe('creating a valid crowdsale', function () {
    it('should fail with zero goal', async function () {
      await expectThrow(
        RefundableCrowdsale.new(
           rate, wallet, this.token.address, 0, this.openingTime, this.closingTime, cap, { from: owner }
        ),
        EVMRevert,
      );
    });
  });

  it('should deny refunds before end', async function () {
    await expectThrow(this.crowdsale.claimRefund({ from: investor }), EVMRevert);
    await increaseTimeTo(this.openingTime);
    await expectThrow(this.crowdsale.claimRefund({ from: investor }), EVMRevert);
  });

  it('should deny refunds after end if goal was reached', async function () {
    await increaseTimeTo(this.openingTime);
    await this.crowdsale.sendTransaction({ value: goal, from: investor });
    await increaseTimeTo(this.afterClosingTime);
    await expectThrow(this.crowdsale.claimRefund({ from: investor }), EVMRevert);
  });

  it('should allow refunds after end if goal was not reached', async function () {
    await increaseTimeTo(this.openingTime);
    await this.crowdsale.sendTransaction({ value: lessThanGoal, from: investor });
    await increaseTimeTo(this.afterClosingTime);
    await this.crowdsale.finalize({ from: owner });
    const pre = await ethGetBalance(investor);
    await this.crowdsale.claimRefund({ from: investor, gasPrice: 0 });
    const post = await ethGetBalance(investor);
    post.minus(pre).should.be.bignumber.equal(lessThanGoal);
  });

  it('should forward funds to wallet after end if goal was reached', async function () {
    await increaseTimeTo(this.openingTime);
    await this.crowdsale.sendTransaction({ value: goal, from: investor });
    await increaseTimeTo(this.afterClosingTime);
    const pre = await ethGetBalance(wallet);
    await this.crowdsale.finalize({ from: owner });
    const post = await ethGetBalance(wallet);
    post.minus(pre).should.be.bignumber.equal(goal);
  });
});
