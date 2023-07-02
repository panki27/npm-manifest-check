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

class colors:
   PURPLE = '\033[1;35;48m'
   CYAN = '\033[1;36;48m'
   BOLD = '\033[1;37;48m'
   BLUE = '\033[1;34;48m'
   GREEN = '\033[1;32;48m'
   YELLOW = '\033[1;33;48m'
   RED = '\033[1;31;48m'
   BLACK = '\033[1;30;48m'
   UNDERLINE = '\033[4;37;48m'
   END = '\033[1;37;0m'

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
        dependencies = json.loads('{}')
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
        dependencies = json.loads('{}')
    try:
        scripts = manifest['scripts']
    except KeyError:
        scripts = json.loads('{}')
    name = manifest['name']

    return Manifest(name, version, dependencies, scripts)

def compare_manifests(pkg, brief=False, color=False, recursive=False):
    mismatch = False
    if pkg.reported_manifest.version != pkg.actual_manifest.version:
        mismatch = True
        if color:
            print(colors.RED, end='')
        print('Version mismatch for {}!'.format(pkg.name))
        if color:
            print(colors.END, end='')
        if not brief:
            if color:
                print(colors.YELLOW, end='')
            print('Reported version: {}'.format(pkg.reported_manifest.version))
            print('Actual version:   {}'.format(pkg.actual_manifest.version))
            if color:
                print(colors.END, end='')

    if pkg.actual_manifest.dependencies != pkg.reported_manifest.dependencies:
        mismatch = True
        if color:
            print(colors.RED, end='')
        print('Dependency mismatch detected for {}!'.format(pkg.name))
        if color:
            print(colors.END, end='')

        if not brief:
            if color:
                print(colors.YELLOW, end='')
            dep_diff = DeepDiff(pkg.reported_manifest.dependencies, pkg.actual_manifest.dependencies, verbose_level=2)
            pprint(dep_diff, indent=2)
            if color:
                print(colors.END, end='')

    if pkg.actual_manifest.scripts != pkg.reported_manifest.scripts:
        mismatch = True
        if color:
            print(colors.RED, end='')
        print('Scripts mismatch detected for {}!'.format(pkg.name))
        if color:
            print(colors.END, end='')

        if not brief:
            if color:
                print(colors.YELLOW, end='')
            scripts_diff = DeepDiff(pkg.reported_manifest.scripts, pkg.actual_manifest.scripts, verbose_level=2)
            pprint(scripts_diff, indent=2)
            if color:
                print(colors.END, end='')

    if pkg.actual_manifest.name != pkg.reported_manifest.name:
        mismatch = True
        if color:
            print(colors.RED, end='')
        print('Name mismatch detected for {}!'.format(pkg.name))
        if color:
            print(colors.END, end='')

        if not brief:
            if color:
                print(colors.YELLOW, end='')
            print('Reported name: {}'.format(pkg.reported_manifest.name))
            print('Actual name:   {}'.format(pkg.actual_manifest.name))
            if color:
                print(colors.END, end='')

    if not mismatch:
        if color:
            print(colors.GREEN, end='')
        print('No mismatch detected for {}.'.format(pkg.name))
        if color:
            print(colors.END, end='')

    if recursive:
        for package in pkg.actual_manifest.dependencies:
            print('Recursive: {}'.format(package))
            mismatch = compare_manifests(Package(package), brief=brief, color=color, recursive=True) or mismatch

    return mismatch


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog='npm-manifest-check', description='Check NPM packages for manifest mismatches')
    parser.add_argument('-r', '--recursive', action='store_true', help='recursively check all dependencies for mismatches')
    parser.add_argument('-b', '--brief', action='store_true', help='do not show detailed comparisons of mismatching values')
    parser.add_argument('-c', '--color', action='store_true', help='colorize the output')
    parser.add_argument('package', type=str, help='name of the NPM package')
    
    args = parser.parse_args()
    package = Package(args.package)
    mismatching = compare_manifests(package, brief=args.brief, color=args.color, recursive=args.recursive)
    if mismatching:
        sys.exit(1)

if __name__ == '__main__':
    main()
