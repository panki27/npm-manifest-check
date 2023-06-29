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
    scripts = parsed['versions'][latest_ver]['scripts']

    # extract number of dependencies
    print('latest version: {}'.format(latest_ver))
    return latest_ver, dependencies, scripts

def get_actual_manifest(pkg, ver):
    index_url = 'https://www.npmjs.com/package/' + pkg + '/v/' + ver + '/index'
    index = json.loads(requests.get(index_url).text)
    hexsum = index['files']['/package.json']['hex']
    print('hex checksum: {}'.format(hexsum))
    manifest_url = 'https://www.npmjs.com/package/{}/file/{}'.format(pkg, hexsum)
    manifest = json.loads(requests.get(manifest_url).text)
    dependencies = manifest['dependencies']
    scripts = manifest['scripts']
    return dependencies, scripts


 
def main():
    import sys
    pkg = sys.argv[1]
    manifest = get_registry_manifest(pkg)
    ver, reported_dependencies, reported_scripts = parse_manifest(manifest)
    actual_dependencies, actual_scripts = get_actual_manifest(pkg, ver)
    if actual_dependencies != reported_dependencies:
        print('Dependency mismatch detected for {}!'.format(pkg))
        print('Reported dependencies: {}'.format(reported_dependencies))
        print('Actual dependencies: {}'.format(actual_dependencies))
    else:
        print('No mismatch detected for {}.'.format(pkg))
    if actual_scripts != reported_scripts:
        print('Scripts mismatch detected for {}!'.format(pkg))
        print('Reported scripts: {}'.format(reported_scripts))
        print('Actual scripts: {}'.format(actual_scripts))


if __name__ == '__main__':
    main()
