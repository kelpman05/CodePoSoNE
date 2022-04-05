# PoSo code
This repository includes the PoSo code and shows how PoSo can be used to enable energy dispatch for an integrated energy system (IES) at the University of Manchester. The parameters and dispatch results of the IES are available at https://github.com/kelpman05/DataUofManchester. Explanation of the code is available at our article:

Chen, S., Mi, H., Ping, J., Yan, Z., Shen, Z., Liu, X., Zhang, N., Xia, Q., Kang, C., (2022), A blockchain consensus mechanism that uses Proof of Solution to optimize energy dispatch and trading, Nature Energy, accepted in principle.
Please cite this article (refered to as PoSo article in the following text) if you want to cite the PoSo code.

# Environment Configuration
- The code must be run in Windows OS.
- The code uses GAMS to solve the optimization problem. Please install GAMS and solver "CONOPT4".
- The code for delegates to communicate messages is written in Python. Therefore, GAMS Python API should be configured. Please read https://www.gams.com/32/docs/API_PY_TUTORIAL.html for API configuration.
- Before running the code, please replace `C:\Users\miller\Desktop\PoO\POO_scenario` with your own local path in POO_scenario\config.scenepoo.12xdual .bat.

# File explanation
- The code about the optimization model and the associated optimality conditions are given in `POO_scenario\distributed_consensus\scene\poo_solve.py`. 
- The delegates' dishonest behaviors can be configured in `POO_scenario\config.scenepoo.12xdual.yaml`. 
- The start-up file is `POO_scenario\config.scenepoo.12xdual .bat`.

# Experiment 
The PoSo article demonstrates four scenarios when running the PoSo code (see Table 3 in the PoSo article). In `POO_scenario\config.scenepoo.12xdual.yaml`, nodes 8-12 refer to delegates C-G, who act as leaders in turns. The variable "leader_evil" defines whether a delegate is dishonest. A leader sends non-optimal messages to those followers defined as "follower_error", and does not send any message to those followers defined as "follower_ignore". A follower sends non-optimal messages to those delegates defined as "follower_trick_error", and does not send any message to those delegates defined as "follower_trick_ignore".
For example, in Scenario I, Leader C sends a non-optimal message to Follower F and does not send any message to others. Follower F does not send any message to others. Hence, the variables "leader_evil" of node 8 and node 11 are set as positive. The variable "follower_ignore" of node 8 is set as [9, 10, 12]. The variable "follower_error" of node 8 is set as [8, 11]. The variable "follower_trick_ignore" of node 11 is set as [9, 10, 12]. By running `config.scenepoo.12xdual.bat`, five windows respectively output the communication records of the five delegates.
The communication records among the five delegates are also stored in path `POO_scenario\tests\ptry\delegate` as "Optimization_data" and "dual_data". The names of the files represent the communication paths of messages. Take file `Optimization_data_Node12_9via10_5facba2b8cfd27ec67edb895785da837` for an example. "Optimization_data" means that this file records an optimal solution. "Node12" means that the message is stored by node 12. "9via10" means that node 9 sends the message to node 12 via node 10. Therefore, this file records "<$744>DE", in Row G, Column R2, Phase for delegates (Leader is D), Scenario I, table 3.

# Credits
This project is based on [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
