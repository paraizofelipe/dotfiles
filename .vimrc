"Configure Vundle
set nocompatible
filetype off


"Vundle config
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()
set backspace=indent,eol,start

"need this to install Vundle
"Plugin 'gmarik/Vundle.vim'
Plugin 'VundleVim/Vundle.vim'

" ---- Plugins ----
Plugin 'sickill/vim-monokai'
Plugin 'JamshedVesuna/vim-markdown-preview'
Plugin 'mattn/emmet-vim'
Plugin 'davidhalter/jedi-vim'
Plugin 'vim-airline/vim-airline'
Plugin 'vim-airline/vim-airline-themes'
Plugin 'scrooloose/nerdtree'
Plugin 'shougo/neocomplete.vim'
" Plugin 'syntastic'
Plugin 'joonty/vdebug'
Plugin 'airblade/vim-gitgutter'
Plugin 'pangloss/vim-javascript'
" Plugin 'valloric/youcompleteme'
Plugin 'w0rp/ale'
Plugin 'Yggdroot/indentLine'
" Plugin 'nathanaelkane/vim-indent-guides'
Plugin 'fatih/vim-go'
Plugin 'posva/vim-vue'
Plugin 'nsf/gocode', {'rtp': 'vim/'}
" Plugin 'phildawes/racer'
Plugin 'rust-lang/rust.vim'

call vundle#end()

" ---- Theme ----
syntax on 
colorscheme monokai
set number
set t_Co=256
set laststatus=2
set colorcolumn=150
highlight ColorColumn ctermbg=234

" ---- TABS ----
set nowrap
set tabstop=2 
set shiftwidth=2
set autoindent 
set pastetoggle=<F2>
set relativenumber
set incsearch
set hlsearch

" ---- AIRLINE ----
let g:airline_theme='simple'
let g:airline_powerline_fonts = 1
autocmd FileType python setlocal completeopt-=preview

" ---- NERDTree ----
"autocmd vimenter * NERDTree
let g:NERDTreeDirArrowExpandable = '+'
let g:NERDTreeDirArrowCollapsible = '-'
filetype plugin indent on

map <C-n> :NERDTreeToggle<CR>
autocmd bufenter * if (winnr("$") == 1 && exists("b:NERDTree") && b:NERDTree.isTabTree()) | q | endif

" ---- EMMET ----
let g:user_emmet_install_global = 0
autocmd FileType html,css EmmetInstall
let g:user_emmet_leader_key='<C-Y>'

" ---- SYNTASTIC ----
" set statusline+=%#warningmsg#
" set statusline+=%{SyntasticStatuslineFlag()}
" set statusline+=%*

" ---- VIM-GO -----
map gob :GoBuild<CR>
map gor :GoRun<CR>
map goi :Goinstall<CR>

let g:indentLine_enabled = 1
let g:indentLine_first_char = ""
map gut :IndentLinesToggle<CR>
let g:indentLine_fileType = ['c', 'cpp', 'go', 'js', 'py', 'json', 'php']
let g:indentLine_concealcursor = ''

nnoremap j :m .+1<CR>==
nnoremap k :m .-2<CR>==
inoremap j <Esc>:m .+1<CR>==gi
inoremap k <Esc>:m .-2<CR>==gi
vnoremap j :m '>+1<CR>gv=gv
vnoremap k :m '<-2<CR>gv=gv
