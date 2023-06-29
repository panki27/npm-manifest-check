#!/bin/sh
#for pkg in $(cat packages.list); do 
while IFS= read -r pkg; do
  output="$(python3 npm-manifest-check.py "$pkg")";
  if [ $? -ne 0 ]; then
    echo "$output";
  fi
done < packages.list
