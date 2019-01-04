import json
import web3
import ipdb
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
Propietarios_source_code = '''

pragma solidity ^0.4.24;

//import "./Owned.sol";

// ----------------------------------------------------------------------------
// Owned contract
// ----------------------------------------------------------------------------

contract Propietarios{

  struct Demand {
    uint maxPrice;
    bool Funding;
    uint index;
  }
  /*address Ccontract = 0x23e1bB98a277fd0e974bafC7bB31b5fBfC8CF358;
  Coops C = Coops(Ccontract);*/
  mapping(address => Demand) private Demands;
  address[] private DemandIndex;
  
  mapping(address => int) private Scores;
  mapping(address => mapping(address => bool)) canRate;

  event LogNewDemand   (address indexed userAddress, uint index, bool Funding, uint maxPrice);
  event LogUpdateDemand(address indexed userAddress, uint index, bool Funding, uint maxPrice);
  event LogDeleteDemand(address indexed userAddress, uint index);
  event LogNewRate(address indexed Rated, int Score);
  
  modifier onlyBy(address _account)
  {
    require(
        msg.sender == _account,
        "Sender not authorized."
    );
    // Do not forget the "_;"! It will
    // be replaced by the actual function
    // body when the modifier is used.
    _;
  }
  
  function isDemand(address userAddress)
    public 
    constant
    returns(bool isIndeed) 
  {
    if(DemandIndex.length == 0) return false;
    return (DemandIndex[Demands[userAddress].index] == userAddress);
  }

  function newDemand(
    bool    Funding, 
    uint    maxPrice) 
    public
    returns(uint index)
  {
    if(isDemand(msg.sender)) revert(); 
    Demands[msg.sender].Funding = Funding;
    Demands[msg.sender].maxPrice   = maxPrice;
    Demands[msg.sender].index     = DemandIndex.push(msg.sender)-1;
    emit 
        LogNewDemand(
        msg.sender, 
        Demands[msg.sender].index, 
        Funding, 
        maxPrice);
    return DemandIndex.length-1;
  }

  function deleteDemand(address userAddress) 
    public
    returns(uint index)
  {
    if(!isDemand(userAddress)) revert(); 
    uint rowToDelete = Demands[userAddress].index;
    address keyToMove = DemandIndex[DemandIndex.length-1];
    DemandIndex[rowToDelete] = keyToMove;
    Demands[keyToMove].index = rowToDelete; 
    DemandIndex.length--;
    Demands[userAddress].index = 0;
    emit
    LogDeleteDemand(
        userAddress, 
        rowToDelete);
    emit
    LogUpdateDemand(
        keyToMove, 
        rowToDelete, 
        Demands[keyToMove].Funding, 
        Demands[keyToMove].maxPrice);
    return rowToDelete;
  }
  
  function getDemand(address userAddress)
    public 
    constant
    returns(uint maxPrice)
  {
    if(!isDemand(userAddress)) revert(); 
    return(Demands[userAddress].maxPrice); 
      //Demands[userAddress].index);
  } 

  function getFunding(address userAddress)
    public 
    constant
    returns(bool Funding)
  {
    if(!isDemand(userAddress)) revert(); 
    return(Demands[userAddress].Funding); 
      //Demands[userAddress].index);
  } 
  
  function updateFunding(bool Funding) 
    public
    returns(bool success) 
  {
    if(!isDemand(msg.sender)) revert(); 
    Demands[msg.sender].Funding = Funding;
    emit
    LogUpdateDemand(
      msg.sender, 
      Demands[msg.sender].index,
      Funding, 
      Demands[msg.sender].maxPrice);
    return true;
  }
  
  function updatemaxPrice(uint maxPrice) 
    public
    returns(bool success) 
  {
    if(!isDemand(msg.sender)) revert(); 
    Demands[msg.sender].maxPrice = maxPrice;
    emit
    LogUpdateDemand(
      msg.sender, 
      Demands[msg.sender].index,
      Demands[msg.sender].Funding, 
      maxPrice);
    return true;
  }

  function getUserCount() 
    public
    constant
    returns(uint count)
  {
    return DemandIndex.length;
  }

  function getUserAtIndex(uint index)
    public
    constant
    returns(address userAddress)
  {
    return DemandIndex[index];
  }


  function getScore(address Owner)
    public
    constant
    returns(int score)
  {
    return Scores[Owner];
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

Propietarios_compiled_sol = compile_source(Propietarios_source_code,  import_remappings=['=./', '-']) # Compiled source code
Propietarios_interface = Propietarios_compiled_sol['<stdin>:Propietarios']

propietarios = w3.eth.contract(
    address = '0xD5fbF619121824aCB4e7aAf66A1d86947CE87f1B',
    abi = Propietarios_interface['abi'],
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
    address = '0x698a6Ef8C478eBcDE72b204C758F127Ac55CFc4F',
    abi = CF_interface['abi'],
)

i_first = 1
i_last = 8
i_demands = i_last - i_first + 1

reference_price = 2190000
min_price = int(reference_price*0.4)

#create offers
for i in range(i_first,i_last+1):
    acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    b_funding = bool(random.getrandbits(1))
    i_MaxPrice = reference_price #random.randint(min_price,reference_price)
    print('NewDemand('+str(b_funding)+', '+str(i_MaxPrice)+')')
    construct_txn = propietarios.functions.newDemand(b_funding,i_MaxPrice).buildTransaction({
        'from': acct.address,
        'nonce': w3.eth.getTransactionCount(acct.address),
        'gasPrice': w3.toWei('1', 'gwei')})

    signed = acct.signTransaction(construct_txn)

    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

    # Wait for the transaction to be mined, and get the transaction receipt
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print('Gas used by New Demand = '+str(tx_receipt.gasUsed))

i_maxsteps = 10000
i_step = 1
i_matched = 0

#behaviour
while ((i_matched < i_demands) and (i_step <= i_maxsteps)):
    print('step '+str(i_step))
    i_matched = 0
    for i in range(i_first,i_last+1):
        #print(public_keys[i])
        b_matched = propietarios.call().isDemand(public_keys[i])
        if b_matched == False:
            i_matched += 1
        elif b_matched == True:
            b_funding = propietarios.call().getFunding(public_keys[i]) 
            #cf.call().crowdsaleClosed()
            if  b_funding == True and cf.call().beneficiary() == public_keys[i]: 
                acct = w3.eth.account.privateKeyToAccount(private_keys[i])
                
                construct_txn = cf.functions.checkGoalReached().buildTransaction({
                    'from': acct.address,
                    'nonce': w3.eth.getTransactionCount(acct.address),
                    'gas': 3000000,
                    'gasPrice': w3.toWei('1', 'gwei')})
                
                signed = acct.signTransaction(construct_txn)
                tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
                tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)            
            
                if cf.call().crowdsaleClosed(): 
                    print('$$$$')
                    construct_txn = cf.functions.safeWithdrawal().buildTransaction({
                        'from': acct.address,
                        'nonce': w3.eth.getTransactionCount(acct.address),
                        'gasPrice': w3.toWei('1', 'gwei')})
                    signed = acct.signTransaction(construct_txn)
                    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
                    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
                    #print('Balance of '+acct.address+' = '+str(coops.call().balanceOf(acct.address))+ '  Coops')
                
            elif ((b_matched == True) and ((i_step % 100000) == 0)):
                #print('*Update Demand*')
                acct = w3.eth.account.privateKeyToAccount(private_keys[i])
                i_MaxPrice = random.randint(min_price,reference_price)
                b_funding = bool(random.getrandbits(1))
                construct_txn = propietarios.functions.updatemaxPrice(i_MaxPrice).buildTransaction({
                    'from': acct.address,
                    'nonce': w3.eth.getTransactionCount(acct.address),
                    'gasPrice': w3.toWei('1', 'gwei')})
                signed = acct.signTransaction(construct_txn)
                tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
                tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

                construct_txn = propietarios.functions.updateFunding(b_funding).buildTransaction({
                    'from': acct.address,
                    'nonce': w3.eth.getTransactionCount(acct.address),
                    'gasPrice': w3.toWei('1', 'gwei')})
                signed = acct.signTransaction(construct_txn)
                tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
                tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

    print(i_matched)
    i_step += 1


tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

#clear demands

for i in range(1,len(public_keys)):
    address = public_keys[i]
    #acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    if propietarios.call().isDemand(public_keys[i]) == True:
        acct = w3.eth.account.privateKeyToAccount(private_keys[i])
        construct_txn = propietarios.functions.deleteDemand(acct.address).buildTransaction({
            'from': acct.address,
            'nonce': w3.eth.getTransactionCount(acct.address),
            'gasPrice': w3.toWei('1', 'gwei')})
        signed = acct.signTransaction(construct_txn)
        tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        print('Gas used by Delete Demand = '+str(tx_receipt.gasUsed))
