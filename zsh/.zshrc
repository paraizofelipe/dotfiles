# ===================================================================
#  CONFIGURAÇÕES GERAIS E VARIÁVEIS DE AMBIENTE
# ===================================================================
export ZSH="$HOME/.oh-my-zsh"
export EDITOR='nvim'
export BAT_THEME=gruvbox-dark
export HIGHLIGHT_STYLE=gruvbox-dark-medium
export USE_GKE_GCLOUD_AUTH_PLUGIN=True
export PYTHONBREAKPOINT=pdb.set_trace
export NVIM_APPNAME=nvim
export I3BLOCKS_CONTRIB=~/projects/i3blocks-contrib
export KUBECONFIG=$HOME/.kube/kubeconfig.yaml

# Desativa o prompt do virtualenv do pyenv, já que temos um prompt customizado
# export PYENV_VIRTUALENV_DISABLE_PROMPT=1

# ===================================================================
#  GERENCIAMENTO DO PATH (AGRUPADO PARA MELHOR PERFORMANCE)
# ===================================================================
# Garante que o .local/bin esteja no PATH e sem duplicatas
localbin="$HOME/.local/bin"
typeset -U path
path=($localbin $path)

# Pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"

# Go
export GOPATH=~/go
export GOROOT=/usr/local/go
export PATH=$PATH:$GOROOT/bin:$GOPATH/bin

# Google Cloud SDK (carregado mais abaixo)
# Poetry (descomente se usar)
# export PATH="$HOME/.poetry/bin:$PATH"

# ===================================================================
#  OH MY ZSH E PLUGINS
# ===================================================================
ZSH_THEME="robbyrussell"
plugins=(git)

