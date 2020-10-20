#!/bin/bash

#docker run -dit -v "C:\Users\sambe\Documents\regen\open-science\soc\src:/app/" --name soc soc-estimator
docker restart soc

# parse named argument options --tile, --config and --SAMPLES
while :; do
    case $1 in
        -d|--data_dir)
                if [ "$2" ]; then
                        DATA=$2
			echo "Data Directory : $DATA"
                        shift
                else
                        echo 'ERROR: "--data_dir" requires a non-empty option argument.'
                        exit 1
                fi
                ;;
        -c|--config)
                if [ "$2" ]; then
                        CONFIG=$2
			echo "Config File : $CONFIG"
                        shift
                else
                        echo 'ERROR: "--config" requires a non-empty option argument.'
                        exit 1
                fi
                ;;
        *)
                break
    esac

    shift
done

# copy config and SAMPLES into running container
if [ -d $DATA ]
then
      echo "Copying data directory"
      docker cp $DATA soc:data
else
      echo "Data directory invalid"
fi

if [ -z "$CONFIG" ]
then
      echo "No CONFIG file copied"
else
      echo "Copying config.yml file"
      docker cp $CONFIG soc:app/config.yml
fi

# execute pre-processing of the data product (tile or batch)
docker exec -it soc bash -c "python /app/soc_calc.py"

# copy output files/folders to host from s2-ard container
echo "Copying files from docker container"
docker cp soc:output $PWD

# remove files/folder from work and output directory on container
#docker exec soc-map sh -c 'rm -rf /output/* /work/*'

docker stop soc
