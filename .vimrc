"Configure Vundle
set nocompatible
filetype off
set cursorline

nnoremap <C-y> "+y
vnoremap <C-y> "+y
nnoremap <C-p> "+p
vnoremap <C-p> "+p

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
Plugin 'myhere/vim-nodejs-complete'
Plugin 'vim-airline/vim-airline-themes'
Plugin 'scrooloose/nerdtree'
Plugin 'shougo/neocomplete.vim'
Plugin 'stanangeloff/php.vim'
Plugin 'shawncplus/phpcomplete.vim'
Plugin 'ryanoasis/vim-devicons'
Plugin 'tpope/vim-fugitive'
Plugin 'sjl/gundo.vim'
Plugin 'majutsushi/tagbar'
Plugin 'Xuyuanp/nerdtree-git-plugin'
Plugin 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plugin 'junegunn/fzf.vim'
" Plugin 'tiagofumo/vim-nerdtree-syntax-highlight'
" Plugin 'syntastic'
Plugin 'joonty/vdebug'
Plugin 'airblade/vim-gitgutter'
Plugin 'pangloss/vim-javascript'
Plugin 'valloric/youcompleteme'
Plugin 'w0rp/ale'
Plugin 'Yggdroot/indentLine'
Plugin 'terryma/vim-multiple-cursors'
"Plugin 'nathanaelkane/vim-indent-guides'
Plugin 'fatih/vim-go'
Plugin 'posva/vim-vue'
Plugin 'nsf/gocode', {'rtp': 'vim/'}
Plugin 'rust-lang/rust.vim'
Plugin 'xolox/vim-misc'
Plugin 'xolox/vim-easytags'
Plugin 'junegunn/gv.vim'
" Plugin 'bling/vim-bufferline'
Plugin 'qpkorr/vim-bufkill'
" Plugin 'mileszs/ack.vim'
Plugin 'rking/ag.vim'
Plugin 'scrooloose/nerdcommenter'

call vundle#end()

let mapleader = " "

" ---- Theme ----
syntax on 
colorscheme monokai
set number
set t_Co=256
set laststatus=2
set colorcolumn=120
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

nmap <leader>1 <Plug>AirlineSelectTab1
nmap <leader>2 <Plug>AirlineSelectTab2
nmap <leader>3 <Plug>AirlineSelectTab3
nmap <leader>4 <Plug>AirlineSelectTab4
nmap <leader>5 <Plug>AirlineSelectTab5
nmap <leader>6 <Plug>AirlineSelectTab6
nmap <leader>7 <Plug>AirlineSelectTab7
nmap <leader>8 <Plug>AirlineSelectTab8
nmap <leader>9 <Plug>AirlineSelectTab9
nmap <leader>, <Plug>AirlineSelectPrevTab
nmap <leader>. <Plug>AirlineSelectNextTab

nmap <leader>w :BW<CR>
nmap <leader>d :BD<CR>

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

let g:easytags_syntax_keyword = 'always'

" NERDTress File highlighting
function! NERDTreeHighlightFile(extension, fg, bg, guifg, guibg)
 exec 'autocmd filetype nerdtree highlight ' . a:extension .' ctermbg='. a:bg .' ctermfg='. a:fg .' guibg='. a:guibg .' guifg='. a:guifg
 exec 'autocmd filetype nerdtree syn match ' . a:extension .' #^\s\+.*'. a:extension .'$#'
endfunction

call NERDTreeHighlightFile('jade', 'green', 'none', 'green', '#151515')
call NERDTreeHighlightFile('ini', 'yellow', 'none', 'yellow', '#151515')
call NERDTreeHighlightFile('md', 'blue', 'none', '#3366FF', '#151515')
call NERDTreeHighlightFile('yml', 'yellow', 'none', 'yellow', '#151515')
call NERDTreeHighlightFile('config', 'yellow', 'none', 'yellow', '#151515')
call NERDTreeHighlightFile('conf', 'yellow', 'none', 'yellow', '#151515')
call NERDTreeHighlightFile('json', 'yellow', 'none', 'yellow', '#151515')
call NERDTreeHighlightFile('html', 'yellow', 'none', 'yellow', '#151515')
call NERDTreeHighlightFile('styl', 'cyan', 'none', 'cyan', '#151515')
call NERDTreeHighlightFile('css', 'cyan', 'none', 'cyan', '#151515')
call NERDTreeHighlightFile('coffee', 'Red', 'none', 'red', '#151515')
call NERDTreeHighlightFile('js', 'Red', 'none', '#ffa500', '#151515')
call NERDTreeHighlightFile('php', 'Magenta', 'none', '#ff00ff', '#151515')
call NERDTreeHighlightFile('go', '905532', 'none', '#ff00ff', '#151515')
call NERDTreeHighlightFile('py', 'blue', 'none', '#ff00ff', '#151515')

