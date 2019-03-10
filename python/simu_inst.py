import json
import web3
import pdb
import os

#from web3 import Web3
from web3 import Web3, HTTPProvider
from solc import compile_source
from web3.contract import ConciseContract

import pandas as pd
import time
import random

data = pd.read_csv("Llaves.csv") 

public_keys = data['Llave Publica']
private_keys = data['Llave Privada']

w3 = Web3(HTTPProvider("https://rinkeby.infura.io/v3/4c0ec7f1412a489d91e1934c66ebf5b1"))

# Solidity source code
Instaladores_source_code = '''
pragma solidity ^0.4.24;

//import "./Owned.sol";

contract Instaladores{

  struct Installer {
    uint Price;
    uint index;
  }
  
  mapping(address => Installer) private Installers;
  address[] private InstallerIndex;

  mapping(address => int) private Scores;
  mapping(address => mapping(address => bool)) canRate;
  
  event LogNewInstaller   (address indexed userAddress, uint index, uint maxPrice);
  event LogUpdateInstaller(address indexed userAddress, uint index, uint maxPrice);
  event LogDeleteInstaller(address indexed userAddress, uint index);
  event LogNewRate(address indexed Rated, int Score);
  
  function isInstaller(address userAddress)
    public 
    constant
    returns(bool isIndeed) 
  {
    if(InstallerIndex.length == 0) return false;
    return (InstallerIndex[Installers[userAddress].index] == userAddress);
  }

  function newInstaller(
    uint    Price) 
    public
    returns(uint index)
  {
    if(isInstaller(msg.sender)) revert(); 
    Installers[msg.sender].Price   = Price;
    Installers[msg.sender].index     = InstallerIndex.push(msg.sender)-1;
    emit 
        LogNewInstaller(
        msg.sender, 
        Installers[msg.sender].index, 
        Price);
    return InstallerIndex.length-1;
  }

  function deleteInstaller(address userAddress) 
    public
    returns(uint index)
  {
    if(!isInstaller(userAddress)) revert(); 
    uint rowToDelete = Installers[userAddress].index;
    address keyToMove = InstallerIndex[InstallerIndex.length-1];
    InstallerIndex[rowToDelete] = keyToMove;
    Installers[keyToMove].index = rowToDelete; 
    InstallerIndex.length--;
    Installers[userAddress].index = 0;
    emit
    LogDeleteInstaller(
        userAddress, 
        rowToDelete);
    emit
    LogUpdateInstaller(
        keyToMove, 
        rowToDelete, 
        Installers[keyToMove].Price);
    return rowToDelete;
  }
  
  function getInstaller(address userAddress)
    public 
    constant
    returns(uint maxPrice)
  {
    if(!isInstaller(userAddress)) revert(); 
    return(Installers[userAddress].Price);
      //Installers[userAddress].index);
  } 
  
  function updatePrice(uint newPrice) 
    public
    returns(bool success) 
  {
    if(!isInstaller(msg.sender)) revert(); 
    Installers[msg.sender].Price = newPrice;
    emit
    LogUpdateInstaller(
      msg.sender, 
      Installers[msg.sender].index,
      newPrice);
    return true;
  }

  function getInstallersCount() 
    public
    constant
    returns(uint count)
  {
    return InstallerIndex.length;
  }

  function getInstallerAtIndex(uint index)
    public
    constant
    returns(address userAddress)
  {
    return InstallerIndex[index];
  }

  function getScore(address installer)
    public
    constant
    returns(int score)
  {
    return Scores[installer];
  }

  function allowRating(
    address    rater, 
    address    rated) 
    public
    returns(bool success)
  {
    canRate[rater][rated] = true;
    return true;
  }
  
  function Rate(
    address    rated,
    int       score)
    public
    returns(bool success)
  {
    if (!canRate[msg.sender][rated]) revert();
    if (score < -1) revert();
    if (score > 1) revert();
    Scores[rated] += score;
    canRate[msg.sender][rated] = false;
    emit 
        LogNewRate(
        rated, 
        score);
    return true;
  }  

}

'''

Instaladores_compiled_sol = compile_source(Instaladores_source_code,  import_remappings=['=./', '-']) # Compiled source code
Instaladores_interface = Instaladores_compiled_sol['<stdin>:Instaladores']

instaladores = w3.eth.contract(
    address = '0xC0ed1D311963EFc99418C0C84Ff2661CF199f9b0',
    abi = Instaladores_interface['abi'],
)

