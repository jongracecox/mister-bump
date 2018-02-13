#!/usr/bin/python
"""
Module to detect appropriate project version number from Git.
"""
from __future__ import print_function
import os
import logging
import re
import argparse
from subprocess import check_output, CalledProcessError, STDOUT

logger = logging.getLogger(__name__)

DEFAULT_VERSION = 'release-0.0.0-1'
DEFAULT_STYLE = 'rc'


def git_fetch_origin():
    """Fetch origin from git to make sure other tags are present."""
    command = ['git', 'fetch', 'origin']
    logger.debug('Fetching commit history from git')

    logger.debug('Command: %s', ' '.join(command))

    with open(os.devnull, 'w') as devnull:
        try:
            return check_output(command, stderr=STDOUT).rstrip().decode('utf-8')
        except CalledProcessError as e:
            logger.error('Failed to fetch from origin.')
            for line in e.output.split('\n'):
                logger.error(line)


def git_describe(options=None, **kwargs):
    """
    Run git describe and return output.

    Pass any arguments valid for use with git describe.  kwargs arguments will be
    translated into ``--arg=value`` format, and added to the command.

    If arguments are passed as lists, then they will be translated into multiple
    arguments.  For example ``git_describe(match=['a','b'])`` will be translated
    into the command ``git describe --match a --match b``.

    If the ``git describe`` command fails then DEFAULT_VERSION will be returned.
    """
    command = ['git', 'describe']

    if options:
        if not isinstance(options, list):
            options = [options]
        command.extend(options)

    logger.debug('Getting current git version')
    for arg in kwargs.keys():
        values = kwargs[arg]
        if not isinstance(values, list):
            values = [values]
        for value in values:
            command.append('--%s=%s' % (arg, value))
    logger.debug('Command: %s', ' '.join(command))

    with open(os.devnull, 'w') as devnull:
        try:
            return check_output(command, stderr=devnull).rstrip().decode('utf-8')
        except CalledProcessError:
            logger.debug('No upstream refs found, so returning default version.')
            return DEFAULT_VERSION


def get_git_branch():
    """Return current git branch.

    This will try to use the GitLab CI CI_BUILD_REF_NAME variable, and
    if that doesn't exist, then use ``git rev-parse`` instead.
    """

    try:
        branch = os.environ['CI_BUILD_REF_NAME']
    except KeyError:
        branch = check_output('git rev-parse --abbrev-ref HEAD', shell=True).rstrip().decode('utf-8')

    logger.debug('Current git branch is %s', branch)
    return branch


def is_bugfix_branch(branch_name, prefix=''):
    """
    Return True if current branch is bugfix branch.

    Identified by the fact that the current branch matches ``bugfix-X-X-X``.

    Args:
        branch_name(str): Name of branch, as retrieved from git.
        prefix(str): Tag / branch prefix.  This is a prefix that you expect to appear
            in front of the tag or branch name.  For example, in branch ``fred/bugfix-1.2.3`` the
            prefix would be ``fred/`` - Note that the trailing ``/`` is included in the prefix.

    Example:
        >>> is_bugfix_branch('release-0.1.0')
        False
        >>> is_bugfix_branch('release-0.1.0-bugfix')
        False
        >>> is_bugfix_branch('bugfix')
        False
        >>> is_bugfix_branch('bugfix-0.1.0')
        True
        >>> is_bugfix_branch('bugfix-1234.13123.45676')
        True
        >>> is_bugfix_branch('bugfix-1234.13123.45676.something')
        False
        >>> is_bugfix_branch('fred/bugfix-0.1.0')
        False
        >>> is_bugfix_branch('fred/bugfix-0.1.0', prefix='fred/')
        True
    """
    result = re.match(r'^%sbugfix-[0-9]+\.[0-9]+\.[0-9]+$' % prefix, branch_name) is not None

    logger.debug('Current branch is bugfix? %s', str(result))

    return result


