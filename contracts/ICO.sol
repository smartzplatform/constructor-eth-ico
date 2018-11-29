pragma solidity 0.4.24;

import "zeppelin-solidity/contracts/crowdsale/Crowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/validation/WhitelistedCrowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/emission/MintedCrowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/validation/IndividuallyCappedCrowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/validation/TimedCrowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/validation/CappedCrowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/distribution/FinalizableCrowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/distribution/RefundableCrowdsale.sol";
import "zeppelin-solidity/contracts/token/ERC20/BurnableToken.sol";
import "zeppelin-solidity/contracts/token/ERC20/ERC20.sol";
import "zeppelin-solidity/contracts/payment/RefundEscrow.sol";


// @title ICO
contract ICO is WhitelistedCrowdsale, TimedCrowdsale, CappedCrowdsale, IndividuallyCappedCrowdsale, FinalizableCrowdsale {

    constructor(uint _rate, address _funds, address _token, uint _softcap,
        uint256 _openingTime,
        uint256 _closingTime,
        uint256 _cap) public
        Crowdsale(_rate, _funds, ERC20(_token)) 
        CappedCrowdsale(_cap)
        TimedCrowdsale(_openingTime, _closingTime) {
        require(_softcap > 0);      

    
        mEscrow = new RefundEscrow(_funds);
        
        cSoftCap = _softcap;        

        _tokenRate.push(_rate);

        _rateChangeDates.push(_openingTime);

    }

    uint public cSoftCap;

    RefundEscrow public mEscrow;
    address public cFunds;

    uint constant  MIN_CONTRIBUTION = 0;


    function _preValidatePurchase(
        address _beneficiary,
        uint256 _weiAmount)  internal {

        super._preValidatePurchase(_beneficiary, _weiAmount);
        minContributionPreValidatePurchase(_beneficiary, _weiAmount);
    }

    function _updatePurchasingState(
        address _beneficiary,
        uint256 _weiAmount
    ) internal {
        super._updatePurchasingState(_beneficiary, _weiAmount);
    } 

    function finalization() internal {
        processRemainingTokens();
        super.finalization();
    }

    function minContributionPreValidatePurchase(
        address _beneficiary,
        uint256 _weiAmount
    ) pure internal {
        require(_weiAmount >= MIN_CONTRIBUTION);
    }

    function processRemainingTokens() internal {
        uint currentBalance = token.balanceOf(address(this));
        if (currentBalance != 0) {
           
            if (needBurn()) {
                BurnableToken(address(token)).burn(currentBalance);
            } else {
                token.transfer(mEscrow.beneficiary(), currentBalance);           
            }  
        } 

        if (goalReached()) {           
            
            mEscrow.close();
            mEscrow.beneficiaryWithdraw();
        } else {
            mEscrow.enableRefunds();
        }               
    }  

    function needBurn() internal pure returns (bool) {
        return  false;
    }

    /**
    * @dev Investors can claim refunds here if crowdsale is unsuccessful
    */
    function claimRefund() public {
        require(isFinalized);
        require(!goalReached());

        mEscrow.withdraw(msg.sender);
    }

    /**
    * @dev Checks whether funding goal was reached.
    * @return Whether funding goal was reached
    */
    function goalReached() public view returns (bool) {
        return weiRaised >= cSoftCap;
    }
   
  /**
   * @dev Overrides Crowdsale fund forwarding, sending funds to escrow.
   */
    function _forwardFunds() internal {
        mEscrow.deposit.value(msg.value)(msg.sender);
    }

    /**
   * @dev Override to extend the way in which ether is converted to tokens.
   * @param _weiAmount Value in wei to be converted into tokens
   * @return Number of tokens that can be purchased with the specified _weiAmount
   */
   
    function _getTokenAmount(uint256 _weiAmount)
        internal view returns (uint256)
    {

        return _weiAmount.mul(getRate());
    }

    function getRate() public onlyWhileOpen view returns (uint256)  {
        
        uint256 first = 0;
        uint256 last = _rateChangeDates.length - 1;
        uint256 i = 0;       


        while(first <= last) {            
            
            i = (last + first) / 2;        
            
         
            if (_rateChangeDates[i] > block.timestamp) {
                last = i - 1;
            } 
            if (_rateChangeDates[i] <= block.timestamp) {
                first = i + 1;
            }          

        }
        if (_rateChangeDates[i] > block.timestamp && i > 0) {
           i = i - 1;
        }         
       
        return _tokenRate[i];
        
    }

    /// @notice periods with token discount rate
    uint256[] public _rateChangeDates;

    /// @notice token rate per sale period
    uint256[] public _tokenRate;
}


contract MintedIco is ICO {
    constructor(uint _rate, address _funds, address _token, uint _softcap,
        uint256 _openingTime,
        uint256 _closingTime,
        uint256 _cap) public ICO(_rate, _funds, _token, _softcap, _openingTime, _closingTime, _cap) {

    }

    /**
    * @dev Overrides delivery by minting tokens upon purchase.
    * @param _beneficiary Token purchaser
    * @param _tokenAmount Number of tokens to be minted
    */   
    function _deliverTokens(  
        address _beneficiary,
        uint256 _tokenAmount
    ) internal {
        require(MintableToken(address(token)).mint(_beneficiary, _tokenAmount));
    }
}
    
