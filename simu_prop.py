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
    address = '0xc493Fef24cC0E42Db3627a703dC756958a2Fa104',
    abi = Propietarios_interface['abi'],
)

i_first = 6
i_last = 10
i_demands = i_last - i_first + 1

reference_price = 2190000
min_price = int(reference_price*0.4)

#create offers
for i in range(i_first,i_last+1):
    acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    b_funding = bool(random.getrandbits(1))
    i_MaxPrice = random.randint(min_price,reference_price)
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

i_maxsteps = 100
i_step = 1
i_matched = 0

#behaviour
while ((i_matched < i_demands) and (i_step <= i_maxsteps)):
    print('step '+str(i_step))
    i_matched = 0
    for i in range(i_first,i_last+1):
        b_matched = propietarios.call().isDemand(public_keys[i])
        if b_matched == False:
            i_matched += 1
        elif ((b_matched == True) and ((i_step % 10) == 0)):
            #print('*Update Demand*')
            acct = w3.eth.account.privateKeyToAccount(private_keys[i])
            i_MaxPrice = random.randint(min_price,reference_price)
            construct_txn = propietarios.functions.updatemaxPrice(i_MaxPrice).buildTransaction({
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
for i in range(i_first,i_last+1):
    acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    construct_txn = propietarios.functions.deleteDemand(acct.address).buildTransaction({
        'from': acct.address,
        'nonce': w3.eth.getTransactionCount(acct.address),
        'gasPrice': w3.toWei('1', 'gwei')})
    signed = acct.signTransaction(construct_txn)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print('Gas used by Delete Demand = '+str(tx_receipt.gasUsed))

        

