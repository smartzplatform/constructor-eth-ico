pragma solidity 0.4.24;

import "../ICO.sol";

contract BurnableICO is ICO {
    constructor(uint _rate, address _funds, address _token, uint _softcap,
        uint256 _openingTime,
        uint256 _closingTime,
        uint256 _cap) public ICO(_rate, _funds, _token, _softcap, _openingTime, _closingTime, _cap) {

    }

    function needBurn() internal pure returns (bool) {
        return  true;
    }



}