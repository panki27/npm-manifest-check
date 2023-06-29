#!/usr/bin/env python3
import requests
import json

# hex checksum = file name
# https://www.npmjs.com/package/darcyclarke-manifest-pkg/v/2.1.15/index
# use hex to get *actual* manifest:
# https://www.npmjs.com/package/darcyclarke-manifest-pkg/file/a1c6250cb3f94bb3487c1bfb673d279642208b5db39a6c052a5c764f0d1abea5

def parse_manifest(pkg):
    # get and parse the manifest which contains the values reported on the frontend
    url = 'https://registry.npmjs.com/' + pkg + '/'
    parsed = json.loads(requests.get(url).text)

    # extract the interesting bits
    latest_ver = parsed['dist-tags']['latest']
    latest_manifest = parsed['versions'][latest_ver]

    dependencies = parsed['versions'][latest_ver]['dependencies']
    scripts = parsed['versions'][latest_ver]['scripts']
    name = parsed['versions'][latest_ver]['name']

    return latest_ver, dependencies, scripts, name


def get_actual_manifest(pkg, ver):
    # get and parse the manifest as it would be installed
    index_url = 'https://www.npmjs.com/package/' + pkg + '/v/' + ver + '/index'
    index = json.loads(requests.get(index_url).text)
    hexsum = index['files']['/package.json']['hex']
    manifest_url = 'https://www.npmjs.com/package/{}/file/{}'.format(pkg, hexsum)

    manifest = json.loads(requests.get(manifest_url).text)
    version = manifest['version']
    dependencies = manifest['dependencies']
    scripts = manifest['scripts']
    name = manifest['name']

    return version, dependencies, scripts, name


def main():
    import sys
    mismatch = False
    pkg = sys.argv[1]
    #manifest = get_registry_manifest(pkg)
    reported_ver, reported_dependencies, reported_scripts, reported_name = parse_manifest(pkg)
    actual_ver, actual_dependencies, actual_scripts, actual_name = get_actual_manifest(pkg, reported_ver)

    if actual_ver != reported_ver:
        mismatch = True
        print('Version mismatch for {}!'.format(pkg))
        print('Reported version: {}'.format(reported_ver))
        print('Actual version: {}'.format(actual_ver))

    if actual_dependencies != reported_dependencies:
        mismatch = True
        print('Dependency mismatch detected for {}!'.format(pkg))
        print('Reported dependencies: {}'.format(reported_dependencies))
        print('Actual dependencies: {}'.format(actual_dependencies))

    if actual_scripts != reported_scripts:
        mismatch = True
        print('Scripts mismatch detected for {}!'.format(pkg))
        print('Reported scripts: {}'.format(reported_scripts))
        print('Actual scripts: {}'.format(actual_scripts))

    if actual_name != reported_name:
        mismatch = True
        print('Name mismatch detected for {}!'.format(pkg))
        print('Reported name: {}'.format(reported_name))
        print('Actual name: {}'.format(actual_name))

    if not mismatch:
        print('No mismatch detected for {}.'.format(pkg))
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
