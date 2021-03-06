#!/usr/bin/env python

from optparse import OptionParser
from subprocess import check_output
import sys
import time
from textwrap import dedent


def _git_config(config_name, git_exe):
    return check_output([git_exe, "config", "--get", config_name]).strip()


def _git_user_name(git_exe):
    return _git_config("user.name", git_exe)


def _git_user_email(git_exe):
    return _git_config("user.email", git_exe)


def _iso_time():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _git_log(revision, git_exe):
    """
    Return a list of log lines.
    """
    return check_output([git_exe, "log", "--pretty=format:%B%n", revision]).split('\n')


def _write_diff(output_f, revision, git_exe):
    output_f.write(check_output([git_exe, "diff", "--unified=20", revision]))


def _write_diffscuss_header(output_f, author, email, git_exe):
    if author is None:
        author = _git_user_name(git_exe)
    if email is None:
        email = _git_user_email(git_exe)

    iso_time = _iso_time()

    header_lines = ['',
                    "author: %s" % author,
                    "email: %s" % email,
                    "date: %s" % iso_time,
                    '']
    header_lines = ['%%* %s' % s for s in header_lines]

    output_f.write('\n'.join(header_lines))
    output_f.write('\n')


def _write_diffscuss_body(output_f, revision, git_exe):
    log_lines = ['%%- %s' % s for s in _git_log(revision, git_exe)]
    output_f.write('\n'.join(log_lines))
    output_f.write('\n')


def main(revision, output_f, author=None, email=None, git_exe=None):
    if not git_exe:
        git_exe = 'git'
    _write_diffscuss_header(output_f, author, email, git_exe)
    _write_diffscuss_body(output_f, revision, git_exe)
    _write_diff(output_f, revision, git_exe)


if __name__ == '__main__':
    parser = OptionParser(usage=dedent("""\
                %prog [options] git_revision_range

                git_revision_range will be passed as-is to git diff and git log.
                For example, you could use HEAD~3..HEAD or some_branch..master.
                Note that you probably don't want just a branch name, as git log
                will start the log from that point and run backwards to the initial
                commit in the repo."""))
    parser.add_option("-a", "--author",
                      help="The author for the diffscuss review (defaults to git user.name)",
                      dest="author")
    parser.add_option("-e", "--email",
                      help="The email address for the diffscuss review (defaults to git user.email)",
                      dest="email")
    parser.add_option("-g", "--git-exe",
                      help="The path to the git executable (defaults to 'git')",
                      dest="git_exe")
    parser.add_option("-o", "--output",
                      help="File in which to put the output (defaults to stdout).",
                      dest="output")

    opts, args = parser.parse_args()

    if opts.output is None:
        out_f = sys.stdout
    else:
        out_f = open(opts.output, 'wb')

    main(args[0], out_f, git_exe=opts.git_exe, author=opts.author, email=opts.email)

    if opts.output is not None:
        out_f.close()
