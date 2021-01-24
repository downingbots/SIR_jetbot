# SIR_jetbot

This is SIRjetbot1. The SIR stands for Sharper Image Robot, which I purchased on
 clearance for less than $20. The 1 is because we bought 3 of them that worked.
 
This robot is an inexpensive platform to run DDQN reinforcement learning. However, 
the software is not specific to the Sharper Image Robot. In theory, it could easily
be generalized to many inexpensive RC toys with tracked or differential-drive wheels and 
an arm or crane or dozer or shovel. Just add a Jetson Nano, battery, and camera mounted
near the end of the arm/crane/shovel as described below. Contact me if interested.

The Sharper Image robot was hacked as followed:

    - Jetson Nano Developer Board with wifi
    - raspberry pi camera v2 with 2 ft cable mounted on a cookie wheel case near the end of the arm.
    - A hacked RC:
        - the inside of the low-end RC control that came with the robot. 
        - You can see/use the buttons here control the robot. 
        - the other side of the board was soldered to wire it up with the IO expansion board.
    - The IO expansion board was required :
        - the RC control uses Tri-state logic on 6 pins.
        - The expansion board uses I2C to communicate with the Jetson Development board
        - The expansion board is connected to the RC control via wires
    - It is powered by a mongo BONAI 5.6A battery pack
    - Logitech gamepad joystick

The code started with the Jetson Notebook tutorial on Obstacle avoidance, but was changed 
significantly. The Notebook tutorials barely ran on my Jetson with the wifi connectivity from my working area. The tutorials were replaced with:

    - The Logitech joystick controls the robot directly
    - The camera is streamed using much lower overhead video webserver for teleoperation.
    - The images are saved directly to the Robot SD card.
    - a poor-man's pwm changes the commands to start/stop up to every tenth of a second or so.
        -- takes the picture when stopped.  
        -- records the command sent by the joystick (lower or upper arm up/down, open/close gripper, etc.) along with the picture in the directory associated with the NN's command.
    
      This data is then gathered and used to train the robot. Note: a tenth of a second of start/stop proved too much for one of the boards and the robot will stop moving after a few minutes of continuous use. Eventually changed the pwm rate to two-moves-per-second.

The robot runs in 4 modes: RC telepresence, data-capture, and using trained neural net(s) including a single CNN, a multi-part sequence of CNNs, and DDQN reinforcement learning.  The data capture and neural net can be for a single alexnet NN, or a sequence of alexnet NNs with function-specific knowledge. For example, the 8-parts are for an HBRC phase-3 tabletop bot is:

    - get the arm to a known position
    - scans for object on the floor (or table)
    - goes to object, keeping object in center of vision
    - pick up the object
    - get the arm to a known position, while gripping object
    - scans for the box
    - goes to the box (keeping box in center of vision)
    - drops object in box
    - backs up and park arm (back to phase 1)

The #1 rule is no falling off the table (or going out-of-bounds).

The same training can be used for both a sequence of functional
NNs and for DDQN RL. A potential goal is to train NNs to different
functions (like above) and then combine the functions together in
different ways to perform different tasks. Then use DDQN to get
optimized end-to-end functionality.

REINFORCEMENT LEARNING ON REAL ROBOTS: Lessons Learned
------------------------------------------------------

I want to do Reinforcement Learning (RL) on real robots (specifically mobile manipulators with high-end hobbyist-grade hardware such as dynamixel MX-64 servos.) These robots cost less than a few thousand dollars. Such robots would be considered very low-end by university research robotics labs.

ROS is a good place to start with real robots, but you'll eventually hit the limits of what custom software can achieve.  Robot perception is still not solved and the best human-designed algorithms leave a lot to be desired.  My hope is that RL can adapt to handle low-end hardware and fill some of the intelligence void in robotics. Unfortunately, RL presents its own set of challenges.  I want to learn these challenges and try to solve subsets of these open-end research problems.

SIR_jetbot_the_first addresses several lessons learned the hard way.
  - Over time, I've become convinced that Robot Arms should have camera attached directly to the arm and use RL for digital servoing. SIR_jetbot1 does this with its only sensor - the RPi camera on its gripper (just below the "wrist").
  - SIR_jetbot1 does discrete moves to avoid realtime processing and also to handle low-end hardware limations (mcp23017 communication rate).
  - on-board Jetson is the most expensive component. Total price of the whole robot is a few hundred dollars.
  - Use imitation-learning to reduce amount of RL episodes that you have to run.
  
  There are many obstacles of doing RL on real robots:
 - number of episodes to tune RL (1000-100,000 on model-free). Solving problems like Open AI's DOTA, Deep Mind's Alpha-GO, Open AI's GTP3, etc. requires hundreds of thousands of dollars of computing power. We want to do realtime tuning of RL on a small scale. We want to be order of 10 training sessions or You-Only-Demo-Once.
 - Getting access to state information. Simulations provide the internal state of objects such as block locations so you can compute distance to block.
 - low-end hardware adds more complexity for repeatability

To solve the problem of getting the state of the environment that simulations can provide for free, you need other external mechanisms to evaluate real-world state:
  - OpenCV implementations to identify state (e.g., distance from line, location of block)
  - Separate cameras
  - add fiducials to objects (e.g., block) in environment
  - add sensors to objects in environment
  - Tons of human-interactons to reset the environment

Lessons from ROSwell:
  - Simulations don't match reality at all!  Spent a ton of time trying to get Gazebo physics engine to realistically model a light, top-heavy robot with low-end servos (e.g., dynamixel MX-64).
  - Problems encountered include incompatible upgrades of components
  - Difficulty tuning of weights, inertia, friction, pids, transmissions
  - Physics of torsional friction in gazebo is missing or unrealistic (depending on physics engine release)
  - Top-heavy robot might flip 10 feet into the air!
  - Lots of papers on needing different lighting, coloring, etc.
  - Might as well use no physics engine and assume perfect performance.

Lessons from Donkey-car:
  - Donkey car perfomance changed as it used up batteries. The RL doesn't adapt for this.
  - Continuous realtime RL is hard. On-board processing needs better performance for continuous realtime RL. On the other hand, Off-loaded processing to a laptop needs better communication performance for continuous realtime RL.
  - You do a lot of training but still overfits to environment, (fails at big DIY robocar events due to the addition of spectators or change in location.)  You need to train on many tracks, in many lighting conditions, with and without spectators, etc.

Lessons from REPLab:
  - Intel 3D Realsense camera gave poor results for any single 3D snapshot. Needed to accumulate and integrate results.  Worked around this by using OctoMaps, but this greatly reduces performance. Most RL implementations just use 2D camera, ignoring 2D camera capabilities.
  - Used ROS moveit to assume away much of the problem, only using RL for planning the final stage of grasping (e.g., lower straight down from above so only choosing final x/y and theta).
  - Frequent calibration between robot camera and arm. Simple calibration didn't do very well across robots or across runs on same robot due to overheating or stressing of motors (e.g., pushing down too hard on tray).
  - Pretrained imagenet models provide some transfer learning for regular cameras, but this doesn't help for 3D cameras.
  - Using OpenCV to evaluate state needed for RL is almost a difficult as solving the problem itself.  For example,identifying the blocks and stacking them can be made easier by adding fiducials pr sensors to blocks (blah)
  - Need to park arm so that it was away from tray so that state of objects on tray could be accurately assessed.

Lesson from using the Jetson nano:
  - The Jetson "notebook" is a cool idea for tutorials, but in practice needs very fast wifi - better than my house has and very fast SSD - faster than I bought.  But putting the gamepad/logitech on the robot and using lower overhead video webstreaming worked fine.

