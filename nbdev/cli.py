#AUTOGENERATED! DO NOT EDIT! File to edit: dev/06_cli.ipynb (unless otherwise specified).

__all__ = ['nbdev_build_lib', 'nbdev_update_lib', 'nbdev_diff_nbs', 'nbdev_test_nbs', 'create_default_sidebar',
           'make_sidebar', 'make_readme', 'nbdev_build_docs', 'nbdev_nb2md', 'rm_execution_count', 'clean_cell_output',
           'cell_metadata_keep', 'nb_metadata_keep', 'clean_cell', 'clean_nb', 'nbdev_clean_nbs', 'nbdev_read_nbs',
           'nbdev_trust_nbs', 'nbdev_fix_merge', 'nbdev_install_git_hooks']

#Cell
from .imports import *
from .export import *
from .sync import *
from .merge import *
from .export2html import *
from .test import *
from fastscript.fastscript import call_parse, Param

#Cell
@call_parse
def nbdev_build_lib(fname:Param("A notebook name or glob to convert", str)=None):
    "Export notebooks matching `fname` to python modules"
    notebook2script(fname=fname)
    write_tmpls()

#Cell
@call_parse
def nbdev_update_lib(fname:Param("A notebook name or glob to convert", str)=None):
    "Propagates any change in the modules matching `fname` to the notebooks that created them"
    script2notebook(fname=fname)

#Cell
@call_parse
def nbdev_diff_nbs():
    "Prints the diff between an export of the library in notebooks and the actual modules"
    diff_nb_script()

#Cell
import traceback

#Cell
def _test_one(fname, tmp_dir=None, flags=None):
    #time.sleep(random.random())
    print(f"testing: {fname}")
    try:
        test_nb(fname, flags=flags, tmp_dir=tmp_dir)
        return True
    except Exception as e:
        print(f"Error in {fname}:")
        #_,_,tb = sys.exc_info()
        #sm = traceback.StackSummary.extract(traceback.walk_tb(tb))
        #res = sm.format()
        #i = 0
        #while str(tmp_dir) not in res[i]: i+=1
        #print('\n'.join(res[i:]))
        tbe = traceback.TracebackException.from_exception(e)
        start_show=False
        for l in tbe.format():
            if not start_show: start_show = str(tmp_dir) in l
            if start_show: print(l)
        return False

#Cell
@call_parse
def nbdev_test_nbs(fname:Param("A notebook name or glob to convert", str)=None,
                   flags:Param("Space separated list of flags", str)=None,
                   n_workers:Param("Number of workers to use", int)=None):
    "Test in parallel the notebooks matching `fname`, passing along `flags`"
    if flags is not None: flags = flags.split(' ')
    if fname is None:
        files = [f for f in Config().nbs_path.glob('*.ipynb') if not f.name.startswith('_')]
    else: files = glob.glob(fname)

    # make sure we are inside the notebook folder of the project
    os.chdir(Config().nbs_path)
    with tempfile.TemporaryDirectory() as d:
        passed = parallel(_test_one, files, flags=flags, tmp_dir=Path(d), n_workers=n_workers)
    if all(passed): print("All tests are passing!")
    else:
        print("The following notebooks failed:")
        print('\n'.join([f.name for p,f in zip(passed,files) if not p]))

#Cell
import time,random,warnings

#Cell
def _leaf(k,v):
    url = 'external_url' if "http" in v else 'url'
    #if url=='url': v=v+'.html'
    return {'title':k, url:v, 'output':'web,pdf'}

#Cell
_k_names = ['folders', 'folderitems', 'subfolders', 'subfolderitems']
def _side_dict(title, data, level=0):
    k_name = _k_names[level]
    level += 1
    res = [(_side_dict(k, v, level) if isinstance(v,dict) else _leaf(k,v))
        for k,v in data.items()]
    return ({k_name:res} if not title
            else res if title.startswith('empty')
            else {'title': title, 'output':'web', k_name: res})

#Cell
_re_catch_title = re.compile('^title\s*:\s*(\S+.*)$', re.MULTILINE)

#Cell
def _get_title(fname):
    "Grabs the title of html file `fname`"
    with open(fname, 'r') as f: code = f.read()
    src =  _re_catch_title.search(code)
    return fname.stem if src is None else src.groups()[0]

