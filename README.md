# mpc-auto-crop
Automatically crop MPC ready images (with bleed edge) to what it will look like as the final card.

## Installation and Usage
(Requires Python 3.8+)  

Create virtual environment and install dependencies
```
python3 -m venv .venv
.\.venv\Scripts\activate
pip install -r .\requirements.txt
```  
Create a directory called `input/` or specify an input directory as the first parameter that contains all the files you want to crop.
```
python .\mpc-auto-crop.py input 
```
Optionally specify an output directory:
```
python .\mpc-auto-crop.py input -o path/to/output/directory
```
