#plotting dockerfile


FROM python:latest

#working directory set
WORKDIR /mydir

#copying plotting script
COPY Plotting/plotting.py /mydir/


#installing the relevant packages needed
RUN pip install --no-cache-dir pandas uproot vector numpy pyarrow matplotlib fsspec awkward

#running the container
CMD ["python", "./plotting.py"]