# Solidity source code
CF_source_code = '''
pragma solidity ^0.4.24;

//import "./Owned.sol";
//import "./Propietarios.sol";
//import "./Proveedores.sol";
//import "./Instaladores.sol";
//import "./Gestores.sol";
import "./Proyectos.sol";
//import "./Coops.sol";



contract CF is Owned{

    address public beneficiary;
    address public vendor;
    address public installer;
    address public manager;

    uint public fundingGoal;
    uint public amountRaised;
    uint public deadline;
    uint numFunders = 0;
    mapping(address => uint256) public balanceOf;
    //mapping(uint => address) Funders;
    //mapping(uint => uint) Funds;
    address[] Funders;
    uint[] Funds;
    bool public fundingGoalReached = false;
    bool public crowdsaleClosed = true;

    event GoalReached(address recipient, uint totalAmountRaised);
    event FundTransfer(address backer, uint amount, bool isContribution);

    address Ccontract = 0x91c3010Caca9AC8817600AA2E53a8FAcde8e2bfd;
    address Ocontract = 0xc493Fef24cC0E42Db3627a703dC756958a2Fa104;
    address Vcontract = 0x88679873522CEEADC39A00187634B657625caF0e;
    address Icontract = 0x023C8ca441e2366d17D94255A37e1bB4b782e56e;
    address Mcontract = 0xe67Cc0C35E461Ad649859738f50598Bd6eb11595;
    address Pcontract = 0x5894A8300b7F9Ba8364DBba6Abb5CE0e29842545;

    Coops C = Coops(Ccontract);
    Propietarios O = Propietarios(Ocontract);
    Proveedores V = Proveedores(Vcontract);
    Instaladores I = Instaladores(Icontract);
    Gestores M = Gestores(Mcontract);
    Proyectos P = Proyectos(Pcontract);
    uint interest_rate = P.interest_rate();

    /**
     * Constructor function
     *
     * Setup the owner
     */

    function Crowdsale (
        address _holder,
        address _vendor,
        address _installer,
        address _manager,
        uint durationInMinutes
    )
      public onlyOwner{
        require(crowdsaleClosed);
        require(O.isDemand(_holder));
        if(!V.isProvider(_vendor)) revert();
        if(!I.isInstaller(_installer)) revert();
        if(!M.isManager(_manager)) revert();

        uint maxPrice = O.getDemand(_holder);
        //bool funding = O.getFunding(holder);
        uint vendorPrice = V.getProvider(_vendor);
        uint installerPrice = I.getInstaller(_installer);
        uint managerPrice = M.getManager(_manager);

        uint prevCost = vendorPrice + installerPrice + managerPrice;
        uint fee = prevCost * interest_rate / 100;
        uint totalCost = prevCost + fee;

        if(maxPrice <= totalCost) revert();

        beneficiary = _holder;
        vendor = _vendor;
        installer = _installer;
        manager = _manager;

        fundingGoal = totalCost;  //InERC20;
        deadline = now + durationInMinutes * 1 minutes;
        crowdsaleClosed = false;
        amountRaised = 0;
        //for (uint i = 0; i < numFunders; i++){
          //  balanceOf[Funders[i]] = 0;
        //}
        //numFunders = 0;
    }

    /**
     * Fallback function
     *
     * The function without name is the default function that is called whenever anyone sends funds to a contract
     */
    /*  DONATIONS IN ETHER
    function () payable public {
        require(!crowdsaleClosed);
        uint amount = msg.value;
        balanceOf[msg.sender] += amount;
        amountRaised += amount;
        emit FundTransfer(msg.sender, amount, true);
        //address(this);
    }*/

    function receiveFund
    (address _sender,
    uint256 _tokens,
    Coops _tokenContract)
    public{
      require(_tokenContract == C);
      require(!crowdsaleClosed);
      if(amountRaised > fundingGoal) revert();
      require(C.transferFrom(_sender, this, _tokens));
      balanceOf[_sender] += _tokens;
      amountRaised += _tokens;
      //Funders[numFunders] = _sender;
      //Funds[numFunders] = _tokens;
      Funders.push(_sender);
      Funds.push(_tokens);
      numFunders += 1;
      emit FundTransfer(msg.sender, _tokens, true);
    }

    modifier afterDeadline() { if (now >= deadline) _; }

    /**
     * Check if goal was reached
     *
     * Checks if the goal or time limit has been reached and ends the campaign
     */
    function checkGoalReached() public afterDeadline {
        //if (amountRaised >= fundingGoal){
        if (C.balanceOf(this) >= fundingGoal){
            fundingGoalReached = true;
            emit GoalReached(beneficiary, amountRaised);
        }
        crowdsaleClosed = true;
    }


    /**
     * Withdraw the funds
     *
     * Checks to see if goal or time limit has been reached, and if so, and the funding goal was reached,
     * sends the entire amount to the beneficiary. If goal was not reached, each contributor can withdraw
     * the amount they contributed.
     */
    function safeWithdrawal() public afterDeadline {
        if (!fundingGoalReached) {
            uint amount = balanceOf[msg.sender];
            balanceOf[msg.sender] = 0;
            if (amount > 0) {
                if (C.transfer(msg.sender, amount)){
                   emit FundTransfer(msg.sender, amount, false);
                } else {
                    balanceOf[msg.sender] = amount;
                }
            }
        }

        if (fundingGoalReached && beneficiary == msg.sender) {
            if (C.transfer(beneficiary, amountRaised)) {
               emit FundTransfer(beneficiary, amountRaised, false);
                for (uint i = 0; i < numFunders; i++){
                    balanceOf[Funders[i]] = 0;
                }
                P.Matching(beneficiary,
                    vendor,
                    installer,
                    manager);
                C.NewProject(beneficiary,
                    Funders,
                    Funds,
                    amountRaised);
            } else {
                //If we fail to send the funds to beneficiary, unlock funders balance
                fundingGoalReached = false;
            }
            //if (C.transfer(beneficiary, amountRaised)) revert();
        }
    }
}
'''

