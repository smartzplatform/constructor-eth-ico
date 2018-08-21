const { advanceBlock } = require('../helpers/advanceToBlock');
const { increaseTimeTo, duration } = require('../helpers/increaseTime');
const { latestTime } = require('../helpers/latestTime');
const { expectThrow } = require('../helpers/expectThrow');
const { EVMRevert } = require('../helpers/EVMRevert');
const { ether } = require('../helpers/ether');


const BigNumber = web3.BigNumber;

const should = require('chai')
  .use(require('chai-bignumber')(BigNumber))
  .should();

const FinalizableCrowdsale = artifacts.require('ICO');
const MintableToken = artifacts.require('MintableToken');

contract('FinalizableCrowdsale', function ([_, owner, wallet, thirdparty]) {
  const rate = new BigNumber(1000);
  const cap = ether(10000);


  before(async function () {
    // Advance to the next block to correctly read time in the solidity "now" function interpreted by ganache
    await advanceBlock();
  });

  beforeEach(async function () {
    this.openingTime = (await latestTime()) + duration.weeks(1);
    this.closingTime = this.openingTime + duration.weeks(1);
    this.afterClosingTime = this.closingTime + duration.seconds(1);

    this.token = await MintableToken.new();   

  
    this.crowdsale = await FinalizableCrowdsale.new(rate, wallet, this.token.address, 0, this.openingTime, this.closingTime, cap);
    await this.crowdsale.addAddressToWhitelist(web3.eth.accounts[0])
    await this.crowdsale.addAddressToWhitelist(owner)
    await this.crowdsale.addAddressToWhitelist(wallet)
    await this.crowdsale.addAddressToWhitelist(thirdparty)


    await this.crowdsale.setUserCap(web3.eth.accounts[0], cap)
    await this.crowdsale.setUserCap(owner, cap)
    await this.crowdsale.setUserCap(wallet, cap)
    await this.crowdsale.setUserCap(thirdparty, cap)


    await this.token.transferOwnership(this.crowdsale.address);

  });

  it('cannot be finalized before ending', async function () {
    await expectThrow(this.crowdsale.finalize({ from: owner }), EVMRevert);
  });

  it('cannot be finalized by third party after ending', async function () {
    await increaseTimeTo(this.afterClosingTime);
    await expectThrow(this.crowdsale.finalize({ from: thirdparty }), EVMRevert);
  });

  it('can be finalized by owner after ending', async function () {
    await increaseTimeTo(this.afterClosingTime);
    await this.crowdsale.finalize({ from: owner });
  });

  it('cannot be finalized twice', async function () {
    await increaseTimeTo(this.afterClosingTime);
    await this.crowdsale.finalize({ from: owner });
    await expectThrow(this.crowdsale.finalize({ from: owner }), EVMRevert);
  });

  it('logs finalized', async function () {
    await increaseTimeTo(this.afterClosingTime);
    const { logs } = await this.crowdsale.finalize({ from: owner });
    const event = logs.find(e => e.event === 'Finalized');
    should.exist(event);
  });
});
