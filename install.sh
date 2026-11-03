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

# Painel de agentes (uso de Claude/Codex/OpenRouter no polybar)
# libxcb-cursor0/libxkbcommon-x11-0/libegl1: exigidas pelo plugin xcb do Qt 6 (PySide6)
# libnotify-bin (notify-send) + libglib2.0-bin (gdbus): alertas e botão de trocar conta
sudo apt-get update
sudo apt-get install -y python3 pipx alacritty picom xdg-utils libnotify-bin libglib2.0-bin \
  libxcb-cursor0 libxkbcommon-x11-0 libegl1 libfontconfig1 libdbus-1-3
command -v uv >/dev/null || pipx install uv
export PATH="$HOME/.local/bin:$PATH"
# Sem pacote apt equivalente (o fonts-font-awesome do 22.04 é a 4.7): só avisa.
fc-list | grep -q "Hack Nerd Font" || echo "AVISO: instale a Hack Nerd Font v3 (github.com/ryanoasis/nerd-fonts) em ~/.local/share/fonts"
fc-list | grep -q "Font Awesome 5 Free" || echo "AVISO: instale a Font Awesome 5 Free (ícone da barra) em ~/.local/share/fonts"
mkdir -p $HOME/.local/bin $HOME/.config/systemd/user
ln -sf $PWD/agents/bin/agents $HOME/.local/bin/agents
ln -sf $PWD/agents/bin/agents-panel $HOME/.local/bin/agents-panel
ln -sf $PWD/agents/systemd/agents-usage.service $HOME/.config/systemd/user/agents-usage.service
ln -sf $PWD/agents/systemd/agents-usage.timer $HOME/.config/systemd/user/agents-usage.timer
if command -v uv >/dev/null; then
  AGENTS_VENV=$HOME/.local/share/agents/venv
  [ -x $AGENTS_VENV/bin/python ] || uv venv --quiet --python 3.13 $AGENTS_VENV
  uv pip install --quiet --python $AGENTS_VENV/bin/python PySide6-Essentials==6.12.0
else
  echo "uv não encontrado: instale-o e rode de novo para criar o venv do painel de agentes"
fi
systemctl --user daemon-reload
systemctl --user enable --now agents-usage.timer
