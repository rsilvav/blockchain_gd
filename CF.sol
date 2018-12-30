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
    
    address Ccontract = 0x3F5C926EC1BbDBD6C54DBdAAde5573D8e0205121;
    address Ocontract = 0xB1bE2Ba214d35Bcc8a52D1c0eE45C1be47AEb477;
    address Vcontract = 0x88679873522CEEADC39A00187634B657625caF0e;
    address Icontract = 0x023C8ca441e2366d17D94255A37e1bB4b782e56e;
    address Mcontract = 0xe67Cc0C35E461Ad649859738f50598Bd6eb11595;
    address Pcontract = 0xAFD6A7DB4Ef9A49B702a7f1aEE428dC6FFfe3941;
    
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
