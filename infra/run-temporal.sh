#!/bin/sh
set -eu
container_address=$(getent hosts "$(hostname)" | awk 'NR==1 {print $1}')
test -n "$container_address"
sed "s/__CONTAINER_IP__/$container_address/g" /run/temporal-template.yaml > /tmp/temporal.yaml
exec temporal-server --config-file /tmp/temporal.yaml --allow-no-auth start
