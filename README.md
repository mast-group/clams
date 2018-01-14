CLAMS
-----
CLAMS is an approach for mining API source code snippets that lies between snippet and sequence mining methods, which ensures lower complexity and thus could apply more readily to other languages.

This is an implementation of the API miner from our paper:

*Summarizing Software API Usage Examples using Clustering Techniques*

N. Katirtzis, T. Diamantopoulos, and C. Sutton. ETAPS/FASE 2018.

## Structure of the project
`main.py`: This is the main function of the project.

`/apisummariser`: Contains all the implementation files. The project is augmented with docstrings. Running `pydoc -p <PORT>` will reveal the documentation.

`/data`: Contains the dataset+examples and results for clams and other systems being used for the evaluation.

`/libs`: Contains any third-party libraries used in the implementation (excluding any Python libraries).

`/results`: The results of the system will be stored here.

`requirements.txt`: These are the dependencies on third-party Python libraries. 

## Installation Instructions

Cd to the project's directory:

```
cd clams
```

Install Java 8:
```
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer
```

Install/Configure [Anaconda 2](https://www.anaconda.com/download/#linux):
```
wget https://repo.continuum.io/archive/Anaconda2-4.2.0-Linux-x86_64.sh
bash Anaconda2-4.2.0-Linux-x86_64.sh -b -p ~/anaconda
rm Anaconda2-4.2.0-Linux-x86_64.sh

//replace <username with your username before running the following command>
echo 'export PATH="/home/<username>/anaconda/bin:$PATH' >> ~/.bashrc 
source .bashrc
conda update conda
conda config --add channels conda-forge
```

Install [Artistic Style formatter](http://astyle.sourceforge.net/):
```
mkdir libs/astyle
sudo apt-get install astyle
ln -s /usr/bin/astyle ./libs/astyle/astyle
```

Install [srcML](http://www.srcml.org/) (remove `-64` for 32 bit OS):
```
mkdir libs/srcml
wget http://131.123.42.38/lmcrs/beta/srcML-Ubuntu14.04-64.deb
sudo dpkg -i srcML-Ubuntu14.04-64.deb
rm srcML-Ubuntu14.04-64.deb
ln -s /usr/bin/srcml ./libs/srcml/srcml
```
Install python dependencies using `conda` and `requirements.txt`:
```
conda install --file requirements.txt
```

## How to run the application
You can run the application using the following command:

```
python main.py
```

The results will be stored in the `results` directory.
