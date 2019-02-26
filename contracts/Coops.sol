pragma solidity ^0.4.24;

//import "./Owned.sol";
//import "./CrowdFunding.sol";

// ----------------------------------------------------------------------------
// 'Coops' token contract
//
// Deployed to : 0xdD870fA1b7C4700F2BD7f44238821C26f7392148
// Symbol      : Coops
// Name        : Coops Token
// Total supply: 1000000000
// Decimals    : 0
//
// Enjoy.
//
// (c) by Moritz Neto with BokkyPooBah / Bok Consulting Pty Ltd Au 2017. The MIT Licence.
// ----------------------------------------------------------------------------


// ----------------------------------------------------------------------------
// Safe maths
// ----------------------------------------------------------------------------
contract SafeMath {
    function safeAdd(uint a, uint b) public pure returns (uint c) {
        c = a + b;
        require(c >= a);
    }
    function safeSub(uint a, uint b) public pure returns (uint c) {
        require(b <= a);
        c = a - b;
    }
    function safeMul(uint a, uint b) public pure returns (uint c) {
        c = a * b;
        require(a == 0 || c / a == b);
    }
    function safeDiv(uint a, uint b) public pure returns (uint c) {
        require(b > 0);
        c = a / b;
    }
}


// ----------------------------------------------------------------------------
// ERC Token Standard #20 Interface
// https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20-token-standard.md
// ----------------------------------------------------------------------------
contract ERC20Interface {
    function totalSupply() public constant returns (uint);
    function balanceOf(address tokenOwner) public constant returns (uint balance);
    function allowance(address tokenOwner, address spender) public constant returns (uint remaining);
    function transfer(address to, uint tokens) public returns (bool success);
    function approve(address spender, uint tokens) public returns (bool success);
    function transferFrom(address from, address to, uint tokens) public returns (bool success);

    event Transfer(address indexed from, address indexed to, uint tokens);
    event Approval(address indexed tokenOwner, address indexed spender, uint tokens);
}


// ----------------------------------------------------------------------------
// Contract function to receive approval and execute function in one call
//
// Borrowed from MiniMeToken
// ----------------------------------------------------------------------------
contract ApproveAndCallFallBack {
    function receiveApproval(address from, uint256 tokens, address token, bytes data) public;
}

// ----------------------------------------------------------------------------
// Owned contract
// ----------------------------------------------------------------------------
contract Owned {
    address public owner;
    address public newOwner;

    event OwnershipTransferred(address indexed _from, address indexed _to);

    constructor() public {
        owner = msg.sender;
    }

    modifier onlyOwner {
        require(msg.sender == owner);
        _;
    }

    function transferOwnership(address _newOwner) public onlyOwner {
        newOwner = _newOwner;
    }
    function acceptOwnership() public {
        require(msg.sender == newOwner);
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
        newOwner = address(0);
    }
}

contract CrowdFunding is Owned{
    
    address public beneficiary;
    uint public fundingGoal;
    uint public amountRaised;
    uint public deadline;
    uint numFunders = 0;
    mapping(address => uint256) public balanceOf;
    //mapping(uint => address) Funders;
    //mapping(uint => uint) Funds;
    address[] Funders;
    uint[] Funds;
    bool fundingGoalReached = false;
    bool crowdsaleClosed = true;

    event GoalReached(address recipient, uint totalAmountRaised);
    event FundTransfer(address backer, uint amount, bool isContribution);
    
    address Ccontract = this;
    Coops C = Coops(Ccontract);

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

}




// ----------------------------------------------------------------------------
// ERC20 Token, with the addition of symbol, name and decimals and assisted
// token transfers
// ----------------------------------------------------------------------------



