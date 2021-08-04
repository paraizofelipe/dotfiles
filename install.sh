#!/bin/bash

if [ ! -d $HOME/.config ]; then mkdir $HOME/.config; fi

ln -sf $PWD/zsh/.zshrc $HOME/.zshrc
ln -sf $PWD/tmux/.tmux.conf $HOME/.tmux.conf
ln -s $PWD/alacritty $HOME/.config/alacritty
ln -s $PWD/bat $HOME/.config/bat
ln -s $PWD/i3 $HOME/.config/i3
ln -s $PWD/i3blocks $HOME/.config/i3blocks
ln -s $PWD/qutebrowser $HOME/.config/qutebrowser
ln -s $PWD/ranger $HOME/.config/ranger

git clone -b nvim-5 https://github.com/paraizofelipe/nvim $HOME/.config/nvim
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone https://github.com/tmux-plugins/tmux-sensible ~/.tmux/plugins/tmux-sensible
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm


ln -sf $PWD/git/.gitconfig $HOME/.gitconfig
ln -sf $PWD/git/.gitignore $HOME/.gitignore