def parse_version(version, prefix=''):
    """
    Split the version string into components.

    Args:
        version(str): Unformatted version number, as returned by git_describe function.
        prefix(str): Tag / branch prefix.  This is a prefix that you expect to appear
            in front of the tag or branch name.  For example, in branch ``fred/bugfix-1.2.3`` the
            prefix would be ``fred/`` - Note that the trailing ``/`` is included in the prefix.

    Returns:
        dict: Version split into component parts

    Example:
        >>> parse_version('release-0.5.0-459-ge02af') == {'deviation': '459', 'major': '0', 'hash': 'ge02af',
        ...     'bugfix': '0', 'type': 'release', 'minor': '5'}
        True
        >>> parse_version('release-0.5.0-459') == {'deviation': '459', 'major': '0', 'hash': '', 'bugfix': '0',
        ...     'type': 'release', 'minor': '5'}
        True
        >>> parse_version('release-0.5.0') == {'deviation': '', 'major': '0', 'hash': '', 'bugfix': '0',
        ...     'type': 'release', 'minor': '5'}
        True
        >>> parse_version('bugfix-0.5.0-459-ge02af') == {'deviation': '459', 'major': '0', 'hash': 'ge02af',
        ...     'bugfix': '0', 'type': 'bugfix', 'minor': '5'}
        True
        >>> parse_version('release-0.5.0-final') == {'deviation': '', 'major': '0', 'hash': '', 'bugfix': '0',
        ...     'type': 'final', 'minor': '5'}
        True
        >>> parse_version('release-0.5.0.final') == {'deviation': '', 'major': '0', 'hash': '', 'bugfix': '0',
        ...     'type': 'final', 'minor': '5'}
        True
        >>> parse_version('fred/release-0.5.0-459-ge02af', prefix='fred/') == {'deviation': '459', 'major': '0',
        ...     'hash': 'ge02af', 'bugfix': '0', 'type': 'release', 'minor': '5'}
        True

    """
    # Strip off the prefix
    if prefix:
        logger.debug('Stripping prefix "%s" from "%s".', prefix, version)
        version = re.sub(r'^%s' % prefix, '', version)
        logger.debug('New version is "%s".', version)

    # Split the version string up on . and - characters.
    parts = re.split(r'[-.]', version)

    # Extend list in case portions are missing.
    parts.extend([''] * (6 - len(parts)))

    parts_dict = {'type': parts[0],
                  'major': parts[1],
                  'minor': parts[2],
                  'bugfix': parts[3],
                  'deviation': parts[4],
                  'hash': parts[5]
                  }

    if parts_dict['deviation'] == 'final':
        parts_dict['deviation'] = parts_dict['hash']
        parts_dict['hash'] = ''
        parts_dict['type'] = 'final'

    return parts_dict


def log_version_details(version_dict):
    """Write version information to log."""
    for k in ['type', 'major', 'minor', 'bugfix', 'deviation', 'hash']:
        logger.debug('Version %s = %s', k, version_dict[k])


def format_version(version, style='rc'):
    """
    Format the version returned by git describe into a semver version number.

    Args:
        version(dict): Version dictionary as returned by parse_version function.
        style(str): Style of suffix. Valid values ``.dev``, ``rc``.

    Returns:
        str: Formatted version number.

    Example:

        >>> format_version({'type': 'release', 'major': '1', 'minor': '2', 'bugfix': '3',
        ...                 'deviation': '459',  'hash': 'ge02af'})
        '1.2.3rc459'
        >>> format_version({'type': 'release', 'major': '1', 'minor': '2', 'bugfix': '3',
        ...                 'deviation': '459',  'hash': 'ge02af'}, style='rc')
        '1.2.3rc459'
        >>> format_version({'type': 'release', 'major': '1', 'minor': '2', 'bugfix': '3',
        ...                 'deviation': '459',  'hash': 'ge02af'}, style='.dev')
        '1.2.3.dev459'
        >>> format_version({'type': 'release', 'major': '1', 'minor': '2', 'bugfix': '3',
        ...                 'deviation': '',  'hash': ''})
        '1.2.3'
        >>> format_version({'type': 'final', 'major': '1', 'minor': '2', 'bugfix': '3',
        ...                 'deviation': '',  'hash': ''})
        '1.2.3.final'
        >>> format_version({'type': 'final', 'major': '1', 'minor': '2', 'bugfix': '3',
        ...                 'deviation': '459',  'hash': 'ge02af'})
        '1.2.3rc459'

    """
    if not version['deviation']:
        style = ''

    version_str = "{major}.{minor}.{bugfix}{suffix}{deviation}".format(
        major=version['major'],
        minor=version['minor'],
        bugfix=version['bugfix'],
        suffix=style,
        deviation=version['deviation']
    )

    # Add final suffix for final releases.
    if version['type'] == 'final' and not version['deviation']:
        logger.debug('Adding final suffix for final release.')
        version_str += '.final'

    logger.debug('Formatted version is "%s"', version_str)

    return version_str


