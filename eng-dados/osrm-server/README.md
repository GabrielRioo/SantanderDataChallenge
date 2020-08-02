# Inicializar o servidor de rotas OSRM-SERVER

docker run -t -i -p 5000:5000 -v /mnt/WORKSPACE/SantanderDataChallenge/eng-dados/osrm-server/:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/sudeste-latest.osm.pbf

docker run -t -i -p 5000:5000 -v /mnt/WORKSPACE/SantanderDataChallenge/eng-dados/osrm-server/:/data osrm/osrm-backend osrm-partition /data/sudeste-latest.osrm

docker run -t -i -p 5000:5000 -v /mnt/WORKSPACE/SantanderDataChallenge/eng-dados/osrm-server/:/data osrm/osrm-backend osrm-customize /data/sudeste-latest.osrm