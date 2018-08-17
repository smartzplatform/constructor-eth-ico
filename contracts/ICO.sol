pragma solidity 0.4.24;

import "zeppelin-solidity/contracts/crowdsale/Crowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/validation/WhitelistedCrowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/emission/MintedCrowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/validation/IndividuallyCappedCrowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/validation/TimedCrowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/validation/CappedCrowdsale.sol";
import "zeppelin-solidity/contracts/crowdsale/distribution/FinalizableCrowdsale.sol";
import "zeppelin-solidity/contracts/token/ERC20/BurnableToken.sol";
import "zeppelin-solidity/contracts/token/ERC20/ERC20.sol";


contract CappedIco is CappedCrowdsale {
    /**
    * @dev Extend parent behavior requiring purchase to respect the funding cap.
    * @param _beneficiary Token purchaser
    * @param _weiAmount Amount of wei contributed
    */
    function cappedPreValidatePurchase(
        address _beneficiary,
        uint256 _weiAmount
    ) internal {
        super._preValidatePurchase(_beneficiary, _weiAmount);
    }
}


contract TimedIco is TimedCrowdsale {
    /**
    * @dev Extend parent behavior requiring to be within contributing period
    * @param _beneficiary Token purchaser
    * @param _weiAmount Amount of wei contributed
    */
    function timedPreValidatePurchase(
        address _beneficiary,
        uint256 _weiAmount
    ) internal {
        super._preValidatePurchase(_beneficiary, _weiAmount);
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
    ) internal {
        super._preValidatePurchase(_beneficiary, _weiAmount);   
    }

    /**
    * @dev Extend parent behavior to update user contributions
    * @param _beneficiary Token purchaser
    * @param _weiAmount Amount of wei contributed
    */
    function  individuallyCappedUpdatePurchasingState(
        address _beneficiary,
        uint256 _weiAmount
    ) internal {
        super._updatePurchasingState(_beneficiary, _weiAmount);   
    }
}


contract MintedIco is MintedCrowdsale {
    /**
    * @dev Overrides delivery by minting tokens upon purchase.
    * @param _beneficiary Token purchaser
    * @param _tokenAmount Number of tokens to be minted
    */
    function mintedDeliverTokens(
        address _beneficiary,
        uint256 _tokenAmount
    ) internal {
        super._deliverTokens(_beneficiary, _tokenAmount);
    }
}


contract WhitelistedIco is WhitelistedCrowdsale {
    function whitelistedPreValidatePurchase(
        address _beneficiary,
        uint256 _weiAmount
    ) internal {
        super._preValidatePurchase(_beneficiary, _weiAmount);
    }
}


/// @title ICO
contract ICO is WhitelistedIco, MintedIco, TimedIco, CappedIco, IndividuallyCappedIco, FinalizableCrowdsale {

    function ICO() public
    Crowdsale(C_RATE, C_FUNDS, ERC20(C_TOKEN)) {}

    uint constant C_RATE = 1;
    address constant C_FUNDS = 1;
    address constant C_TOKEN = 1;

    function setNextSale(address sale) public onlyOwner {
        require(hasClosed(), "crowdsale has not been closed before setup next sale");
        // Could be called only once
        require(mNextSale == address(0), "Next sale must set once");

        mNextSale = sale;
    }

    function _preValidatePurchase(
        address _beneficiary,
        uint256 _weiAmount)  internal {
        whitelistedPreValidatePurchase(_beneficiary, _weiAmount);
        individuallyCappedPreValidatePurchase(_beneficiary, _weiAmount);
        timedPreValidatePurchase(_beneficiary, _weiAmount);
        cappedPreValidatePurchase(_beneficiary, _weiAmount);
    }

    function _updatePurchasingState(
        address _beneficiary,
        uint256 _weiAmount
    ) internal {
        individuallyCappedUpdatePurchasingState(_beneficiary, _weiAmount);      
    }

    function _deliverTokens(  
        address _beneficiary,
        uint256 _tokenAmount
    ) internal {
        super._deliverTokens(_beneficiary, _tokenAmount);
        mintedDeliverTokens(_beneficiary, _tokenAmount);
    }

    function finalization() internal {
        processRemainingTokens();
    }

    function processRemainingTokens() internal {
        uint currentBalance = token.balanceOf(address(this));
        if (0 == currentBalance)
            return;

        if (hasNextSale()) {
            assert(mNextSale != address(0));

            token.transfer(mNextSale, currentBalance);
        } else {
            // Burn all remaining tokens
            BurnableToken(address(token)).burn(currentBalance);            
        }
    }

    function hasNextSale() internal pure returns (bool) {
        return true;
    }

    address mNextSale = address(0);

}
    