def get_increment_type(version, prefix=''):
    """
    Return the appropriate increment type based on the current version.

    Args:
        version(str): Unformatted version number, as returned by git_describe function.
        prefix(str): Tag / branch prefix.  This is a prefix that you expect to appear
            in front of the tag or branch name.  For example, in branch ``fred/bugfix-1.2.3`` the
            prefix would be ``fred/`` - Note that the trailing ``/`` is included in the prefix.

    Returns:
        str: Type of version increment to be performed (``major``, ``minor``, ``bugfix``).

    Example:

        >>> get_increment_type('release-0.5.0')
        >>> get_increment_type('release-0.5.0-459-ge02af')
        'minor'
        >>> get_increment_type('bugfix-0.5.0')
        >>> get_increment_type('bugfix-0.5.0-459-ge02af')
        'bugfix'
        >>> get_increment_type('release-0.5.0-final')
        >>> get_increment_type('release-0.5.0-final-459-ge02af')
        'major'
        >>> get_increment_type('blahblahblah')
        >>> get_increment_type('fred/release-0.5.0-459-ge02af', prefix='fred/')
        'minor'

    """
    version_dict = parse_version(version, prefix=prefix)

    # If there is no deviation from the previous release then this IS the release.
    if not version_dict['deviation']:
        logger.debug('There is no deviation from %s %s.%s.%s.  No increment will be performed.',
                     version_dict['type'], version_dict['major'], version_dict['minor'], version_dict['bugfix'])
        return None

    if re.match(r'.*[.-]final-?', version):
        return 'major'
    elif re.match(r'^release-.*', version):
        return 'minor'
    elif re.match(r'^bugfix-.*', version):
        return 'bugfix'

    return 'minor'


