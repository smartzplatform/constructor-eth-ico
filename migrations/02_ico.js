var ICO = artifacts.require("ICOConstructor");

module.exports = function(deployer) {
  // Deploy the Migrations contract as our only task
  deployer.deploy(ICO);
};