#Cell
from .export2html import _nb2htmlfname
def create_default_sidebar():
    "Create the default sidebar for the docs website"
    dic = {"Overview": "/"}
    files = [f for f in Config().nbs_path.glob('*.ipynb') if not f.name.startswith('_')]
    fnames = [_nb2htmlfname(f) for f in sorted(files)]
    dic.update({_get_title(f):f'/{f.stem}' for f in fnames if f.stem!='index'})
    dic = {Config().lib_name: dic}
    json.dump(dic, open(Config().doc_path/'sidebar.json', 'w'), indent=2)

#Cell
def make_sidebar():
    "Making sidebar for the doc website form the content of `doc_folder/sidebar.json`"
    if not (Config().doc_path/'sidebar.json').exists() or Config().custom_sidebar == 'False': create_default_sidebar()
    sidebar_d = json.load(open(Config().doc_path/'sidebar.json', 'r'))
    res = _side_dict('Sidebar', sidebar_d)
    res = {'entries': [res]}
    res_s = yaml.dump(res, default_flow_style=False)
    res_s = res_s.replace('- subfolders:', '  subfolders:').replace(' - - ', '   - ')
    res_s = f"""
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# Instead edit {'../../sidebar.json'}
"""+res_s
    open(Config().doc_path/'_data/sidebars/home_sidebar.yml', 'w').write(res_s)

#Cell
_re_index = re.compile(r'^(?:\d*_|)index\.ipynb$')

#Cell
def make_readme():
    "Convert the index notebook to README.md"
    index_fn = None
    for f in Config().nbs_path.glob('*.ipynb'):
        if _re_index.match(f.name): index_fn = f
    assert index_fn is not None, "Could not locate index notebook"
    convert_md(index_fn, Config().config_file.parent, jekyll=False)
    n = Config().config_file.parent/index_fn.with_suffix('.md').name
    shutil.move(n, Config().config_file.parent/'README.md')

#Cell
@call_parse
def nbdev_build_docs(fname:Param("A notebook name or glob to convert", str)=None,
                     force_all:Param("Rebuild even notebooks that haven't changed", bool)=False,
                     mk_readme:Param("Also convert the index notebook to README", bool)=True,):
    "Build the documentation by converting notebooks mathing `fname` to html"
    notebook2html(fname=fname, force_all=force_all)
    if fname is None: make_sidebar()
    if mk_readme: make_readme()

#Cell
@call_parse
def nbdev_nb2md(fname:Param("A notebook file name to convert", str),
                dest:Param("The destination folder", str)='.',
                jekyll:Param("To use jekyll metadata for your markdown file or not", bool)=True,):
    "Convert the notebook in `fname` to a markdown file"
    convert_md(fname, dest, jekyll=jekyll)

#Cell
def rm_execution_count(o):
    "Remove execution count in `o`"
    if 'execution_count' in o: o['execution_count'] = None

#Cell
def clean_cell_output(cell):
    "Remove execution count in `cell`"
    if 'outputs' in cell:
        for o in cell['outputs']: rm_execution_count(o)

#Cell
cell_metadata_keep = ["hide_input"]
nb_metadata_keep   = ["kernelspec", "jekyll"]

#Cell
def clean_cell(cell, clear_all=False):
    "Clen `cell` by removing superluous metadata or everything except the input if `clear_all`"
    rm_execution_count(cell)
    if 'outputs' in cell:
        if clear_all: cell['outputs'] = []
        else:         clean_cell_output(cell)
    cell['metadata'] = {} if clear_all else {k:v for k,v in cell['metadata'].items() if k in cell_metadata_keep}

#Cell
def clean_nb(nb, clear_all=False):
    "Clean `nb` from superfulous metadata, passing `clear_all` to `clean_cell`"
    for c in nb['cells']: clean_cell(c, clear_all=clear_all)
    nb['metadata'] = {k:v for k,v in nb['metadata'].items() if k in nb_metadata_keep }

#Cell
import io,sys,json

#Cell
def _print_output(nb):
    "Print `nb` in stdout for git things"
    _output_stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    x = json.dumps(nb, sort_keys=True, indent=1, ensure_ascii=False)
    _output_stream.write(x)
    _output_stream.write("\n")
    _output_stream.flush()

