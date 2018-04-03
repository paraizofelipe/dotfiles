set encoding=UTF-8


" ---- Theme ----
syntax on 
colorscheme monokai
set t_Co=256
set laststatus=2
set colorcolumn=123
highlight ColorColumn ctermbg=234

" ---- Editor ----
set cursorline
set nowrap
set tabstop=2 
set shiftwidth=2
set autoindent 
set pastetoggle=<F2>
set relativenumber
set incsearch
set hlsearch
set number

set regexpengine=0
set foldmethod=indent
set foldlevel=20
" set foldopen=all
hi Folded ctermbg=234
hi Pmenu ctermbg=253 ctermfg=232

source ~/.vim/plugins.vim
source ~/.vim/keys.vim