CF_compiled_sol = compile_source(CF_source_code,  import_remappings=['-']) # Compiled source code
CF_interface = CF_compiled_sol['<stdin>:CF']

cf = w3.eth.contract(
    address = '0x4Bac31B5056b1975D286d552F64F7962b8f2b2cc',
    abi = CF_interface['abi'],
)

i_first = 45
i_last = 64
i_demands = i_last - i_first + 1

reference_price = int(2190000*0.5)
min_price = int(reference_price*0.2)

#create offers
for i in range(i_first,i_last+1):
    acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    i_price_i = random.randint(min_price,reference_price)
    if instaladores.call().isInstaller(public_keys[i]) == False:
        print('NewInstaller('+str(i_price_i)+')')
        construct_txn = instaladores.functions.newInstaller(i_price_i).buildTransaction({
            'from': acct.address,
            'nonce': w3.eth.getTransactionCount(acct.address),
            'gasPrice': w3.toWei('1', 'gwei')})
        signed = acct.signTransaction(construct_txn)
        tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
        # Wait for the transaction to be mined, and get the transaction receipt
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        print('Gas used by New Installer = '+str(tx_receipt.gasUsed))

i_maxsteps = 10000
i_step = 1
i_matched = 0
i_checkgas = []

#behaviour
while ((i_matched < i_demands) and (i_step <= i_maxsteps)):
    print('step '+str(i_step))
    i_matched = 0
    for i in range(i_first,i_last+1):
        b_matched = instaladores.call().isInstaller(public_keys[i])
        if b_matched == False:
            i_matched += 1
        elif public_keys[i] == cf.call().installer():
            pass
        elif ((b_matched == True) and ((i_step % 200) == 0)):
            #print('*Update Demand*')
            acct = w3.eth.account.privateKeyToAccount(private_keys[i])
            i_price_i = random.randint(min_price,reference_price)
            construct_txn = instaladores.functions.updatePrice(i_price_i).buildTransaction({
                'from': acct.address,
                'nonce': w3.eth.getTransactionCount(acct.address),
                'gasPrice': w3.toWei('1', 'gwei')})
            signed = acct.signTransaction(construct_txn)
            tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
            tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
            i_checkgas.append(tx_receipt.gasUsed)
    print(i_matched)
    i_step += 1


tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)



#clear demands

for i in range(1,len(public_keys)):
    address = public_keys[i]
    #acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    if instaladores.call().isInstaller(public_keys[i]) == True:
        acct = w3.eth.account.privateKeyToAccount(private_keys[i])
        construct_txn = instaladores.functions.deleteInstaller(acct.address).buildTransaction({
            'from': acct.address,
            'nonce': w3.eth.getTransactionCount(acct.address),
            'gasPrice': w3.toWei('1', 'gwei')})
        signed = acct.signTransaction(construct_txn)
        tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        print('Gas used by Delete Demand = '+str(tx_receipt.gasUsed))


print(i_checkgas)
        
