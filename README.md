# PoSo code
This project implements the PoSo scheme on the integerated energy system (IES) in the University of Manchester. User can refer to https://github.com/kelpman05/DataUofManchester for the paramteters and dispatching results of IES. The settings of four scenarios are shown in paper "A blockchain consensus mechanism that uses Proof of Solution to optimize energy dispatch and trading". 

# Environment Configuration
- The project could only run in Windows OS.
- The project use GAMS to solve the optimization model. User should install GAMS and ensure that the solver "CONOPT4" is avaliable.
- The communication program is implemented by Python. Therfore, GAMS Python API should be configured. User can refer to https://www.gams.com/32/docs/API_PY_TUTORIAL.html for the API configureration.
- Before running the project, the user should replace `C:\Users\miller\Desktop\PoO\POO_scenario` with own local path in `POO_scenario\config.scenepoo.12xdual .bat` file.

# Files explanation
- The optimization program and KKT verification program is in `POO_scenario\distributed_consensus\scene\poo_solve.py`. 
- The configurations of delegates' dishonest behavior in four scenarios are in `POO_scenario\config.scenepoo.12xdual.yaml`. 
- The start-up file is `POO_scenario\config.scenepoo.12xdual .bat`.

# Experiment 
The configuration of four scenarios are in `POO_scenario\config.scenepoo.12xdual.yaml`. 
Nodes 8-12 correspond to delegates C-G. Nodes 8-12 will act as leader in sequence.  The "leader_evil" option represents whether the delegate is dishonest. For the leader, "folower_ignore" option defines the nodes that the leader will not send message. "follower_error" option defines the nodes that the leader will send non-optimal message. For delegates, "follower_trick_ignore" option defines the nodes that the delegate will not send message. The "follower_trick_error" option defines the nodes that the delgegate will send non-optimal message. Take scenario 1 for example. Leader C sends the non-optimal message only to delegate F but not others. Delegate F does not send any message to other followers. The "leader_evil" options of node 8 and node 11 are actived. The "follower_ignore" option of node 8 is configured as [9,10,12]. The "follower_error" option of node 8 is [8,11]. The follower_trick_error of node 11 is set as [9,10,12]. Finally, run `config.scenepoo.12xdual.bat` and five windows that represent nodes 8-12 will be opened. The communication records of five delegates are shown in the widows. 

The communication message among delegates are stored in path `POO_scenario\tests\ptry\delegate` as "Optimization_data" and "dual_data". The name of the files represents the communication path of the message. Take file `Optimization_data_Node12_9via10_5facba2b8cfd27ec67edb895785da837` for example. "Optimization_data" represents that this file records the optimization message. "Node12" represents that the message is received by Node 12. "9via10" represents that this message is the one that node 9 forwards to node 10. Therefore, the message corresponds to the <$744>DE in paper "A blockchain consensus mechanism that uses Proof of Solution to optimize energy dispatch and trading", Table 3, Scenario I, Phase for delegates (Leader is D), row G, column R2.

# Credits
This package was created with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
