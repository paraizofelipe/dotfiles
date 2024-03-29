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

export PATH=$PATH:$HOME/.local/bin

export GOPATH=~/go
export GOROOT=/usr/local/go
export PATH=$PATH:$GOROOT/bin:$GOPATH/bin

alias ls="exa"

export USE_GKE_GCLOUD_AUTH_PLUGIN=True

# alias go="grc go"

# export PYENV_VIRTUALENV_DISABLE_PROMPT=1
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

export PYTHONBREAKPOINT=pdb.set_trace

# export PATH="$HOME/.poetry/bin:$PATH"
# source $HOME/.poetry/env
source $HOME/.env
source $HOME/.database.env

eval "$(direnv hook zsh)"

[ -s ~/.luaver/luaver ] && . ~/.luaver/luaver

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/home/paraizo/google-cloud-sdk/path.zsh.inc' ]; then . '/home/paraizo/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/home/paraizo/google-cloud-sdk/completion.zsh.inc' ]; then . '/home/paraizo/google-cloud-sdk/completion.zsh.inc'; fi

# source <(kubectl completion zsh)
# alias k="kubectl"
# compdef __start_kubectl k
