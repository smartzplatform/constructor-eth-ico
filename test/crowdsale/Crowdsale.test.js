const { ether } = require('../../node_modules/zeppelin-solidity/test/helpers/ether');
const { ethGetBalance } = require('../../node_modules/zeppelin-solidity/test/helpers/web3');
const { latestTime } = require('../../node_modules/zeppelin-solidity/test/helpers/latestTime');
const { increaseTimeTo, duration } = require('../../node_modules/zeppelin-solidity/test/helpers/increaseTime');
const { advanceBlock } = require('../../node_modules/zeppelin-solidity/test/helpers/advanceToBlock');


const BigNumber = web3.BigNumber;

const should = require('chai')
  .use(require('chai-bignumber')(BigNumber))
  .should();

const Crowdsale = artifacts.require('ICO');
const SimpleToken = artifacts.require('SimpleToken');

contract('Crowdsale', function ([_, investor, wallet, purchaser, investorCheck]) {
  const rate = new BigNumber(1);
  const value = ether(42);
  const tokenSupply = new BigNumber('1e22');
  const expectedTokenAmount = rate.mul(value);
  const cap = ether(10000);

  beforeEach(async function () {
    await advanceBlock();
    this.token = await SimpleToken.new();
    this.openingTime = (await latestTime());
    this.closingTime = this.openingTime + duration.weeks(1);
  
    this.crowdsale = await Crowdsale.new(rate, wallet, this.token.address, 1, this.openingTime, this.closingTime, cap);
    await this.crowdsale.addAddressesToWhitelist([web3.eth.accounts[0], purchaser, investor, investorCheck])
    await this.crowdsale.setGroupCap([web3.eth.accounts[0], purchaser, investor, investorCheck], cap)

    await this.token.transfer(this.crowdsale.address, tokenSupply);
  });

  describe('accepting payments', function () {
    it('should accept payments', async function () {
      await this.crowdsale.send(value);
      await this.crowdsale.buyTokens(investor, { value: value, from: purchaser });
    });
  });

  describe('high-level purchase', function () {
    it('should log purchase', async function () {
      const { logs } = await this.crowdsale.sendTransaction({ value: value, from: investor });
      const event = logs.find(e => e.event === 'TokenPurchase');
      should.exist(event);
      event.args.purchaser.should.equal(investor);
      event.args.beneficiary.should.equal(investor);
      event.args.value.should.be.bignumber.equal(value);
      event.args.amount.should.be.bignumber.equal(expectedTokenAmount);
    });

    it('should assign tokens to sender', async function () {
      await this.crowdsale.sendTransaction({ value: value, from: investor });
      const balance = await this.token.balanceOf(investor);
      balance.should.be.bignumber.equal(expectedTokenAmount);
    });

    it('should forward funds to wallet', async function () {
      const escrowAddr = await this.crowdsale.mEscrow();
      const pre = await ethGetBalance(escrowAddr);
      await this.crowdsale.sendTransaction({ value, from: investor });
      const post = await ethGetBalance(escrowAddr);
      post.minus(pre).should.be.bignumber.equal(value);
    });
  });

  describe('low-level purchase', function () {
    it('should log purchase', async function () {
      const { logs } = await this.crowdsale.buyTokens(investor, { value: value, from: purchaser });
      const event = logs.find(e => e.event === 'TokenPurchase');
      should.exist(event);
      event.args.purchaser.should.equal(purchaser);
      event.args.beneficiary.should.equal(investor);
      event.args.value.should.be.bignumber.equal(value);
      event.args.amount.should.be.bignumber.equal(expectedTokenAmount);
    });

    it('should assign tokens to beneficiary', async function () {
      await this.crowdsale.buyTokens(investor, { value, from: purchaser });
      const balance = await this.token.balanceOf(investor);
      balance.should.be.bignumber.equal(expectedTokenAmount);
    });

    it('should forward funds to wallet', async function () {
      const escrowAddr = await this.crowdsale.mEscrow();
      const pre = await ethGetBalance(escrowAddr);
      await this.crowdsale.buyTokens(investor, { value, from: purchaser });
      const post = await ethGetBalance(escrowAddr);
   
      post.minus(pre).should.be.bignumber.equal(value);
    });
  });
});
