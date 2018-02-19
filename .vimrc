"Configure Vundle
set nocompatible
filetype off
set cursorline

"Vundle config
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()
set backspace=indent,eol,start

"need this to install Vundle
"Plugin 'gmarik/Vundle.vim'
Plugin 'VundleVim/Vundle.vim'

" ---- Plugins ----
Plugin 'sickill/vim-monokai'
Plugin 'dracula/vim'
Plugin 'JamshedVesuna/vim-markdown-preview'
Plugin 'mattn/emmet-vim'
Plugin 'davidhalter/jedi-vim'
Plugin 'vim-airline/vim-airline'
Plugin 'vim-airline/vim-airline-themes'
Plugin 'scrooloose/nerdtree'
Plugin 'shougo/neocomplete.vim'
Plugin 'ryanoasis/vim-devicons'
Plugin 'tiagofumo/vim-nerdtree-syntax-highlight'
" Plugin 'syntastic'
Plugin 'joonty/vdebug'
Plugin 'airblade/vim-gitgutter'
Plugin 'pangloss/vim-javascript'
Plugin 'valloric/youcompleteme'
Plugin 'w0rp/ale'
 Plugin 'Yggdroot/indentLine'
"Plugin 'nathanaelkane/vim-indent-guides'
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
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#formatter = 'unique_tail'
let g:airline#extensions#tabline#buffer_idx_mode = 1
autocmd FileType python setlocal completeopt-=preview

" ---- NERDTree ----
"autocmd vimenter * NERDTree
let g:NERDTreeDirArrowExpandable = "\ue5ff"
let g:NERDTreeDirArrowCollapsible = "\ue5fe"
let g:NERDTreeHighlightFolders = 1 
let g:NERDTreeHighlightFoldersFullName = 1
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

" ---- Python -----
map lo :lopen<CR>
map lc :lclose<CR>

" ---- Indent Guide -----

 let g:indentLine_enabled = 0
 let g:indentLine_first_char = ""
 map gut :IndentLinesToggle<CR>
 let g:indentLine_fileType = ['c', 'cpp', 'go', 'js', 'py', 'json', 'php']
 let g:indentLine_concealcursor = ''

"let g:indent_guides_enable_on_vim_startup = 1
"let g:indent_guides_auto_colors = 0
"hi IndentGuidesOdd  ctermbg=233
"hi IndentGuidesEven ctermbg=234
set ts=4 sw=4 et
"let g:indent_guides_start_level = 2
"let g:indent_guides_guide_size = 1
"map gut :IndentGuidesToggle<CR>

nnoremap j :m .+1<CR>==
nnoremap k :m .-2<CR>==
inoremap j <Esc>:m .+1<CR>==gi
inoremap k <Esc>:m .-2<CR>==gi
vnoremap j :m '>+1<CR>gv=gv
vnoremap k :m '<-2<CR>gv=gv
