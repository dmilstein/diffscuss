import os
import shutil
import sys
from subprocess import check_output, check_call


DIFFSCUSS_MB_FILE_NAME = '.diffscuss-mb'
USERS_DIR_NAME = 'users'
REVIEWS_DIR_NAME = 'reviews'


def mkdir_for_keeps(dir_name):
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    with open(os.path.join(dir_name, '.gitkeep'), 'wb') as fil:
        fil.write(' ')


def get_inbox_name(git_exe):
    return check_output([git_exe,
                         "config",
                         "--get",
                        "diffscuss-mb.inbox"]).strip()

def set_inbox_name(inbox_name, git_exe):
    return check_call([git_exe,
                       "config",
                       "diffscuss-mb.inbox",
                       inbox_name])


def get_git_root(git_exe):
    return check_output([git_exe,
                         "rev-parse",
                         "--show-toplevel"]).strip()


def real_abs_join(*args):
    return os.path.abspath(os.path.realpath(os.path.join(*args)))


def get_dmb_root(git_exe):
    git_root = get_git_root(git_exe)
    marker_fname = real_abs_join(git_root, DIFFSCUSS_MB_FILE_NAME)
    codereview_dir_name = None
    try:
        with open(marker_fname, 'rb') as fil:
            codereview_dir_name = fil.read().strip()
    except IOError:
        raise Exception("Please run dmb-init.py.")
    return real_abs_join(git_root, codereview_dir_name)


def get_reviews_dir(git_exe):
    return real_abs_join(get_dmb_root(git_exe), REVIEWS_DIR_NAME)


def check_inited(git_exe):
    dmb_root = get_dmb_root(git_exe)
    for d in ['', 'reviews', 'users']:
        to_check = os.path.join(dmb_root, d)
        if not os.path.isdir(to_check):
            raise Exception("%s does not exist, please create run dmb-init.py." %
                            to_check)


def get_inbox_path(inbox_name, git_exe):
    return os.path.join(get_dmb_root(git_exe),
                        USERS_DIR_NAME,
                        inbox_name)


def dmb_done(diffscuss_fname, inbox, git_exe):
    check_inited(git_exe)
    if not inbox:
        inbox = get_inbox_name(git_exe)
    inbox_path = get_inbox_path(inbox, git_exe)
    if not os.path.exists(inbox_path):
        _exit("Inbox '%s' doesn't exist, create it with dmb-mk-inbox.py" % inbox, 2)

    diffscuss_fpath = os.path.abspath(os.path.realpath(diffscuss_fname))

    for fname in os.listdir(inbox_path):
        if fname == '.gitkeep':
            continue
        fpath = os.path.join(inbox_path, fname)
        target = os.path.abspath(os.path.realpath(fpath))
        if target == diffscuss_fpath:
            os.remove(fpath)

    return diffscuss_fpath


def _error(msg):
    print >> sys.stderr, msg


def _move_to_reviews_dir(diffscuss_fname, git_exe):
    diffscuss_fpath = os.path.abspath(os.path.realpath(diffscuss_fname))
    reviews_dir = get_reviews_dir(git_exe)
    if os.path.commonprefix([reviews_dir,
                             diffscuss_fpath]) != reviews_dir:
        # if the review file is not in the reviews folder, we need to
        # move it in.
        shutil.move(diffscuss_fpath, reviews_dir)
        review_fpath = os.path.join(reviews_dir,
                                    os.path.basename(diffscuss_fpath))
    else:
        # otherwise, just use the path to the file as it's already in
        # reviews.
        review_fpath = diffscuss_fpath

    return review_fpath


def _link(review_fpath, inbox_path):
    relative_path = os.path.relpath(review_fpath, inbox_path)
    dest = os.path.join(inbox_path, os.path.basename(review_fpath))
    if os.path.exists(dest):
        os.remove(dest)
    os.symlink(relative_path, dest)


def dmb_post(diffscuss_fname, recipients, git_exe):
    check_inited(git_exe)
    review_fpath = _move_to_reviews_dir(diffscuss_fname, git_exe)

    for recipient in recipients:
        inbox_path = get_inbox_path(recipient, git_exe)
        if not os.path.isdir(inbox_path):
            _error(
                "Inbox %s doesn't seem to exist, please create it or specify another.")
        _link(review_fpath, inbox_path)

    return review_fpath
