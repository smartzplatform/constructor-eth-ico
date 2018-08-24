const { advanceBlock } = require('../../node_modules/zeppelin-solidity/test/helpers/advanceToBlock');
const { increaseTimeTo, duration } = require('../../node_modules/zeppelin-solidity/test/helpers/increaseTime');
const { latestTime } = require('../../node_modules/zeppelin-solidity/test/helpers/latestTime');
const { expectThrow } = require('../../node_modules/zeppelin-solidity/test/helpers/expectThrow');
const { EVMRevert } = require('../../node_modules/zeppelin-solidity/test/helpers/EVMRevert');
const { ether } = require('../../node_modules/zeppelin-solidity/test/helpers/ether');


const BigNumber = web3.BigNumber;

const should = require('chai')
  .use(require('chai-bignumber')(BigNumber))
  .should();

const NonBurnableICO = artifacts.require('ICO');
const BurnableICO = artifacts.require('BurnableICO');

// const MintableToken = artifacts.require('SimpleToken');
const SimpleToken = artifacts.require('SimpleToken');


contract('FinalizeICO', function ([_, owner, wallet, thirdparty, investor]) {
  const rate = 1;
  const cap = ether(10000);
  const value = ether(42);
  const tokenSupply = new BigNumber('1e22');

 
  
  describe('using burnable ico', function () {    
    
    
    beforeEach(async function () {
      await advanceBlock();

      this.openingTime = (await latestTime()+ duration.weeks(1));
      this.closingTime = this.openingTime + duration.weeks(1);
      this.afterClosingTime = this.closingTime + duration.seconds(1);
      this.token =  await SimpleToken.new();
      
      this.crowdsale = await BurnableICO.new(rate, wallet, this.token.address, 1, this.openingTime, this.closingTime, cap, {from: owner});
      
      await this.crowdsale.addAddressesToWhitelist([web3.eth.accounts[0], owner, wallet, thirdparty, investor], {from: owner});
      await this.crowdsale.setGroupCap([web3.eth.accounts[0], owner, wallet, thirdparty, investor], cap, {from: owner});    
      
      await this.token.transfer(this.crowdsale.address, tokenSupply);
      
    }); 
    
    it('burn token after finalize', async function () {
      await increaseTimeTo(this.openingTime);
      
      await this.crowdsale.sendTransaction({ value: value, from: investor });
      balancePre =  await this.token.balanceOf(this.crowdsale.address);
      balancePre.should.be.bignumber.equal(tokenSupply - value);
      
      await increaseTimeTo(this.afterClosingTime);    
      
      await this.crowdsale.finalize({ from: owner });
      balanceAfter = await this.token.balanceOf(this.crowdsale.address);
      balanceAfter.should.be.bignumber.equal(0);      
      balanceFundsAfter = await this.token.balanceOf(wallet);
      balanceFundsAfter.should.be.bignumber.equal(0)

    });
  });

  describe('using non burnable ico', function () {    
    
    
    beforeEach(async function () {
      await advanceBlock();
      this.openingTime = (await latestTime()+ duration.weeks(1));
      this.closingTime = this.openingTime + duration.weeks(1);
      this.afterClosingTime = this.closingTime + duration.seconds(1);
      this.token =  await SimpleToken.new();
      
      this.crowdsale = await NonBurnableICO.new(rate, wallet, this.token.address, 1, this.openingTime, this.closingTime, cap, {from: owner});
      
      await this.crowdsale.addAddressesToWhitelist([web3.eth.accounts[0], owner, wallet, thirdparty, investor], {from: owner});
      await this.crowdsale.setGroupCap([web3.eth.accounts[0], owner, wallet, thirdparty, investor], cap, {from: owner});    
      
      await this.token.transfer(this.crowdsale.address, tokenSupply);
      
    }); 
    
    it('transfer token after finalize', async function () {
      await increaseTimeTo(this.openingTime);
      
      await this.crowdsale.sendTransaction({ value: value, from: investor });
      balancePre =  await this.token.balanceOf(this.crowdsale.address);
      balancePre.should.be.bignumber.equal(tokenSupply - value);
      
      await increaseTimeTo(this.afterClosingTime);    
      
      await this.crowdsale.finalize({ from: owner });
      balanceAfter = await this.token.balanceOf(this.crowdsale.address);
      balanceAfter.should.be.bignumber.equal(0);      

      balanceFundsAfter = await this.token.balanceOf(wallet);
      balanceFundsAfter.should.be.bignumber.equal(balancePre)

      
    });
  });
  
});