# OTIMIZAÇÃO: compinit (sistema de autocompletar)
# Isso verifica se um arquivo de cache (.zcompdump) existe e é recente.
# Evita a reconstrução desnecessária do autocompletar a cada inicialização.
autoload -Uz compinit
if [[ -n ~/.zcompdump(#qN.mh+24) ]]; then
  compinit -i
else
  compinit -C
fi;

# Carrega o Oh My Zsh
source $ZSH/oh-my-zsh.sh

# Carrega plugins manualmente (geralmente mais rápido que pelo array do OMZ)
source $ZSH/custom/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
source $ZSH/custom/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source $ZSH/plugins/fzf/fzf.plugin.zsh

# ===================================================================
#  INICIALIZAÇÃO DE FERRAMENTAS (COM OTIMIZAÇÕES)
# ===================================================================

# --- Pyenv ---
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# --- Google Cloud SDK ---
if [ -f '/home/paraizo/google-cloud-sdk/path.zsh.inc' ]; then . '/home/paraizo/google-cloud-sdk/path.zsh.inc'; fi
if [ -f '/home/paraizo/google-cloud-sdk/completion.zsh.inc' ]; then . '/home/paraizo/google-cloud-sdk/completion.zsh.inc'; fi

# --- Direnv ---
eval "$(direnv hook zsh)"

# --- Outras ferramentas ---
[ -s ~/.luaver/luaver ] && . ~/.luaver/luaver
[ -s "$HOME/.config/envman/load.sh" ] && source "$HOME/.config/envman/load.sh"
source ~/projects/esctl/autocomplete/zsh_autocomplete

# --- kubectl completion (OTIMIZADO) ---
# OTIMIZAÇÃO: Carrega o autocompletar a partir de um cache.
# O comando `source <(kubectl completion zsh)` é lento. Em vez disso, geramos o
# arquivo uma vez e o carregamos diretamente.
#
# Para gerar o cache, execute este comando UMA VEZ no seu terminal:
#   kubectl completion zsh > ~/.zsh/completion/_kubectl
#
# (Certifique-se de que o diretório ~/.zsh existe: mkdir -p ~/.zsh)
fpath+=~/.zsh/completion
if [ -f ~/.zsh/completion/_kubectl ]; then
  source ~/.zsh/completion/_kubectl
fi

# --- NVM (Node Version Manager) (OTIMIZADO) ---
# OTIMIZAÇÃO: Carregamento "preguiçoso" (lazy loading) do NVM.
# O NVM não será carregado até que você use um comando relacionado (nvm, node, npm, etc.).
# Isso remove a maior causa de lentidão na inicialização.
export NVM_DIR="$HOME/.nvm"
# lazy_load_nvm() {
#   [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
#   [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
#
#   # Remove as funções de lazy load para que não executem novamente
#   unset -f lazy_load_nvm nvm node npm npx yarn pnpm
# }

[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Adiciona ganchos para os comandos do Node.js
# Quando você digitar um desses, `lazy_load_nvm` será chamado primeiro.
# alias nvm='lazy_load_nvm && nvm'
# alias node='lazy_load_nvm && node'
# alias npm='lazy_load_nvm && npm'
# alias npx='lazy_load_nvm && npx'
# alias yarn='lazy_load_nvm && yarn'
# alias pnpm='lazy_load_nvm && pnpm'

# ===================================================================
#  ALIASES E CONFIGURAÇÕES FINAIS
# ===================================================================
alias k="kubectl"
alias ls="exa"

stty -ixon -ixoff

# Carrega variáveis de ambiente locais (se existirem)
[ -f "$HOME/.user.env" ] && source "$HOME/.user.env"
[ -f "$HOME/.database.env" ] && source "$HOME/.database.env"

# ===================================================================
#  PROMPT CUSTOMIZADO (GRUVBOX)
# ===================================================================
setopt PROMPT_SUBST
autoload -Uz vcs_info

# Paleta de cores Gruvbox (atualizada)
C_FG="%F{223}"        # fg: #ebdbb2
C_BLACK="%F{235}"     # bg0_h: #1d2021
C_RESET="%f"
BG_GRAY="%K{237}"     # bg1: #3c3836
BG_AQUA="%K{72}"      # aqua: #689d6a
BG_ORANGE="%K{166}"   # orange: #d65d0e
BG_RED="%K{124}"      # red: #cc241d
BG_BLUE="%K{66}"      # blue: #458588
BG_RESET="%k"

# Símbolos e Ícones
SEPARATOR=""
ICON_GIT=""
ICON_PYTHON=""

zstyle ':vcs_info:git:*' formats " ${ICON_GIT} %b"

precmd() {
  vcs_info
  if [[ -n "$VIRTUAL_ENV" ]]; then
    PYENV_INFO=$(basename "$VIRTUAL_ENV")
  else
    PYENV_INFO=""
  fi

  local prompt_string=""
  local last_bg_code=""

  # Segmento 1: Usuário (cinza)
  last_bg_code="237" # gray
  prompt_string+="${BG_GRAY}${C_FG} %n "

  # Segmento 2: Diretório (azul)
  prompt_string+="${BG_BLUE}%F{$last_bg_code}${SEPARATOR}${C_BLACK} %. "
  last_bg_code="66" # blue

  # Segmento 3: Branch do Git (laranja) - Sempre visível
  prompt_string+="${BG_ORANGE}%F{$last_bg_code}${SEPARATOR}${C_BLACK}"
  if [[ -n "$vcs_info_msg_0_" ]]; then
    prompt_string+="${vcs_info_msg_0_} "
  else
    prompt_string+=" " # Adiciona um espaço para manter o segmento aberto
  fi
  last_bg_code="166" # orange

  # Segmento 4: Ambiente Virtual Python (vermelho) - Sempre visível
  prompt_string+="${BG_RED}%F{$last_bg_code}${SEPARATOR}${C_BLACK}"
  if [[ -n "$PYENV_INFO" ]]; then
    prompt_string+=" ${ICON_PYTHON} ${PYENV_INFO} "
  else
    prompt_string+=" " # Adiciona um espaço para manter o segmento aberto
  fi
  last_bg_code="124" # red

  # Segmento Final
  prompt_string+="${BG_RESET}%F{$last_bg_code}${SEPARATOR}${C_RESET} "
  PROMPT=$prompt_string
}

# pnpm
export PNPM_HOME="/home/paraizo/.local/share/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
# pnpm end

# Painel de agentes: shims de claude/codex que aplicam a conta ativa
# (agents account use). Precisa vir depois de ~/.local/bin, onde estão os CLIs reais.
export PATH="$HOME/.local/share/agents/shims:$PATH"  # shims do ai-usage (conta ativa)