" ---- EMMET ----
let g:user_emmet_install_global = 0
autocmd FileType html,vue,css,php EmmetInstall
let g:user_emmet_leader_key='<C-e>'
let g:user_emmet_settings = {
  \  'php' : {
  \    'extends' : 'html',
  \    'filters' : 'c',
  \  },
  \  'xml' : {
  \    'extends' : 'html',
  \  },
  \  'haml' : {
  \    'extends' : 'html',
  \  },
  \}

" ---- MULTI CURSOR ----
let g:multi_cursor_start_key='<F6>'
let g:multi_cursor_next_key='<C-m>'
let g:multi_cursor_prev_key='<C-p>'
let g:multi_cursor_skip_key='<C-x>'
let g:multi_cursor_quit_key='<Esc>'

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
map ln :lnext<CR>

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

map tu :UpdateTags<CR>

inoremap j :m .+1<CR>==
inoremap k :m .-2<CR>==
nnoremap j :m .+1<CR>==
nnoremap k :m .-2<CR>==
inoremap j <Esc>:m .+1<CR>==gi
inoremap k <Esc>:m .-2<CR>==gi
vnoremap j :m '>+1<CR>gv=gv
vnoremap k :m '<-2<CR>gv=gv

nnoremap <F4> :GundoToggle<CR>

if has('python3')
    let g:gundo_prefer_python3 = 1
endif

nmap <F8> :TagbarToggle<CR>
let g:tagbar_ctags_bin = '/usr/bin/ctags'

let vim_markdown_preview_github=1
let vim_markdown_preview_toggle=1

set foldmethod=indent
set foldlevel=20
" set foldopen=all
hi Folded ctermbg=234
hi Pmenu ctermbg=253 ctermfg=232

set regexpengine=0

nnoremap <leader>c :call ShowSpecialChar()<CR>

function ShowNoAsciiChar()
    syntax off
    syntax match nonascii "[^\x00-\x7F]"
    highlight nonascii ctermfg=0 ctermbg=1
endfunction


let g:ale_linters = { 'javascript': ['eslint'], }

" let g:javascript_plugin_flow = 1
let g:javascript_plugin_ngdoc = 1
let g:javascript_plugin_jsdoc = 1

augroup javascript_folding
    au!
    au FileType javascript setlocal foldmethod=syntax
augroup END

" let g:javascript_conceal_function             = "ƒ"
" let g:javascript_conceal_null                 = "ø"
" let g:javascript_conceal_this                 = "@"
" let g:javascript_conceal_return               = "⇚"
" let g:javascript_conceal_undefined            = "¿"
" let g:javascript_conceal_NaN                  = "ℕ"
" let g:javascript_conceal_prototype            = "¶"
" let g:javascript_conceal_static               = "•"
" let g:javascript_conceal_super                = "Ω"
" let g:javascript_conceal_arrow_function       = "⇒"
" let g:javascript_conceal_noarg_arrow_function = "🞅"
" let g:javascript_conceal_underscore_arrow_function = "🞅"

" custom folding function
" http://dhruvasagar.com/2013/03/28/vim-better-foldtext
function! NeatFoldText()
  let line = ' ' . substitute(getline(v:foldstart), '^\s*"\?\s*\|\s*"\?\s*{{' . '{\d*\s*', '', 'g') . ' '
  let lines_count = v:foldend - v:foldstart + 1
  let lines_count_text = '| ' . printf("%10s", lines_count . ' lines') . ' |'
  let foldchar = matchstr(&fillchars, 'fold:\zs.')
  let foldtextstart = strpart('+' . repeat(foldchar, v:foldlevel*2) . line, 0, (winwidth(0)*2)/3)
  let foldtextend = lines_count_text . repeat(foldchar, 8)
  let foldtextlength = strlen(substitute(foldtextstart . foldtextend, '.', 'x', 'g')) + &foldcolumn
  return foldtextstart . repeat(foldchar, winwidth(0)-foldtextlength) . foldtextend
endfunction
set foldtext=NeatFoldText()