#Cell
@call_parse
def nbdev_clean_nbs(fname:Param("A notebook name or glob to convert", str)=None,
                    clear_all:Param("Clean all metadata and outputs", bool)=False,
                    disp:Param("Print the cleaned outputs", bool)=False):
    "Clean all notebooks in `fname` to avoid merge conflicts"
    #Git hooks will pass the notebooks in the stdin
    input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8') if sys.stdin else None
    if input_stream and fname is None:
        nb = json.load(input_stream)
        clean_nb(nb, clear_all=clear_all)
        _print_output(nb)
        return
    files = Config().nbs_path.glob('**/*.ipynb') if fname is None else glob.glob(fname)
    for f in files:
        if not str(f).endswith('.ipynb'): continue
        nb = read_nb(f)
        clean_nb(nb, clear_all=clear_all)
        if disp: _print_output(nb)
        else:
            NotebookNotary().sign(nb)
            nbformat.write(nb, str(f), version=4)

#Cell
@call_parse
def nbdev_read_nbs(fname:Param("A notebook name or glob to convert", str)=None):
    "Check all notebooks matching `fname` can be opened"
    files = Config().nbs_path.glob('**/*.ipynb') if fname is None else glob.glob(fname)
    for nb in files:
        try: _ = read_nb(nb)
        except Exception as e:
            print(f"{nb} is corrupted and can't be opened.")
            raise e

#Cell
@call_parse
def nbdev_trust_nbs(fname:Param("A notebook name or glob to convert", str)=None,
                    force_all:Param("Trust even notebooks that haven't changed", bool)=False):
    "Trust noteboks matching `fname`"
    check_fname = Config().nbs_path/".last_checked"
    last_checked = os.path.getmtime(check_fname) if check_fname.exists() else None
    files = Config().nbs_path.glob('**/*.ipynb') if fname is None else glob.glob(fname)
    for fn in files:
        if last_checked and not force_all:
            last_changed = os.path.getmtime(fn)
            if last_changed < last_checked: continue
        nb = read_nb(fn)
        if not NotebookNotary().check_signature(nb): NotebookNotary().sign(nb)
    check_fname.touch(exist_ok=True)

#Cell
@call_parse
def nbdev_fix_merge(fname:Param("A notebook filename to fix", str),
                    fast:Param("Fast fix: automatically fix the merge conflicts in outputs or metadata", bool)=True,
                    trust_us:Param("Use local outputs/metadata when fast mergning", bool)=True):
    "Fix merge conflicts in notebook `fname`"
    fix_conflicts(fname, fast=fast, trust_us=trust_us)

#Cell
import subprocess

#Cell
@call_parse
def nbdev_install_git_hooks():
    "Install git hooks to clean/trust notebooks automatically"
    path = Config().config_file.parent
    fn = path/'.git'/'hooks'/'post-merge'
    #Trust notebooks after merge
    with open(fn, 'w') as f:
        f.write("""#!/bin/bash
echo "Trusting notebooks"
nbdev_trust_nbs
"""
        )
    os.chmod(fn, os.stat(fn).st_mode | stat.S_IEXEC)
    #Clean notebooks on commit/diff
    with open(path/'.gitconfig', 'w') as f:
        f.write("""# Generated by nbdev_install_git_hooks
#
# If you need to disable this instrumentation do:
#
# git config --local --unset include.path
#
# To restore the filter
#
# git config --local include.path .gitconfig
#
# If you see notebooks not stripped, checked the filters are applied in .gitattributes
#
[filter "clean-nbs"]
        clean = nbdev_clean_nbs
        smudge = cat
        required = true
[diff "ipynb"]
        textconv = nbdev_clean_nbs --disp True --fname
""")
    cmd = "git config --local include.path ../.gitconfig"
    print(f"Executing: {cmd}")
    result = subprocess.run(cmd.split(), shell=False, check=False, stderr=subprocess.PIPE)
    if result.returncode == 0:
        print("Success: hooks are installed and repo's .gitconfig is now trusted")
    else:
        print("Failed to trust repo's .gitconfig")
        if result.stderr: print(f"Error: {result.stderr.decode('utf-8')}")
    with open(Config().nbs_path/'.gitattributes', 'w') as f:
        f.write("""**/*.ipynb filter=clean-nbs
**/*.ipynb diff=ipynb
"""
               )