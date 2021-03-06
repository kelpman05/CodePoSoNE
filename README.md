# PoSo code
- This repository includes the PoSo code and shows how PoSo can be used to enable energy dispatch for an integrated energy system (IES) at the University of Manchester. The parameters and dispatch results of the IES are available at https://github.com/kelpman05/DataUofManchester. Explanation of the PoSo algorithm is available at the following article. Please cite this article (refered to as PoSo article in the following text) if you want to cite the PoSo code.
- Chen, S., Mi, H., Ping, J., Yan, Z., Shen, Z., Liu, X., Zhang, N., Xia, Q., Kang, C., (2022), A blockchain consensus mechanism that uses Proof of Solution to optimize energy dispatch and trading, Nature Energy, https://doi.org/10.1038/s41560-022-01027-4.
- If you do not have institutional access to the PoSo article, please access the full article via https://rdcu.be/cPa8Z. Please feel free to publicly share this link.  
- Please contact Sijie Chen (sijie.chen AT sjtu.edu.cn) if you have any questions. 

# Environment Configuration
- The code must be run in Windows OS.
- The code uses GAMS to solve the optimization problem. Please install GAMS and solver "CONOPT4".
- The code for delegates to communicate messages is written in Python. Please install GAMS Python API. 
- Before running the code, please replace `C:\Users\miller\Desktop\PoO\POO_scenario` with your own local path in POO_scenario\config.scenepoo.12xdual .bat.

# Experiment 
The PoSo article demonstrates four scenarios when running the PoSo code (see Table 3 in the PoSo article). In `POO_scenario\config.scenepoo.12xdual.yaml`, nodes 8-12 act as leaders in turns. The variable "name" can be set as C, D, E, F, and G to represent different delegates. The variable "leader_evil" defines whether a delegate is dishonest. A dishonest leader sends non-optimal messages to those followers defined as "follower_error", and does not send any message to those followers defined as "follower_ignore". A dishonest follower sends non-optimal messages to those delegates defined as "follower_trick_error", and does not send any message to those delegates defined as "follower_trick_ignore".

For example, in Scenario 1, Leader C sends a non-optimal message to Follower F and does not send any message to others. Follower F does not send any message to others. The variables "name" of nodes 8-12 are set as C-G. Hence, the variables "leader_evil" of node C and node F are activated. The variable "follower_ignore" of node C is set as [9, 10, 12]. The variable "follower_error" of node C is set as [8, 11]. The variable "follower_trick_ignore" of node E is set as [9, 10, 12]. By running `config.scenepoo.12xdual.bat`, five windows respectively output the communication records of the five delegates.

The communication records among the five delegates are also stored in path `POO_scenario\tests\ptry\delegate` as "Optimization_data" and "dual_data". The names of the files represent the communication paths of messages. Take file `Optimization_data_NodeE_DviaGviaE_5facba2b8cfd27ec67edb895785da837.gdx` for an example. "Optimization_data" means that this file records an optimal solution. "NodeE" means that the message is stored by delegate E. "DviaGviaE" means that delegate D sends the message to delegate E via delegate G. Therefore, this file records "<$744>DG", in Row E, Column R2, Phase for delegates (Leader is D), Scenario 1, table 3.

# Credits
This project is based on [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
