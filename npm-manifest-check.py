#!/usr/bin/env python3
import requests
import json
import time
from pprint import pprint
from deepdiff import DeepDiff

# https://www.npmjs.com/package/darcyclarke-manifest-pkg/v/2.1.15/index
# hex checksum = file name
# use hex to get *actual* manifest:
# https://www.npmjs.com/package/darcyclarke-manifest-pkg/file/a1c6250cb3f94bb3487c1bfb673d279642208b5db39a6c052a5c764f0d1abea5

def parse_manifest(pkg):
    # get and parse the manifest which contains the values reported on the frontend
    url = 'https://registry.npmjs.com/{}/'.format(pkg)
    parsed = json.loads(requests.get(url).text)

    # extract the interesting bits
    try:
        latest_ver = parsed['dist-tags']['latest']
    except KeyError:
        print(f'Failed to find latest version for {pkg} - might have been unpublished?')
        return None, None, None, None
    latest_manifest = parsed['versions'][latest_ver]

    try:
        dependencies = latest_manifest['dependencies']
    except KeyError:
        dependencies = None
    try:
        scripts = latest_manifest['scripts']
    except KeyError:
        scripts = json.loads('{}')
    name = latest_manifest['name']

    return latest_ver, dependencies, scripts, name


def get_actual_manifest(pkg, ver):
    # get and parse the manifest as it would be installed
    # first, we need to find the package.json delivered with the package:
    index_url = 'https://www.npmjs.com/package/{}/v/{}/index'.format(pkg, ver)
    while True:
        try:
            index = json.loads(requests.get(index_url).text)
            break
        except json.decoder.JSONDecodeError:
            print('Failed to get index from webservice, retrying...')
            time.sleep(1)

    hexsum = index['files']['/package.json']['hex']
    manifest_url = 'https://www.npmjs.com/package/{}/file/{}'.format(pkg, hexsum)

    # Sometimes the webservice seems to respond with an empty json - so this kludge got made:
    while True:
        try:
            manifest = json.loads(requests.get(manifest_url).text)
            break
        except json.decoder.JSONDecodeError:
            print('Failed getting manifest JSON from webserver, retrying...')
            time.sleep(1)

    # now we can parse it
    version = manifest['version']
    try:
        dependencies = manifest['dependencies']
    except KeyError:
        dependencies = None
    try:
        scripts = manifest['scripts']
    except KeyError:
        scripts = json.loads('{}')
    name = manifest['name']

    return version, dependencies, scripts, name

def main():
    import sys
    mismatch = False
    pkg = sys.argv[1]
    reported_ver, reported_dependencies, reported_scripts, reported_name = parse_manifest(pkg)

    if reported_ver == None:
        sys.exit(2)
    actual_ver, actual_dependencies, actual_scripts, actual_name = get_actual_manifest(pkg, reported_ver)

    if actual_ver != reported_ver:
        mismatch = True
        print('Version mismatch for {}!'.format(pkg))
        print('Reported version: {}'.format(reported_ver))
        print('Actual version: {}'.format(actual_ver))

    if actual_dependencies != reported_dependencies:
        mismatch = True
        dep_diff = DeepDiff(reported_dependencies, actual_dependencies, verbose_level=2)

        print('Dependency mismatch detected for {}!'.format(pkg))
        pprint(dep_diff, indent=2)

    if actual_scripts != reported_scripts:
        mismatch = True
        scripts_diff = DeepDiff(reported_scripts, actual_scripts, verbose_level=2)

        print('Scripts mismatch detected for {}!'.format(pkg))
        pprint(scripts_diff, indent=2)

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
