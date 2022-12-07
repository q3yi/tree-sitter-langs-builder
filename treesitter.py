#!/usr/bin/env python3

import os
import sys
import shutil

import json
import argparse
import asyncio


async def run(cmd, cwd=None):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd)

    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise Exception(stderr.decode())


async def fetch(url, save_folder):

    if os.path.exists(save_folder):
        cmd = 'git pull'
        return await run(cmd, cwd=save_folder)
    else:
        cmd = f'git clone {url} --depth 1 --quiet {save_folder}'
        return await run(cmd)


async def compile(language, src, dest, ext):
    target_file = os.path.join(dest, f'libtree-sitter-{language}.{ext}')
    compile_parser = "cc -c -I. parser.c"

    if os.path.exists(os.path.join(src, "scanner.c")):
        await run("cc -fPIC -c -I. scanner.c", cwd=src)

    if os.path.exists(os.path.join(src, "scanner.cc")):
        await asyncio.gather(
            run(compile_parser, cwd=src),
            run("c++ -fPIC -c -I. scanner.cc", cwd=src))
        link_cmd = f'c++ -fPIC -shared *.o -o "{target_file}"'
    else:
        await run(compile_parser, cwd=src)
        link_cmd = f'cc -fPIC -shared *.o -o "{target_file}"'

    await run(link_cmd, cwd=src)


async def build(language, repo, repo_root="", dest_folder="", ext="so"):
    repo_folder = f'libtree-sitter-{language}'
    src_folder = os.path.join(repo_folder, repo_root, "src")

    await fetch(repo, os.path.join(os.getcwd(), repo_folder))

    shutil.copy("tree-sitter-lang.in", src_folder)
    shutil.copy("emacs-module.h", src_folder)
    shutil.copy(os.path.join(repo_folder, repo_root, "grammar.js"), src_folder)

    await compile(language, src_folder, dest_folder, ext)

    shutil.rmtree(repo_folder)


async def json_batch_build(json_file, repo_root, dest_folder, ext):

    with open(json_file, mode="r") as f:
        configs = json.load(f)

    tasks = []
    for lang_conf in configs:
        lang = lang_conf["language"]
        repo = lang_conf["repo"]

        repo_root = lang_conf.get("repo_root", repo_root)
        dest = lang_conf.get("dist_folder", dest_folder)
        ext = lang_conf.get("ext", ext)

        tasks.append(build(lang, repo, repo_root, dest, ext))

    await asyncio.gather(*tasks)


async def main():
    parser = argparse.ArgumentParser(description="Build emacs tree-sitter language module")
    parser.add_argument("language", metavar="LANG", nargs="*", help="languages needed to built")
    parser.add_argument("--github-org", dest="org", nargs="?", default="tree-sitter", help="github organization that holds repo")
    parser.add_argument("--repo-root", dest="repo_root", nargs="?", default="", help="support mutliple language in one repo, like typescript and tsx")
    parser.add_argument("--repo", dest="repo", nargs="?", help="full git repo url")
    parser.add_argument("--dist", dest="dist", nargs="?", help="build module into folder. default: ./dist")
    parser.add_argument("--ext", dest="ext", nargs="?", help="module extensition. '.so' in linux, '.dylib' in osx")
    parser.add_argument("--batch-json", dest="json", nargs="?", help="batch build")

    args = parser.parse_args(sys.argv[1:])

    if not args.ext:
        args.ext = "so"
        if os.uname().sysname == "Darwin":
            args.ext = "dylib"

    if not args.dist:
        args.dist = os.path.join(os.getcwd(), "dist")

    if args.json:
        try:
            await json_batch_build(args.json, args.repo_root, args.dist, args.ext)
            sys.exit(0)
        except Exception as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    if len(args.language) == 0:
        print("at least one language needed.", file=sys.stderr)
        sys.exit(1)

    tasks = []
    for lang in args.language:
        if len(args.language) < 2 and args.repo:
            repo_url = args.repo
        else:
            repo_url = f'https://github.com/{args.org}/tree-sitter-{lang}.git'

        tasks.append(
            build(lang, repo_url, repo_root=args.repo_root, dest_folder=args.dist, ext=args.ext)
        )

    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
