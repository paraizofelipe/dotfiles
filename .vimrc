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
Plugin 'syntastic'
Plugin 'joonty/vdebug'

call vundle#end()

" ---- Theme ----
syntax on 
colorscheme monokai
set number
set t_Co=256
set laststatus=2

" ---- TABS ----
set tabstop=2                                                                                                                           │drwxr-xr-x  3 felipe felipe  4096 ago 20 18:24 .java
set shiftwidth=2                                                                                                                        │drwx------  3 felipe felipe  4096 ago 20 17:16 .local
set autoindent 
set pastetoggle=<F2>

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

" ---- SYNTASTIC ----
set statusline+=%#warningmsg#
set statusline+=%{SyntasticStatuslineFlag()}
set statusline+=%*

let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 1
let g:syntastic_check_on_open = 1
let g:syntastic_check_on_wq = 0
let g:syntastic_python_checkers = ['pylint']
let g:syntastic_javascript_checkers = ['eslint']
