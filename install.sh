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

# Painel de agentes (ai-usage: uso de Claude/Codex/OpenRouter no polybar)
# libxcb-cursor0/libxkbcommon-x11-0/libegl1: exigidas pelo plugin xcb do Qt 6 (PySide6)
# libnotify-bin (notify-send) + libglib2.0-bin (gdbus): alertas e botão de trocar conta
sudo apt-get update
sudo apt-get install -y python3 pipx alacritty picom xdg-utils libnotify-bin libglib2.0-bin \
  libxcb-cursor0 libxkbcommon-x11-0 libegl1 libfontconfig1 libdbus-1-3 curl xz-utils fontconfig fonts-hack-ttf
command -v uv >/dev/null || pipx install uv
export PATH="$HOME/.local/bin:$PATH"
# Hack Nerd Font >= 3.5: traz os logos do Claude/OpenAI (U+EC82/U+EC81) usados na barra
if ! fc-list ":family=Hack Nerd Font:charset=ec82" | grep -q .; then
  NF_TMP=$(mktemp -d)
  curl -fsSL -o "$NF_TMP/Hack.tar.xz" https://github.com/ryanoasis/nerd-fonts/releases/download/v3.5.1/Hack.tar.xz &&
    echo "cdd389472e10e2261520140ff1b382b4f8a226af5fd0b2735b975d31151d9c3c  $NF_TMP/Hack.tar.xz" | sha256sum -c --quiet - &&
    mkdir -p "$HOME/.local/share/fonts/Hack" &&
    tar -xJf "$NF_TMP/Hack.tar.xz" -C "$HOME/.local/share/fonts/Hack" &&
    fc-cache -f "$HOME/.local/share/fonts" ||
    echo "AVISO: falha ao instalar a Hack Nerd Font v3.5.1"
  rm -rf "$NF_TMP"
fi
# Sem pacote apt equivalente (o fonts-font-awesome do 22.04 é a 4.7): só avisa.
fc-list | grep -q "Font Awesome 5 Free" || echo "AVISO: instale a Font Awesome 5 Free (ícone da barra) em ~/.local/share/fonts"
# O app fica em repo próprio; o install.sh dele cuida do uv tool, dos shims e do timer.
AI_USAGE_DIR="$HOME/projects/ai-usage"
[ -d "$AI_USAGE_DIR" ] || git clone https://github.com/paraizofelipe/ai-usage "$AI_USAGE_DIR"
"$AI_USAGE_DIR/install.sh"
