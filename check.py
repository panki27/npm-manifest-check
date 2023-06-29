#!/usr/bin/env python3
import requests
import json

# hex checksum = file name
# https://www.npmjs.com/package/darcyclarke-manifest-pkg/v/2.1.15/index
# use hex to get *actual* manifest:
# https://www.npmjs.com/package/darcyclarke-manifest-pkg/file/a1c6250cb3f94bb3487c1bfb673d279642208b5db39a6c052a5c764f0d1abea5

def get_registry_manifest(pkg):
    url = 'https://registry.npmjs.com/' + pkg + '/'
    r = requests.get(url) 
    return(r.text)

def parse_manifest(manifest):
    # parse the manifest which represents the values from the frontend
    parsed = json.loads(manifest)

    # extract latest package version
    latest_ver = parsed['dist-tags']['latest']
    latest_manifest = parsed['versions'][latest_ver]

    dependencies = parsed['versions'][latest_ver]['dependencies']

    # extract number of dependencies
    print('latest version: {}'.format(latest_ver))
    return latest_ver, dependencies

def get_actual_manifest(pkg, ver):
    index_url = 'https://www.npmjs.com/package/' + pkg + '/v/' + ver + '/index'
    index = json.loads(requests.get(index_url).text)
    hexsum = index['files']['/package.json']['hex']
    print('hex checksum: {}'.format(hexsum))
    manifest_url = 'https://www.npmjs.com/package/{}/file/{}'.format(pkg, hexsum)
    manifest = json.loads(requests.get(manifest_url).text)
    dependencies = manifest['dependencies']
    return dependencies


 
def main():
    import sys
    pkg = sys.argv[1]
    manifest = get_registry_manifest(pkg)
    ver, reported_dependencies = parse_manifest(manifest)
    actual_dependencies = get_actual_manifest(pkg, ver)
    if actual_dependencies != reported_dependencies:
        print('Dependency mismatch detected for {}!'.format(pkg))
        print('Reported dependencies: {}'.format(reported_dependencies))
        print('Actual dependencies: {}'.format(actual_dependencies))
    else:
        print('No mismatch detected for {}.'.format(pkg))


if __name__ == '__main__':
    main()
