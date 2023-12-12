import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
import os
import time
import uproot

def run_command(command):
    #execute a shell command using subprocess.Popen
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #allows running a command in the shell and captures the stdout and stderr outputs 
    stdout, stderr = process.communicate()
    #printing an error statement if any of the commands do not run as expected with their error message
    if process.returncode != 0:
        print(f"Error executing {' '.join(command)}\nError message: {stderr.decode()}")
    else:
        #if the commands successful it prints the normal output you would expect
        print(stdout.decode())

#prepare environment function
def prepare_environment():
    print("Cleaning up Docker system...")
    #run the Docker command to remove unused data (like containers, networks, images)
    run_command("docker system prune -f")
    #this is done because at times if the system wasn't cleared docker would throw out errors to do with 
    #existing networks and cache

    print("Creating Docker network 'mit'...")
    #create a new Docker network named 'mit'. This network will be used to connect the containers
    run_command("docker network create mit")
    #sometimes system prune deletes the networks so this command is needed, sometimes it doesn't so an existing network
    #error might get thrown out but the program still runs as intended

    print("Removing existing files in 'sharer' directory...")
    #deletes all files in the 'sharer' directory to ensure a clean environment 
    run_command("del /f /q .\\sharer\\*")
    #useful for clearing all old files from past runs and making sure everything you see in the directory is from the current run

    print("Building Docker images without using cache...")
    #builds the docker images as defined in the docker-compose file, without using cache
    run_command("docker-compose build --no-cache")
    #ensures that the latest versions of images are used since sometimes docker runs past versions of the code through cache

def process_sample(sample, worker_beginning, worker_end, worker_id):
     #executes a docker container to process a specific sample of data
     #the docker container is run using docker-compose, and all the environment variables are set
    subprocess.run([
        #Run the service defined in the docker-compose.yml file and remove the container after it exits
        "docker-compose", "run", "--rm",
        "-e", f"SAMPLE={sample}", #pass the sample name as an environment variable
        "-e", f"WORKER_BEGINNING={worker_beginning}", #pass the beginning index of the batches as an environment variable
        "-e", f"WORKER_END={worker_end}", #pass the ending index of the worker batches
        "-e", f"WORKER_ID={worker_id}",  #pass the worker identification
        "reading" #specify the reading service to run as defined in the yml file
    ])

def run_plotting():
    #execute the plotting service using docker compose
    subprocess.run(["docker-compose", "run", "--rm", "plotting"])
    #the "--rm" flag makes sure that the container is removed after the plotting is complete

#for the problematic sample:
def calculate_extra_workers(workers):
    #here I determine the number of additional "pseudo" workers needed based on the total number of workers
    #through thorough testing from 1-9 workers this is the logic that works the best:
    #for 3-7 workers, increment by 1 for each pair
    #for more than 7 workers, the strategy changes to increment pseudo workers by 1 instead of at each pair
    if workers <= 7:
        return (workers - 1) // 2
    else:
        return workers - 4


def run_program(samples):
    #recording the starting time
    start_time = time.time()
    #asking user how many workers they would like to use
    try:
        workers = int(input("Enter the number of workers to use: "))
    except ValueError:
        #default is 2 if a number is not put in
        print("Invalid input. Using default 2 workers.")
        workers = 2

    #asks the user if they would like to wipe all data and build on no cache before running, makes sure theres no errors
    user_input = input("Do you want to prepare the environment (clearing all unused docker items and cache) before running the scripts? If this isn't done you might encounter docker memory or network issues (y/n): ").strip().lower()
    if user_input == 'y':
        prepare_environment()

    #define the path to the dataset and import necessary information from the infofile
    tuple_path = "https://atlas-opendata.web.cern.ch/atlas-opendata/samples/2020/4lep/"
    #gets the current script of the file
    current_script = os.path.dirname(os.path.realpath(__file__))
    #imports infofile from it
    sys.path.append(current_script)
    import infofile

    #creates a dictionary mapping each sample to its file path
    info_library = {sample: "Data/" if 'data' in sample else f"MC/mc_{infofile.infos[sample]['DSID']}." for sample in samples}

    #special handling for the problematic sample which at higher numbers takes a long time for the final worker to process its data 
    #specifically defining the problematic sample
    problem_sample = 'ggH125_ZZ4lep'
    

    #handling the processing of each sample with multiple workers:
    #ThreadPoolExectutor is used to manage a pool of threads and allow the data processing operations to run in parallel
    with ThreadPoolExecutor(max_workers=workers) as executor:
        #ensures no sequential processes are taking place even as it scales up with higher data sets
        #not particularly useful for this context but still provides optimisation and scalability potential
        #it allows for the parallel processing of the different data batches/segments
        for sample in samples:
            #construct the full path to each sample file
            path = os.path.join(tuple_path, info_library[sample] + sample + ".4lep.root")
            with uproot.open(path + ":mini") as tree:
                #determine the total number of entries in the current sample
                entries = tree.num_entries
                #adjusting the workload distribution for problematic samples
                if sample == problem_sample:
                    #extra distributions calculated:
                    extra_workers = calculate_extra_workers(workers)
                    #not needed if the workers are just 1 or 2
                    if workers > 2:
                        #adding the extra workers for that sample
                        loads = entries // (workers + extra_workers)
                    else:
                        #normal load distribution:
                        loads = entries // workers
                else:
                    #normal load distribution:
                    loads = entries // workers

                #increase batch size for the last worker to cover all the remaining entries 
                last_load_increase = entries % workers
                #distribute the data processing load across workers:
                for worker_index in range(workers):
                    worker_beginning = worker_index * loads
                    worker_end = worker_beginning + loads
                    #adjusts the end index for the last worker
                    if worker_index == workers - 1:
                        worker_end += last_load_increase

                    #if it's the problematic sample and the last worker, distribute the remainder
                    if sample == problem_sample and worker_index == workers - 1:
                        worker_end = entries  #makes sure the last worker covers everything remaining
                     #submit the data processing task to the executor
                     #the workerid is defined as worker_index+1
                    executor.submit(process_sample, sample, worker_beginning, worker_end, worker_index + 1) 
    #runs the plotting function only after all the reading has been completed, so then it can aggregate and the plot
    run_plotting()

    #simulating the processing time
    time.sleep(workers)  
    #getting the total time taken
    total_time = time.time() - start_time
    print(total_time)
    return 



if __name__ == "__main__":
    #defining the list of samples to be processed
    samples = ['data_A', 'data_B', 'data_C', 'data_D', 'Zee', 'Zmumu', 'ttbar_lep', 'llll', 'ggH125_ZZ4lep', 'VBFH125_ZZ4lep', 'WH125_ZZ4lep', 'ZH125_ZZ4lep']
    #running the program with those samples
    run_program(samples)

   

