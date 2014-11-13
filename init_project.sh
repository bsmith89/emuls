#!/usr/bin/env bash -x

git submodule update --init --recursive
git remote rename origin template
git config --unset branch.master.remote
git config --local filter.dropoutput_ipynb.clean utils/ipynb_output_filter.py
git config --local filter.dropoutput_ipynb.smudge cat
unlink README.md
ln -s NOTE.md README.md
rm -i $0
git add -A
git commit -em "Clean project.  Let's get started!"
