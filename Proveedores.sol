pragma solidity ^0.4.24;

//import "./Owned.sol";

contract Proveedores{

  struct Provider {
    uint Price;
    uint index;
  }
  
  mapping(address => Provider) private Providers;
  address[] private ProviderIndex;

  mapping(address => int) private Scores;
  mapping(address => mapping(address => bool)) canRate;
  
  event LogNewProvider   (address indexed userAddress, uint index, uint maxPrice);
  event LogUpdateProvider(address indexed userAddress, uint index, uint maxPrice);
  event LogDeleteProvider(address indexed userAddress, uint index);
  event LogNewRate(address indexed Rated, int Score);
  
  function isProvider(address userAddress)
    public 
    constant
    returns(bool isIndeed) 
  {
    if(ProviderIndex.length == 0) return false;
    return (ProviderIndex[Providers[userAddress].index] == userAddress);
  }

  function newProvider(uint Price) 
    public
    returns(uint index)
  {
    if(isProvider(msg.sender)) revert(); 
    Providers[msg.sender].Price   = Price;
    Providers[msg.sender].index     = ProviderIndex.push(msg.sender)-1;
    emit 
        LogNewProvider(
        msg.sender, 
        Providers[msg.sender].index, 
        Price);
    return ProviderIndex.length-1;
  }

  function deleteProvider(address userAddress) 
    public
    returns(uint index)
  {
    if(!isProvider(userAddress)) revert(); 
    uint rowToDelete = Providers[userAddress].index;
    address keyToMove = ProviderIndex[ProviderIndex.length-1];
    ProviderIndex[rowToDelete] = keyToMove;
    Providers[keyToMove].index = rowToDelete; 
    ProviderIndex.length--;
    emit
    LogDeleteProvider(
        userAddress, 
        rowToDelete);
    emit
    LogUpdateProvider(
        keyToMove, 
        rowToDelete, 
        Providers[keyToMove].Price);
    return rowToDelete;
  }
  
  function getProvider(address userAddress)
    public 
    constant
    returns(uint maxPrice)
  {
    if(!isProvider(userAddress)) revert(); 
    return(
      Providers[userAddress].Price); 
      //Providers[userAddress].index);
  } 
  
  function updatePrice(uint newPrice) 
    public
    returns(bool success) 
  {
    if(!isProvider(msg.sender)) revert(); 
    Providers[msg.sender].Price = newPrice;
    emit
    LogUpdateProvider(
      msg.sender, 
      Providers[msg.sender].index,
      newPrice);
    return true;
  }

  function getProvidersCount() 
    public
    constant
    returns(uint count)
  {
    return ProviderIndex.length;
  }

  function getProviderAtIndex(uint index)
    public
    constant
    returns(address userAddress)
  {
    return ProviderIndex[index];
  }
  
  function getScore(address vendor)
    public
    constant
    returns(int score)
  {
    return Scores[vendor];
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