def increment_version(version, increment):
    """
    Increment version number by increment.

    Args:
        version(dict): Parsed version number, as returned by parse_version function.
        increment(str, optional): Type of version increment to be performed (``major``, ``minor``, ``bugfix``).

    Example:
        >>> increment_version({'type': 'release', 'major': '1', 'minor': '2', 'bugfix': '3',
        ...                    'deviation': '459', 'hash': 'ge02af'}, 'minor') == {'deviation': '459',
        ...                        'major': '1', 'hash': 'ge02af', 'bugfix': '0', 'type': 'release', 'minor': '3'}
        True
        >>> increment_version({'type': 'release', 'major': '1', 'minor': '2', 'bugfix': '3',
        ...                    'deviation': '459', 'hash': 'ge02af'}, 'major') == {'deviation': '459', 'major': '2',
        ...                        'hash': 'ge02af', 'bugfix': '0', 'type': 'release', 'minor': '0'}
        True
        >>> increment_version({'type': 'release', 'major': '1', 'minor': '2', 'bugfix': '3',
        ...                    'deviation': '459', 'hash': 'ge02af'}, 'bugfix') == {'deviation': '459', 'major': '1',
        ...                        'hash': 'ge02af', 'bugfix': '4', 'type': 'release', 'minor': '2'}
        True
        >>> increment_version({'type': 'release', 'major': '1', 'minor': '2', 'bugfix': '3',
        ...                    'deviation': '459', 'hash': 'ge02af'}, None) == {'deviation': '459', 'major': '1',
        ...                        'hash': 'ge02af', 'bugfix': '3', 'type': 'release', 'minor': '2'}
        True

    """
    if not increment:
        logger.debug('No increment to be done.')
        return version

    logger.debug('Incrementing with %s version increment.', increment.upper())

    if increment == 'major':
        version['major'] = str(int(version['major']) + 1)
        version['minor'] = version['bugfix'] = '0'
    elif increment == 'minor':
        version['minor'] = str(int(version['minor']) + 1)
        version['bugfix'] = '0'
    elif increment == 'bugfix':
        version['bugfix'] = str(int(version['bugfix']) + 1)

    return version


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Get appropriate project version number based on Git status.")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.')
    parser.add_argument('-s', '--style', type=str, help='Style of suffix.', choices=['rc', '.dev'],
                        default=DEFAULT_STYLE)
    parser.add_argument('override', nargs='?', default=None, help='Override version number.'
                        ' Must be in the format "release-0.0.0-000-aaaaaa".')
    parser.add_argument('-n', '--no-increment', action='store_true', help='Do not increment version number.')
    parser.add_argument('-p', '--prefix', type=str, default=None,
                        help='Optionally specify a prefix that you expect to appear before the "release-X.X.X" tag. '
                             'For example if your tag was "fred/release-0.1.0" then you would use '
                             'a PREFIX of "fred/".')

    return parser.parse_args()


def get_git_version(tags=None, prefix=None):
    """
    Get the current version from git.

    This involves using ``git describe`` to fetch the distance from the specified tags.

    Args:
        tags(list of str): List of tags to search git for.
        prefix(str, optional): Specify a prefix that you expect to appear before the
            "release-X.X.X" tag.

    Returns:
        str: Unparsed verison string.
    """
    if not tags:
        tags = ['release-*']

    if prefix:
        logger.debug('Adding prefix "%s" to all tags.', prefix)
        tags = [prefix+t for t in tags]

    logger.debug('Searching for the following tags: %s', ', '.join(tags))

    logger.debug('Fetching all candidate upstream versions')

    candidates = [git_describe(options='--tags', abbrev=4, match=t) for t in tags]

    logger.debug('Candidate versions: %s' % ', '.join(candidates))

    # Take the candidates list of strings and turn into a list
    # containing version string and parsed dict.
    candidates = [[c, parse_version(c, prefix=prefix)] for c in candidates]

    selected_version = None

    for candidate in candidates:

        logger.debug('Comparing candidate %s', candidate[0])
        log_version_details(candidate[1])

        if not selected_version:
            selected_version = candidate
        elif int(candidate[1]['deviation']) < int(selected_version[1]['deviation']):
            selected_version = candidate

    # Get current branch, and check whether we are on bugfix.
    # If so, then we will hack the selected version to be a 'bugfix' rather than 'release'.
    if is_bugfix_branch(get_git_branch(), prefix=prefix):
        # TODO: Decide whether we need to include prefix in the following sub call.
        selected_version[0] = re.sub('^release', 'bugfix', selected_version[0], count=1)

    # The selected candidate version string will be the first part of the tuple,
    # so return that.
    logger.debug('Version detected as "%s"', selected_version[0])

    return selected_version[0]


