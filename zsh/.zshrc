

export ZSH="$HOME/.oh-my-zsh"

ZSH_THEME="robbyrussell"
# ZSH_THEME="spaceship"

plugins=(git)

fpath+=~/.zfunc
autoload -Uz compinit && compinit

source $ZSH/oh-my-zsh.sh

# source $ZSH/custom/plugins/zsh-vi-mode/zsh-vi-mode.zsh
source $ZSH/custom/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
source $ZSH/custom/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source $ZSH/plugins/fzf/fzf.plugin.zsh

export EDITOR='nvim'


export BAT_THEME=gruvbox-dark
export HIGHLIGHT_STYLE=gruvbox-dark-medium

export XDG_DATA_DIRS=$XDG_DATA_DIRS:~/.local/share/flatpak/exports/share/applications:/var/lib/flatpak/exports/share/applications

alias k="kubectl"

stty -ixon -ixoff


export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

export I3BLOCKS_CONTRIB=~/projects/i3blocks-contrib

alias ls="exa"

export USE_GKE_GCLOUD_AUTH_PLUGIN=True

# alias go="grc go"

# export PYENV_VIRTUALENV_DISABLE_PROMPT=1
export PATH="$PYENV_ROOT/bin:$PATH"
export PYENV_ROOT="$HOME/.pyenv"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

export PYTHONBREAKPOINT=pdb.set_trace
# export PYTHONBREAKPOINT="ipdb.set_trace"

# export PATH="$HOME/.poetry/bin:$PATH"
# source $HOME/.poetry/env
source $HOME/.user.env
source $HOME/.database.env

eval "$(direnv hook zsh)"

[ -s ~/.luaver/luaver ] && . ~/.luaver/luaver

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/home/paraizo/google-cloud-sdk/path.zsh.inc' ]; then . '/home/paraizo/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/home/paraizo/google-cloud-sdk/completion.zsh.inc' ]; then . '/home/paraizo/google-cloud-sdk/completion.zsh.inc'; fi

PROG=es
source ~/projects/esctl/autocomplete/zsh_autocomplete

export KUBECONFIG=$HOME/.kube/kubeconfig.yaml
source <(kubectl completion zsh)
alias k="kubectl"
# compdef __start_kubectl k

# Generated for envman. Do not edit.
[ -s "$HOME/.config/envman/load.sh" ] && source "$HOME/.config/envman/load.sh"
nvm use default >/dev/null

export GOPATH=~/go
export GOROOT=/usr/local/go
export PATH=$PATH:$GOROOT/bin:$GOPATH/bin

######### Unique localbin

localbin="$HOME/.local/bin"
path=(${path[@]:#"$localbin"})
path+=$localbin
export PATH=$PATH:$localbin
export PATH
export PATH="<path to install directory>/gcc-arm-none-eabi-7-2018-q2-update/bin:${PATH}"

export NVIM_APPNAME=lazyvim
# export NVIM_APPNAME=nvim-orig

#### Prompt customization

setopt PROMPT_SUBST
autoload -Uz vcs_info

C_FG="%F{223}"        # fg: #ebdbb2
C_BLACK="%F{235}"     # bg0_h: #1d2021
C_RESET="%f"

BG_BLUE="%K{66}"      # blue: #458588
BG_AQUA="%K{72}"      # aqua: #689d6a
BG_GREEN="%K{106}"    # green: #98971a
BG_ORANGE="%K{166}"   # orange: #d65d0e
BG_RESET="%k"

SEPARATOR_RIGHT=""
SEPARATOR_THIN=""

zstyle ':vcs_info:git:*' formats "${BG_GREEN}${C_BLACK} ${SEPARATOR_THIN} %b ${BG_RESET}${C_GREEN}"

precmd() {
  # Atualiza as informações do Git
  vcs_info

  # Define o prompt do lado direito (RPROMPT)
  # Mostra o código de erro do último comando, se for diferente de zero
  RPROMPT="${C_RED}%(?..%? ${SEPARATOR_THIN} )%f"
}


PROMPT="${BG_YELLOW}${C_BLACK}${USER}${SEPARATOR_RIGHT}{BG_RESET} %~ ${BG_RESET}"

# PROMPT="${BG_BLUE}${C_WHITE} %~ ${BG_RESET}${C_BLUE}"
# PROMPT+="${SEPARATOR_RIGHT}${vcs_info_msg_0_}"
# PROMPT+="${SEPARATOR_RIGHT}${C_RESET} "
