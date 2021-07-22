#!/bin/bash


ln -sf $PWD/zsh/.zshrc $HOME/.zshrc
ln -sf $PWD/tmux $HOME/.tmux
ln -s $PWD/alacritty $HOME/.config/alacritty
ln -s $PWD/bat $HOME/.config/bat
ln -s $PWD/i3 $HOME/.config/i3
ln -s $PWD/qutebrowser $HOME/.config/qutebrowser
ln -s $PWD/ranger $HOME/.config/ranger

git clone https://github.com/paraizofelipe/nvim $HOME/.config/nvim
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone https://github.com/tmux-plugins/tmux-sensible ~/.tmux/plugins/tmux-sensible
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm


ln -sf $PWD/git/.gitconfig $HOME/.gitconfig
ln -sf $PWD/git/.gitignore $HOME/.gitignore
