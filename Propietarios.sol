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
