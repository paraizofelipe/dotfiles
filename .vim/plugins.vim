set nocompatible
filetype off

set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()

Plugin 'VundleVim/Vundle.vim'

Plugin 'elixir-lang/vim-elixir'
Plugin 'slashmili/alchemist.vim'
Plugin 'sickill/vim-monokai'
Plugin 'joshdick/onedark.vim'
Plugin 'vim-airline/vim-airline-themes'
Plugin 'ryanoasis/vim-devicons'
Plugin 'mattn/emmet-vim'
Plugin 'myhere/vim-nodejs-complete'
Plugin 'davidhalter/jedi-vim'
Plugin 'vim-airline/vim-airline'
Plugin 'scrooloose/nerdtree'
Plugin 'shougo/neocomplete.vim'
Plugin 'stanangeloff/php.vim'
Plugin 'shawncplus/phpcomplete.vim'
Plugin 'tpope/vim-fugitive'
Plugin 'sjl/gundo.vim'
Plugin 'majutsushi/tagbar'
Plugin 'Xuyuanp/nerdtree-git-plugin'
Plugin 'airblade/vim-gitgutter'
Plugin 'w0rp/ale'
Plugin 'terryma/vim-multiple-cursors'
Plugin 'fatih/vim-go'
Plugin 'posva/vim-vue'
Plugin 'nsf/gocode', {'rtp': 'vim/'}
Plugin 'rust-lang/rust.vim'
Plugin 'xolox/vim-misc'
Plugin 'plasticboy/vim-markdown'
" Plugin 'xolox/vim-easytags'
Plugin 'valloric/youcompleteme'
Plugin 'scrooloose/nerdcommenter'
Plugin 'junegunn/gv.vim'
Plugin 'Yggdroot/indentLine'
Plugin 'qpkorr/vim-bufkill'
Plugin 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plugin 'junegunn/fzf.vim'

call vundle#end()
filetype plugin indent on
"-----------------


" ---- START vim-airline ----
let g:airline_theme='simple'
let g:airline_powerline_fonts = 1
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#formatter = 'unique_tail'
let g:airline#extensions#tabline#buffer_idx_mode = 1

autocmd FileType python setlocal completeopt-=preview
" ---- END vim-airline ---


" ---- START indentLine ----
let g:indentLine_enabled = 0
let g:indentLine_char = '│'
let g:indentLine_concealcursor = 0
let g:indentLine_conceallevel = 1
let g:indentLine_faster = 1
let g:indentLine_color_term = 239
let g:indentLine_color_gui = '#3B4048'
let g:indentLine_color_tty_light = 7 " (default: 4)
let g:indentLine_color_dark = 1 " (default: 2)
let g:indentLine_fileType = ['c', 'cpp', 'go', 'js', 'py', 'json', 'php']
" ---- END indentLine ----


" ---- START NERDTree ----
"autocmd vimenter * NERDTree
let g:NERDTreeDirArrowExpandable = ""
let g:NERDTreeDirArrowCollapsible = ""
let g:NERDTreeHighlightFolders = 1 
let g:NERDTreeHighlightFoldersFullName = 1

autocmd bufenter * if (winnr("$") == 1 && exists("b:NERDTree") && b:NERDTree.isTabTree()) | q | endif

" NERDTree File highlighting
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
" ---- END NERDTree ----


" ---- START emmet ----
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
" ---- END emmet -----


" ---- START vim-multiple-cursor ----
let g:multi_cursor_start_key='<F6>'
let g:multi_cursor_next_key='<C-m>'
let g:multi_cursor_prev_key='<C-p>'
let g:multi_cursor_skip_key='<C-x>'
let g:multi_cursor_quit_key='<Esc>'
" ---- END vim-multiple-cursors ---- 


" ---- START nerdcomment ----
let g:NERDSpaceDelims = 1
let g:NERDCompactSexyComs = 1
let g:NERDDefaultAlign = 'left'
let g:NERDAltDelims_java = 1
let g:NERDCommentEmptyLines = 1
let g:NERDTrimTrailingWhitespace = 1
" ---- END ---

" ---- START ale ----
let g:ale_linters = { 'elixir': ['elixir-ls'], }
" ----- END ale -----

" ---- START vim-javascript ----
" let g:javascript_plugin_flow = 1
let g:javascript_plugin_ngdoc = 1
let g:javascript_plugin_jsdoc = 1
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
" ---- END vim-javascript ---

" ---- START youcomplete ----
let g:ycm_semantic_triggers =  {
  \   'c' : ['->', '.'],
  \   'cpp,objcpp' : ['->', '.', '::'],
  \   'php' : ['->', '::'],
  \   'cs,java,javascript,typescript,d,python,perl6,scala,vb,elixir,go' : ['.'],
  \   'ruby' : ['.', '::'],
  \ }
" ---- END youcomplete ----

" ---- START fzf -----
"
" ---- END fzf -----