def bump(style=DEFAULT_STYLE, override=None, no_increment=False, prefix=None):
    """
    Return bumped version.

    Args:
        style(str): Style of suffix. Valid values ``.dev``, ``rc``.
        override(str): Override the incoming version number (i.e. don't take it from git).
        no_increment(bool): Do not actually bump the version, just return the current version.
            This might not seem useful, but it allows you to use ``bump`` to simply fetch the
            current git version, and reformat it.
        prefix(str, optional): Specify a prefix that you expect to appear before the
            "release-X.X.X" tag.

    Returns:
        str: Bumped version number in simplified output format (see examples).

    Example:

        Current version is a deviation of the ``release-1.2.0`` tag.  Since it comes after the
        release, we can assume this is for the next minor release.

        >>> bump(override='release-1.2.0-456-aaaaa')
        '1.3.0rc456'

        Technically there should never be a "release" tag with a bugfix version number (``X.X.3``),
        but if there was, it should be handled like this.

        >>> bump(override='release-1.2.3-456-aaaaa')
        '1.3.0rc456'

        Current version is a deviation of the ``bugfix-1.2.3`` tag.  Since it comes after the
        bugfix, we can assume this is for the next bugfix release.  Bug fixes are
        assumed to be on their own branch that never goes back into master.
        Therefore in a bugfix branch, we will only ever see incrementing bugfix
        numbers.

        >>> bump(override='bugfix-1.2.3-456-aaaaa')
        '1.2.4rc456'

        Current version is the ``bugfix-1.2.3`` tag, so return that version number.
        There is no need to refer to bugfix within the output version number since
        this is implicit in the bugfix version number.

        >>> bump(override='bugfix-1.2.3')
        '1.2.3'

        Current version is the ``release-1.2.0`` tag, so return that versio number.

        >>> bump(override='release-1.2.0')
        '1.2.0'

        Current version is the ``release-1.2.0.final`` tag, which is the final version
        of the 1.2.0 release.  This is used to indicate that from now, everything is
        working towards the next major release.bump

        >>> bump(override='release-1.2.0.final')
        '1.2.0.final'
        >>> bump(override='release-1.2.0-final')
        '1.2.0.final'
        >>> bump(override='release-1.2.0-final')
        '1.2.0.final'

        Current version is a deviation from the ``release-1.2.0-final`` tag, and since
        the last release was the final for that version, this is considered as work
        that goes into the next major version.

        >>> bump(override='release-1.2.0-final-456')
        '2.0.0rc456'

        Current version is a deviation from the ``release-1.2.0.final`` tag.
        This tag is subtly different to the previous example in that is uses ``.final``
        instead of ``-final``.  The used of ``.`` is not standard, but has been supported
        since it could be a common mistake, and should be handled elegantly.  Since
        the last release was the final for that version, this is considered as work
        that goes into the next major version.

        >>> bump(override='release-1.2.0.final-456')
        '2.0.0rc456'

        When a prefix appears before the "release-X.X.X", a prefix should be passed.
        This causes mister bump to search the git history for that specific tag, and will
        result in that tags version number being retrieved and bumped.  This can be useful
        for projects that have multiple components, allowing them to have different version
        numbers.

        >>> bump(override='fred/release-1.2.0.final-456', prefix='fred/')
        '2.0.0rc456'

    """
    # Check for override
    # If there was a command line argument then we assume it is a version override.
    if override:
        git_version = override
        logger.debug('Using override version "%s"', git_version)
    else:
        git_fetch_origin()
        git_version = get_git_version(prefix=prefix)

    # Parse the version number into parts
    version_dict = parse_version(git_version, prefix=prefix)

    # Do not increment version numbers if override was passed.
    if not no_increment:

        # Detect the increment type, based on previous tag
        increment_type = get_increment_type(git_version, prefix=prefix)

        # Increment the version number based on increment type
        version_dict = increment_version(version_dict, increment_type)

    else:
        logger.debug('No increment option is set to no increment will occur.')

    # Format the version number
    formatted_version = format_version(version_dict, style=style)

    # Output the number
    return formatted_version


def test():
    # Test function
    import doctest
    doctest.testmod()


def main():
    """
    Run getversion to get the next version number.
    """
    args = parse_args()

    if args.verbose:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.WARNING

    logging.basicConfig(level=logging_level,
                        format="%(asctime)s [%(name)s:%(lineno)d][%(levelname)s] %(message)s",
                        datefmt='%I:%M:%S')

    print(bump(style=args.style, override=args.override, no_increment=args.no_increment,
               prefix=args.prefix))


if __name__ == '__main__':
    main()
