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


contract CappedIco is CappedCrowdsale {
    /**
    * @dev Constructor, takes maximum amount of wei accepted in the crowdsale.
    * @param _cap Max amount of wei to be contributed
    */
    constructor(uint256 _cap) public CappedCrowdsale(_cap) { 

    }

    /**
    * @dev Extend parent behavior requiring purchase to respect the funding cap.
    * @param _beneficiary Token purchaser
    * @param _weiAmount Amount of wei contributed
    */
    function cappedPreValidatePurchase(
        address _beneficiary,
        uint256 _weiAmount
    ) view internal {
        require(weiRaised.add(_weiAmount) <= cap);
    }
}


contract TimedIco is TimedCrowdsale {
    constructor(uint256 _openingTime, uint256 _closingTime) public TimedCrowdsale(_openingTime, _closingTime) {

    }

    /**
    * @dev Extend parent behavior requiring to be within contributing period
    * @param _beneficiary Token purchaser
    * @param _weiAmount Amount of wei contributed
    */
    function timedPreValidatePurchase(
        address _beneficiary,
        uint256 _weiAmount
    ) view internal onlyWhileOpen {
      
    }

}


contract IndividuallyCappedIco is IndividuallyCappedCrowdsale {

    /**
    * @dev Extend parent behavior requiring purchase to respect the user's funding cap.
    * @param _beneficiary Token purchaser
    * @param _weiAmount Amount of wei contributed
    */
    function individuallyCappedPreValidatePurchase(
        address _beneficiary,
        uint256 _weiAmount
    ) view internal {        
        require(contributions[_beneficiary].add(_weiAmount) <= caps[_beneficiary]);
    }

    /**
    * @dev Extend parent behavior to update user contributions
    * @param _beneficiary Token purchaser
    * @param _weiAmount Amount of wei contributed
    */
    function individuallyCappedUpdatePurchasingState(
        address _beneficiary,
        uint256 _weiAmount
    ) internal {
        contributions[_beneficiary] = contributions[_beneficiary].add(_weiAmount);
    }
}


contract WhitelistedIco is WhitelistedCrowdsale {
    function whitelistedPreValidatePurchase(
        address _beneficiary,
        uint256 _weiAmount
    ) view internal onlyIfWhitelisted(_beneficiary) {
    }
}


/// @title ICO
contract ICO is WhitelistedIco, TimedIco, CappedIco, IndividuallyCappedIco, FinalizableCrowdsale {

    constructor(uint _rate, address _funds, address _token, uint _softcap,
        uint256 _openingTime,
        uint256 _closingTime,
        uint256 _cap) public
        Crowdsale(_rate, _funds, ERC20(_token)) 
        CappedIco(_cap)
        TimedIco(_openingTime, _closingTime) {
        require(_softcap > 0);      

    
        mEscrow = new RefundEscrow(_funds);
        
        cSoftCap = _softcap;          

    }

    uint public cSoftCap;

    RefundEscrow public mEscrow;
    address public cFunds;

    uint constant  MIN_CONTRIBUTION = 0;


    function _preValidatePurchase(
        address _beneficiary,
        uint256 _weiAmount)  internal {
        whitelistedPreValidatePurchase(_beneficiary, _weiAmount);
        individuallyCappedPreValidatePurchase(_beneficiary, _weiAmount); 
        timedPreValidatePurchase(_beneficiary, _weiAmount); 
        cappedPreValidatePurchase(_beneficiary, _weiAmount);
        minContributionPreValidatePurchase(_beneficiary, _weiAmount);
    }

    function _updatePurchasingState(
        address _beneficiary,
        uint256 _weiAmount
    ) internal {
        individuallyCappedUpdatePurchasingState(_beneficiary, _weiAmount);      
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
    
