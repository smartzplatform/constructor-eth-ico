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

contract('NextStageICO', function ([_, owner, wallet, thirdparty, investor]) {
  const rate = 1;
  const cap = ether(10000);
  const value = ether(42);



  before(async function () {
    // Advance to the next block to correctly read time in the solidity "now" function interpreted by ganache
    await advanceBlock();
  });

  beforeEach(async function () {
    this.openingTime = (await latestTime());
    this.closingTime = this.openingTime + duration.weeks(1);
    this.afterClosingTime = this.closingTime + duration.seconds(1);

    this.token = await MintableToken.new();   

  
    this.crowdsale = await FinalizableCrowdsale.new(rate, wallet, this.token.address, 1, this.openingTime, this.closingTime, cap, { from: owner });
    await this.crowdsale.addAddressToWhitelist(web3.eth.accounts[0],{ from: owner })
    await this.crowdsale.addAddressToWhitelist(owner,{ from: owner })
    await this.crowdsale.addAddressToWhitelist(wallet,{ from: owner })
    await this.crowdsale.addAddressToWhitelist(thirdparty, { from: owner })
    await this.crowdsale.addAddressToWhitelist(investor, { from: owner })


    await this.crowdsale.setUserCap(web3.eth.accounts[0], cap,{ from: owner })
    await this.crowdsale.setUserCap(owner, cap, { from: owner })
    await this.crowdsale.setUserCap(wallet, cap, { from: owner })
    await this.crowdsale.setUserCap(thirdparty, cap, { from: owner })
    await this.crowdsale.setUserCap(investor, cap, { from: owner })


    await this.token.transferOwnership(this.crowdsale.address);


  });

  it('move to next stage', async function () {
  //  console.log(await this.crowdsale.hasClosed())
    /* await this.crowdsale.sendTransaction({ value: value, from: investor });
    await increaseTimeTo(this.afterClosingTime);    
    await this.crowdsale.finalize({ from: owner });
    await this.crowdsale.setNextSale(thirdparty, {from: owner}) */
   // console.log(await this.token.getBalance(thirdparty));
  });

});
