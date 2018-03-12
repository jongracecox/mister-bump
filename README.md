# Mister Bump

[![image](https://travis-ci.org/jongracecox/mister-bump.svg?branch=master)](https://travis-ci.org/jongracecox/mister-bump)

Supported versions: Python 2.6, 2.7, 3.5, 3.6.

## Introduction
`mister_bump` is a Python-based tool for handling version numbering in Git projects.
It can be used from within Python via import, or via the command line.

The idea is to automate the creation of version numbers within Git projects.  This can
be done by using the tool in a projects' CI/CD build pipeline.  

In order for the tool to work correctly you should use the versioning approach suggested
below.

## Installation

Installation can be done via `pip`.

```bash
pip install mister_bump
```

## Basic Usage

Once installed via pip, you can use the command line interface `get-git-version`, or `mister-bump`.

If you have downloaded the project source, you can call `mister_bump.py` using the
same syntax.

*Note: You must call the script from inside the root directory of the Git project you want the version for.*

Basic call with no arguments:

```
[08:18:39 user@localhost mister-bump]$ get-git-version 
1.0.0rc1
```

In the above call, the **next** version to be created will be `1.0.0rc1`.  So if
the Git project was pushed to master and the CI pipeline ran, the version used in CI
would be `1.0.0rc1`. 

The style can be changed to use `.dev` for development release (typically used as a post release version).

```
[08:19:16 user@localhost mister-bump]$ get-git-version --style .dev
1.0.0.dev1
```

It is possible to tell the script to **not** increment the detected version number.
This can be used for different versioning schemes.  For example, you may want to create
post release versions, rather than pre-release versions.

```
[08:19:24 user@localhost mister-bump]$ get-git-version --style .dev --no-increment
0.3.0.dev1
```

In this example the **last** version in Git is `0.3.0`, and the "deviation" (distance in commits)
is 1 - meaning that there has been one additional commit since that version. 

Verbose output can be obtained by passing the `--verbose` argument.

```
[08:19:31 user@localhost mister-bump]$ get-git-version --style rc --verbose
08:19:40 [mister_bump:308][DEBUG] Fetching all candidate upstream versions
08:19:40 [mister_bump:31][DEBUG] Getting current git version
08:19:40 [mister_bump:38][DEBUG] Command: git describe --match=release-* --abbrev=4
08:19:40 [mister_bump:312][DEBUG] Candidate versions: release-0.3.0-final-1-gc68c
08:19:40 [mister_bump:322][DEBUG] Comparing candidate release-0.3.0-final-1-gc68c
08:19:40 [mister_bump:141][DEBUG] Version type = final
08:19:40 [mister_bump:141][DEBUG] Version major = 0
08:19:40 [mister_bump:141][DEBUG] Version minor = 3
08:19:40 [mister_bump:141][DEBUG] Version bugfix = 0
08:19:40 [mister_bump:141][DEBUG] Version deviation = 1
08:19:40 [mister_bump:141][DEBUG] Version hash = 
08:19:40 [mister_bump:60][DEBUG] Current git branch is master
08:19:40 [mister_bump:86][DEBUG] Current branch is bugfix? False
08:19:40 [mister_bump:337][DEBUG] Version detected as "release-0.3.0-final-1-gc68c"
08:19:40 [mister_bump:267][DEBUG] Incrementing with MAJOR version increment.
08:19:40 [mister_bump:193][DEBUG] Formatted version is "1.0.0rc1"
1.0.0rc1

```

Help can be obtained using the `--help` argument.

```
[08:14:40 user@localhost mister-bump]$ get-git-version --help
usage: get-git-version [-h] [-v] [-s {rc,.dev}] [-n] [override]

Get appropriate project version number based on Git status.

positional arguments:
  override              Override version number. Must be in the format
                        "release-0.0.0-000-aaaaaa".

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose output.
  -s {rc,.dev}, --style {rc,.dev}
                        Style of suffix.
  -n, --no-increment    Do not increment version number.
```

## A Suggested Versioning Approach

This is one way to do versioning, and it is the way that this tool was designed to work with.
If you have a different versioning approach this tool may not work as expected.

### Pipeline Setup

Make sure the `mister_bump` package is installed where your CI pipeline will run.  This could be a case
of installing on a server, adding the package to a Docker image, or simply `pip` installing it
within the CI pipeline.

Normally you add versioning because you want to deploy something as part of your CI pipeline.
Set your pipeline up to perform deployment from the `master` branch (for release candidates),
and `release-*` branches (for releases).  You can optionally add deployment for `bugfix-*` branches
for bugfix release candidates.  Do not perform deployment on `release-*-final` branches
(more on that later), so add an exclusion for that too.

If your pipeline is running in GitLab CI then you can add this to your `.gitlab-ci.yml`:

```yaml
  only:
    - /^release-.*$/
    - master
    - /^bugfix-.*$/
  except:
    - /^release-.*-final$/
```

In your CI script you can get the version number into an environment variable using:

```bash
export VERSION=$(get-git-version --style rc)
echo "VERSION is $VERSION"
```

Use the `$VERSION` environment variable when creating artifacts.

### Starting out

When you first start version numbering on a project, there will be no tags, so the script
won't detect a "current" version.  In this instance it will always return `0.1.0rc1`.

You can either leave it like this, and accept that all release candidates will be created
with the same version number up until the first release, or you can create a new
`release-0.0.0` tag on the project, which will mean each commit will
result in a new version number:

* `0.1.0rc1`
* `0.1.0rc2`
* `0.1.0rc3`

If you set your CI pipeline to deploy on master updates then you will have new project
artifacts generated and deployed with each update to master.

*Note that the `N` in `rc<N>` indicates a distance (in commits)from the last release tag, so if
you merge multiple commits into master at the same time this will only result in one CI pipeline
running, and there will be gaps in the release candidate numbers*

* Create tag `release-0.0.0`
* Create dev branch `X`
  * Commit 1 (distance of 1 commit)
  * Commit 2 (distance of 2 commits)
  * Commit 3 (distance of 3 commits)
* Merge branch `X` into `master`
  * Master CI pipeline will create version `0.1.0rc3` (no `rc1` or `rc2`)

### Releasing a version

**TL;DR** - Create tag `release-X.Y.Z` pointing to master

Each master branch update will be a release candidate for the **next** release, so
`0.1.0rc3` is a *candidate* for the `0.1.0` release.  When you decide you are ready
to cut a release simply create a new tag on the project.

Assuming the last release candidate was `0.1.0rc3`, you would create a new tag called `release-0.1.0`.

In GitLab you can do this through the web UI by clicking Repository > Tags, then click
the green **New tag** button, type in `release-0.1.0`, and make sure `master` is selected
as the source branch.

Once the tag has been created, a new CI pipeline should run, and generate the artifacts for
your new release, with a version number of `0.1.0`.

All subsequent commits to master will now be tagged as `0.2.0rc<N>`, as they are
contributing towards the next release.

*NOTE: The tag names are key to how `mister_bump` works, so make sure you use the
correct format (`release-<major>.<minor>.<bugfix>`)* 

### Bugfixing

**TL;DR** - To fix `X.Y.Z` release create branch `bugfix-X.Y.Z` pointing to master,
 make changes, create tag `release-X.Y.Z+1`. Cherry-pick fixes to master.

This section explains how to fix a bug in a previous release.  In the examples we will assume
we have released `0.2.0` (i.e. there is a `release-0.2.0` tag).  

In this instance we will be working to produce a `0.2.1` bugfix release.  You should think
of `0.2.1` as a bugfix for `0.2.0`.

1. Create a branch called `bugfix-<release-you-want-to-fix>`.  In our example this is
 `bugfix-0.2.0`.
2. Develop your fix by committing to the bugfix branch.  As you go, each commit will result in
  a `0.2.1rc<N>` version if your CI is setup to deploy on bugfix branch.
3. Once your bugfix is ready to release create a tag for `release-0.2.1`, and base it on the
  bugfix branch.  This will cause a new `0.2.1` version to be created in CI.
4. Finally make sure all your fixes are **also** applied to master (either manually or via
  cherry-picking)

You should now have something that looks like this:

* Tag `release-0.2.0`
* Branch `bugfix-0.2.0`
  * Commit 1 (distance of 1 commit) - version = `0.2.1rc1`
  * Commit 2 (distance of 2 commits) - version = `0.2.1rc2`
  * Commit 3 (distance of 3 commits) - version = `0.2.1rc3`
  * Tag bugfix branch as `release-0.2.1` - version = `0.2.1`
* Cherry-pick commit 1 onto master
* Cherry-pick commit 2 onto master
* Cherry-pick commit 3 onto master

### Breaking change / Major release

**TL;DR** - To close release `X.Y.Z` and move to `X+1.0.0` create tag `release-X.Y.Z-final`
pointing to `release-X.Y.Z`.

Major release numbers are typically reserved for breaking changes.  When you need to make a
breaking change, or just want to switch to a new major release (maybe due to a significant change)
you need to "finalise" the current major version, so you can move onto the next.

Consider the following example:

Lets assume we have the following released versions.

* `0.1.0rc1`
* `0.1.0rc2`
* `0.1.0rc3`
* `0.1.0` (tag `release-0.1.0`)
* `0.2.0rc1`
* `0.2.0rc2`
* `0.2.0rc3`
* `0.2.0` (tag `release-0.2.0`)

If we carry on as normal, and start committing changes to master, the next versions would be
`0.3.0rc1`, `0.3.0rc2`, `0.3.0rc3`, etc.

Lets say we want to make a breaking change, and want to start work on `1.0.0`.  We need to
"close off" the `0` major release number, and move onto major version `1`.

To do this we need to create a `final` tag called `release-0.2.0-final`, pointing at `release-0.2.0`.

This `final` tag shouldn't be used to cut a release, since it should be pointing to the same
thing as the `release-0.2.0` tag.  It's just used to tell `mister_bump` that we have finished with
`0.X.X`, and we're ready to start `1.0.0`.

Continuing our earlier example, we would expect to see:

* `0.1.0rc1`
* `0.1.0rc2`
* `0.1.0rc3`
* `0.1.0` (tag `release-0.1.0`)
* `0.2.0rc1`
* `0.2.0rc2`
* `0.2.0rc3`
* `0.2.0` (tag `release-0.2.0`)
* Now we want to make a breaking change
* Tag `release-0.2.0-final`
* `1.0.0.rc1`
* `1.0.0.rc2`
* `1.0.0.rc3`
* `1.0.0` (tag `release-1.0.0`)
* `1.1.0rc1`
* `1.1.0rc2`
* `1.1.0rc3`
* `1.1.0` (tag `release-1.1.0`)

## Version numbers for Python packages

If you are using `mister-bump` to version a Python package, you can call the package directly from your `setup.py`.

```python
#!/usr/bin/python
from setuptools import setup
import mister_bump


setup(
    name='<your-package-bame>',
    description='<Your package description.>',
    version=mister_bump.bump(style='rc'),
    ...
    )
```

## Multiple version numbers in one project

In rare instances you may want to manage version numbers for multiple deliverables
within one project, and you may want them to be versioned independently.  This is supported
in `mister-bump` using the `--prefix` option.

Lets imagine you have two packages within your project: `fred` and `barney`.  You could configure
your CI pipeline to build and deploy those packages independently, based on the branch / tag names.
For example, `fred` could be deployed from CI pipelines on tags starting with `fred/`
(e.g. `fred/release-1.2.3`), and `barney` could be deployed from pipelines on branches starting with
`barney/`.

When running `mister-bump`, you can pass `--prefix='fred/'`, and `mister-bump` will fetch the latest
version for `fred/`, increment the version number (according to the documentation above), and return
the new version number.

Some things to note:

* If there is a `/` separating the prefix from the remainder of the tag, then you need to include
  the trailing `/`.
* The version number returned by `mister-bump` will not include the prefix.  It will just be `X.Y.ZrcN`
