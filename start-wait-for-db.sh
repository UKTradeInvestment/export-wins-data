#!/bin/bash -xe

until pg_isready -U postgres -h localhost; do sleep 1; done
sleep 2
until pg_isready -U postgres -h localhost; do sleep 1; done
./start.sh