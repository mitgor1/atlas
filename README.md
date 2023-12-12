# ATLAS Analysis Program

A processing system which can analyse ATLAS data using cloud tools such as docker compose was developed. It can configure itself automatically with minimum human intervention except for specifying the amount of workers and preparing the correct directory. It performs the analysis processing in a distributed fashion using multiple nodes and generates plots for Higgs analysis as well as showing potential for scaling to larger systems and data sets.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Contact](#contact)


## Installation

Steps to install your project:
1. Clone the repo
2. Install Docker Desktop on your system
3. Ensure the directory is in the correct format and order as shown below:
`````
Docker/
├── Plotting/
│   ├── Dockerfile
│   └── plotting.py
├── Reading/
│   ├── Dockerfile
│   └── reading.py
├── Sharer/
│   └── [EMPTY]
├── docker-compose.yml
├── infofile.py
└── program.py
`````
## Usage

### Getting Started
You are now ready to run the application after successfully installing and configuring the project as described in the installation section. Make sure your directory structure matches the one in the repository.

### Running the Application
Start the application by typing the following command into your terminal:

```bash
python program.py
```
When you run this command, you will be asked to specify:

The number of workers the programme should execute per sample.
Whether the environment should be prepared before running the programme.

### Environment Preparation (Optional)

Preparing the environment is mainly optional except for the initial network creation. It involves deleting all unused docker containers, items, and networks; however, it is useful because you may encounter network issues if the correct network is not created, as well as other docker memory issues. The following are the commands executed by the programme to prepare the environment:

```bash
docker system prune -f
```
This is is done to avoid existing network, memory and cache errors.

```bash
docker network create mit
```
This is crucial as it is the network defined and used for the containers to connect and communicate in the programme.

```bash
del /f /q .\\sharer\\* 
```
This ensures the sharer directory is empty before the program runs.

```bash
docker-compose build --no-cache
```
Without using cache, this builds the docker images specified in the docker-compose file. This ensures that the most recent versions of images are used, as Docker occasionally runs older versions of code through the cache memory.


## Contact

Please contact if you have any questions or need more information:

- **Name:** Mit Gor
- **Email:** [qe20651@bristol.ac.uk](mailto:qe20651@bristol.ac.uk)

