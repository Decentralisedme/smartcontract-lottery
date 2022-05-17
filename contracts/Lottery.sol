// SPDX-License-Identifier: MIT
pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";

contract Lottery is VRFConsumerBase, Ownable {
    //  keep track of the players
    address payable[] public players;
    // Entre Fee variable
    uint256 public usdEntryFee;
    address payable public recentWinner;
    uint256 public randomness;
    // Chainlink to convert usd50 to eath with Price feed
    AggregatorV3Interface internal ethUsdPriceFeed;
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    LOTTERY_STATE public lottery_state;
    uint256 public fee;
    bytes32 public keyhash;
    // Events for in order to call randomness when Local
    event RequestedRandomness(bytes32 requestId);

    //  0
    //  1
    //  2

    constructor(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyhash
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        usdEntryFee = 50 * (10**18);
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED;
        fee = _fee;
        keyhash = _keyhash;
    }

    // Thnk the basic function you need: enter the lott / get entrance fee / start and end it
    function enter() public payable {
        // you can only enter if lottery is open
        require(lottery_state == LOTTERY_STATE.OPEN);
        //  $50 min
        require(msg.value >= getEntranceFee(), "Not enough ETH!");
        players.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();
        // make price a 1- uint256, 2- 18decimals (it comes with 8)
        uint256 adjustedPrice = uint256(price) * 10**10;
        // price in eth  = usd50/2000 >> 1 eth = usd2000
        //  50 * 10^18 /2000 >>> so 50 and 2000 has same numb of dec
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice;
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "You cannot start a new lottery yet!"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        // NON ACCETABLE
        // uint256(
        //     keccak256(
        //         abi.encodePacked(
        //             nonce,
        //             msg.sender,
        //             block.difficulty,
        //             block.timestamp
        //         )
        //     )
        // ) % players.lenght;
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;
        // we put the request of the randome number here
        bytes32 requestId = requestRandomness(keyhash, fee);
        // The following ReuestRand is from event above
        //  this event will be emitted when we call end lottery
        emit RequestedRandomness(requestId);
    }

    // here we put the callback function to get the number of our request
    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        //  we run 2 checks: on lottery and on the randome number
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "You re there yet!"
        );
        require(_randomness > 0, "random-not-found");
        //  now we need to slect the winner
        //  we have a list of payble public player [1,2,34,....]
        // We want to pick a random winner from that list
        // it is called modular function
        uint256 indexOfWinner = _randomness % players.length;
        recentWinner = players[indexOfWinner];
        recentWinner.transfer(address(this).balance);
        // Reset - list of payable playrs - change lottery state to CLOSED - keep track of the random numb

        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }
}