contract Coops is ERC20Interface, Owned, SafeMath {
    
    struct Project{
        address owner;
        address[] funders;
        uint[] amounts;
        uint totalPrice;
        uint ID;
    }
    
    
    string public symbol;
    string public  name;
    
    
    uint8 public decimals;
    uint public _totalSupply;
    
    uint public numProjects = 0;
    uint public kwh_price = 100;

    mapping(address => uint) balances;
    mapping(address => mapping(address => uint)) allowed;
    mapping(address => mapping(address => uint)) private Debts;
    mapping(address => uint) private totalDebts;
    mapping(uint => Project) private Projects; 

    // ------------------------------------------------------------------------
    // Constructor
    // ------------------------------------------------------------------------
    constructor() public {
        symbol = "Coops";
        name = "Coops Token";
        decimals = 0;
        _totalSupply = 1000000000;
        balances[owner] = _totalSupply;
        emit Transfer(address(0), owner, _totalSupply);
    }


    // ------------------------------------------------------------------------
    // Total supply
    // ------------------------------------------------------------------------
    function totalSupply() public constant returns (uint) {
        return _totalSupply  - balances[address(0)];
    }


    // ------------------------------------------------------------------------
    // Get the token balance for account tokenOwner
    // ------------------------------------------------------------------------
    function balanceOf(address tokenOwner) public constant returns (uint balance) {
        return balances[tokenOwner];
    }
    
    function getDebt(address debtor, address creditter) 
    public
    constant
    returns(uint debt)
    {
    return (Debts[debtor][creditter]);
    }
    
    function getTotalDebt(address debtor) 
    public
    constant
    returns(uint debt)
    {
    return (totalDebts[debtor]);
    }


    // ------------------------------------------------------------------------
    // Transfer the balance from token owner's account to to account
    // - Owner's account must have sufficient balance to transfer
    // - 0 value transfers are allowed
    // ------------------------------------------------------------------------
    function transfer(address to, uint tokens) public returns (bool success) {
        balances[msg.sender] = safeSub(balances[msg.sender], tokens);
        balances[to] = safeAdd(balances[to], tokens);
        emit Transfer(msg.sender, to, tokens);
        return true;
    }

    function Pay(address creditter, uint amount) 
    public
    returns(bool success) {
        balances[msg.sender] = safeSub(balances[msg.sender], amount);
        //Debts[debtor][creditter] -= amount;
        Debts[msg.sender][creditter] = safeSub(Debts[msg.sender][creditter],amount);
        //totalDebts[debtor] -= amount;
        totalDebts[msg.sender] = safeSub(totalDebts[msg.sender],amount);
        balances[creditter] = safeAdd(balances[creditter], amount);
        return true;
    } 

    // ------------------------------------------------------------------------
    // Token owner can approve for spender to transferFrom(...) tokens
    // from the token owner's account
    //
    // https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20-token-standard.md
    // recommends that there are no checks for the approval double-spend attack
    // as this should be implemented in user interfaces 
    // ------------------------------------------------------------------------
    function approve(address spender, uint tokens) public returns (bool success) {
        allowed[msg.sender][spender] = tokens;
        emit Approval(msg.sender, spender, tokens);
        return true;
    }
    
    function addDebt(address debtor, address creditter, uint amount) 
    public
    returns(bool success) 
  {
    //Debts[debtor][creditter] += amount;
    Debts[debtor][creditter] = safeAdd(Debts[debtor][creditter], amount);
    //totalDebts[debtor] += amount;
    totalDebts[debtor] = safeAdd(totalDebts[debtor], amount);
    return true;
  }


    // ------------------------------------------------------------------------
    // Transfer tokens from the from account to the to account
    // 
    // The calling account must already have sufficient tokens approve(...)-d
    // for spending from the from account and
    // - From account must have sufficient balance to transfer
    // - Spender must have sufficient allowance to transfer
    // - 0 value transfers are allowed
    // ------------------------------------------------------------------------
    function transferFrom(address from, address to, uint tokens) public returns (bool success) {
        balances[from] = safeSub(balances[from], tokens);
        allowed[from][msg.sender] = safeSub(allowed[from][msg.sender], tokens);
        balances[to] = safeAdd(balances[to], tokens);
        emit Transfer(from, to, tokens);
        return true;
    }

    // ------------------------------------------------------------------------
    // Returns the amount of tokens approved by the owner that can be
    // transferred to the spender's account
    // ------------------------------------------------------------------------
    function allowance(address tokenOwner, address spender) public constant returns (uint remaining) {
        return allowed[tokenOwner][spender];
    }


    // ------------------------------------------------------------------------
    // Token owner can approve for spender to transferFrom(...) tokens
    // from the token owner's account. The spender contract function
    // receiveApproval(...) is then executed
    // ------------------------------------------------------------------------
    /*function approveAndCall(address spender, uint tokens, bytes data) public returns (bool success) {
        allowed[msg.sender][spender] = tokens;
        emit Approval(msg.sender, spender, tokens);
        ApproveAndCallFallBack(spender).receiveApproval(msg.sender, tokens, this, data);
        return true;
    }*/
    function Fund(address spender, uint tokens) public returns (bool success) {
        require(balanceOf(msg.sender)>0);
        require(totalDebts[msg.sender]==0);
        allowed[msg.sender][spender] = tokens;
        emit Approval(msg.sender, spender, tokens);
        //ApproveAndCallFallBack(spender).receiveApproval(msg.sender, tokens, this, data);
        //CrowdFunding F = CrowdFunding(Fcontract)
        CrowdFunding(spender).receiveFund(
            msg.sender, 
            tokens, 
            this);
        return true;
    }


    // ------------------------------------------------------------------------
    // Don't accept ETH
    // ------------------------------------------------------------------------
    function () public payable {
        revert();
    }


    // ------------------------------------------------------------------------
    // Owner can transfer out any accidentally sent ERC20 tokens
    // ------------------------------------------------------------------------
    function transferAnyERC20Token(address tokenAddress, uint tokens) public onlyOwner returns (bool success) {
        return ERC20Interface(tokenAddress).transfer(owner, tokens);
    }
    
    // ------------------------------------------------------------------------
    // Projects
    // ------------------------------------------------------------------------
    function NewProject(
        address owner,
        address[] funders, 
        uint[] amounts, 
        uint totalPrice) 
        public {
        //require(canCreate[msg.sender] == true);
        //require(D.getTotalDebt(owner) == 0);
        Projects[numProjects].owner = owner;
        Projects[numProjects].funders = funders;
        Projects[numProjects].amounts = amounts;
        Projects[numProjects].totalPrice = totalPrice;
        Projects[numProjects].ID = numProjects;
        numProjects += 1;
    }
    
    function Generate(uint kwh, uint ID) 
      public 
      {
        require(Projects[ID].owner == msg.sender);
        uint amount = kwh*kwh_price;
        uint amount_i;
        for (uint i = 0; i < (Projects[ID].funders).length; i++){
          amount_i = amount*(Projects[ID].amounts[i])/(Projects[ID].totalPrice);
          addDebt(msg.sender, (Projects[ID].funders[i]), amount_i);
        }
    }
}
