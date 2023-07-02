#!/usr/bin/env python3
import requests
import json
import time
from pprint import pprint
from deepdiff import DeepDiff

from dataclasses import dataclass

@dataclass
class Manifest:
    name: str
    version: str
    dependencies: dict
    scripts: dict

@dataclass
class Package:
    name: str
    reported_manifest: Manifest
    actual_manifest: Manifest

    def __init__(self, name: str):
        self.name = name
        self.reported_manifest = parse_manifest(name)
        self.actual_manifest = parse_actual_manifest(name, self.reported_manifest.version)

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
    
    return Manifest(name, latest_ver, dependencies, scripts)

def parse_actual_manifest(pkg, ver):
    # get and parse the manifest as it would be installed
    # first, we need to find the package.json delivered with the package:
    index_url = 'https://www.npmjs.com/package/{}/v/{}/index'.format(pkg, ver)
    while True:
        try:
            index = json.loads(requests.get(index_url).text)
            break
        except json.decoder.JSONDecodeError:
            print('Failed to get index from webservice, retrying...')
            time.sleep(5)

    hexsum = index['files']['/package.json']['hex']
    manifest_url = 'https://www.npmjs.com/package/{}/file/{}'.format(pkg, hexsum)

    # Sometimes the webservice seems to respond with an empty json - so this kludge got made:
    while True:
        try:
            manifest = json.loads(requests.get(manifest_url).text)
            break
        except json.decoder.JSONDecodeError:
            print('Failed getting manifest JSON from webserver, retrying...')
            time.sleep(5)

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

    return Manifest(name, version, dependencies, scripts)

def compare_manifests(pkg):
    if pkg.reported_manifest.version != pkg.actual_manifest.version:
        mismatch = True
        print('Version mismatch for {}!'.format(pkg.name))
        print('Reported version: {}'.format(pkg.reported_manifest.version))
        print('Actual version:   {}'.format(pkg.actual_manifest.version))

    if pkg.actual_manifest.dependencies != pkg.reported_manifest.dependencies:
        mismatch = True
        dep_diff = DeepDiff(pkg.reported_manifest.dependencies, pkg.actual_manifest.dependencies, verbose_level=2)

        print('Dependency mismatch detected for {}!'.format(pkg.name))
        pprint(dep_diff, indent=2)

    if pkg.actual_manifest.scripts != pkg.reported_manifest.scripts:
        mismatch = True
        scripts_diff = DeepDiff(pkg.reported_manifest.scripts, pkg.actual_manifest.scripts, verbose_level=2)

        print('Scripts mismatch detected for {}!'.format(pkg.name))
        pprint(scripts_diff, indent=2)

    if pkg.actual_manifest.name != pkg.reported_manifest.name:
        mismatch = True
        print('Name mismatch detected for {}!'.format(pkg.name))
        print('Reported name: {}'.format(pkg.reported_manifest.name))
        print('Actual name:   {}'.format(pkg.actual_manifest.name))

    return mismatch


def main():
    import sys

    package_name = sys.argv[1]
    package = Package(package_name)
    mismatching = compare_manifests(package)
    if mismatching:
        sys.exit(1)

if __name__ == '__main__':
    main()
