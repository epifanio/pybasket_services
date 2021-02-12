export DOMAIN=$1.metsis-api.met.no
export DOMAIN2=$2.metsis-api.met.no
docker stack rm $1
sleep 25
export NODE_ID=$(docker info -f '{{.Swarm.NodeID}}')
#if ["$1" == "swarmpit"]; then
#    docker node update --label-add swarmpit.db-data=true $NODE_ID
#    docker node update --label-add swarmpit.influx-data=true $NODE_ID
#else
#    export EMAIL=epiesasha@me.com
docker node update --label-add $1.$1-data=true $NODE_ID
#fi
sleep 5
docker stack deploy -c $1.yml $1
