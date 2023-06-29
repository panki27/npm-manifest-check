# npm manifest confusion checker

A `python` script to check `npm` packages for manifest mismatches, [as reported by Darcy Clarke.](https://blog.vlt.sh/blog/the-massive-hole-in-the-npm-ecosystem)

## Usage

Install the requirements first:

```
pip install -r requirements.txt
```

### Single package

To check a single package, pass the name of a package to the script as the first argument. Here, I'm using the package Darcy has helpfully provided:

```
$ ./npm-manifest-check.py darcyclarke-manifest-pkg
Version mismatch for darcyclarke-manifest-pkg!
Reported version: 2.1.15
Actual version: 3.0.0
Dependency mismatch detected for darcyclarke-manifest-pkg!
Reported dependencies: {}
Actual dependencies: {'sleepover': '*'}
Scripts mismatch detected for darcyclarke-manifest-pkg!
Reported scripts: {}
Actual scripts: {'install': 'touch ./bad-pkg-write && echo "bad pkg exec!"\n'}
Name mismatch detected for darcyclarke-manifest-pkg!
Reported name: darcyclarke-manifest-pkg
Actual name: express
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
