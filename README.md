# npm manifest confusion checker

A `python` script to check `npm` packages for manifest mismatches, [as reported by Darcy Clarke.](https://blog.vlt.sh/blog/the-massive-hole-in-the-npm-ecosystem) Can also check all the dependencies of a package recursively.

## Usage

Install the requirements first:

```
pip install -r requirements.txt
```

Check the help:

```
./npm-manifest-check.py -h
usage: npm-manifest-check [-h] [-b] package

Check NPM packages for manifest mismatches

positional arguments:
  package      name of the NPM package

optional arguments:
  -h, --help   show this help message and exit
  -r, --recursive  recursively check all dependencies for mismatches
  -b, --brief  do not show detailed comparisons of mismatching values
  -c, --color  colorize the output
```

### Single package

To check a single package, pass the name of a package to the script as the first argument. Here, I'm using the package Darcy has helpfully provided:

```
$ ./npm-manifest-check.py darcyclarke-manifest-pkg
Version mismatch for darcyclarke-manifest-pkg!
Reported version: 2.1.15
Actual version:   3.0.0
Dependency mismatch detected for darcyclarke-manifest-pkg!
{'dictionary_item_added': {"root['sleepover']": '*'}}
Scripts mismatch detected for darcyclarke-manifest-pkg!
{ 'dictionary_item_added': { "root['install']": 'touch ./bad-pkg-write && echo '
                                                '"bad pkg exec!"\n'}}
Name mismatch detected for darcyclarke-manifest-pkg!
Reported name: darcyclarke-manifest-pkg
Actual name:   express
```

A 'good' package will look like this:

```
$ ./npm-manifest-check.py color
No mismatch detected for color.
```

### Multiple packages

`check_packages.sh` is a wrapper script which reads a list of packages to check from a `packages.list` file. Add the packages you want to check to this file, one package per line, and start the script:

```
./check_pages.sh
```

It will only report packages that have a mismatch.

You can use the following command to create a packages.list based on your lockfile.
```bash
npm ls --depth=0 --parseable | awk '{gsub(/\/.*\//,"",$1); print}'| sort -u  > packages.list
```
You could alter the `depth=0` variable to scan even deeper dependencies.

#### Output
You can use the `check_and_output_packages.sh` to output the results.
The default path will be _npm-manifest-check-results.json_ but can be changed by adding a name after the script.
It is also possible to change the output to a basic HTML or plain text.
```
./check_and_output_packages.sh -h
***
Usage: check_and_output_packages.sh [<name>] [--format=json|html|text] [--verbose]
***
```

### CI
To use the package in a CI pipeline, inspiration can be found in the following Gitlab pipeline snippet
```yaml
npm-manifest-check:
  stage: security
  image: python:3-alpine
  before_script:
    - git clone https://github.com/panki27/npm-manifest-check.git npm-manifest-check
    - cd npm-manifest-check
    - pip install -r requirements.txt
    - cd -
  script:
    - npm ls --depth=0 --parseable | awk '{gsub(/\/.*\//,"",$1); print}'| sort -u  > packages.list
    - sh ./npm-manifest-check/check_and_output_packages.sh
    - ls
  artifacts:
    reports:
      npmmanifestcheck: npm-manifest-check.json
    expire_in: 1 week
  dependencies: []
  rules:
    - if: '$NPM_MANIFEST_CHECK_DISABLED'
      when: never
    - if: $CI_COMMIT_BRANCH
      exists:
        - '**/package.json'
```
