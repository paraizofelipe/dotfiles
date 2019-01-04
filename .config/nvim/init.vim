" Plugins
call plug#begin('~/.config/nvim/plugged')

  function! DoRemote(arg)
    UpdateRemotePlugins
  endfunction

" looking
  Plug 'ryanoasis/vim-devicons'
  Plug 'Yggdroot/indentLine'
  Plug 'tomasr/molokai'
  Plug 'sickill/vim-monokai'
  Plug 'dracula/vim', { 'as': 'dracula' }
  Plug 'morhetz/gruvbox'
  Plug 'joshdick/onedark.vim'
  Plug 'vim-airline/vim-airline-themes'
  Plug 'vim-airline/vim-airline'
  Plug 'altercation/vim-colors-solarized'
  Plug 'myusuf3/numbers.vim'
  Plug 'powerman/vim-plugin-AnsiEsc'
" completion/templating
  Plug 'Shougo/deoplete.nvim', { 'do': function('DoRemote'), 'tag': '*' }
" command extension
" utils
  Plug 'neomake/neomake'
  Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
  Plug 'junegunn/fzf.vim'
  Plug 'qpkorr/vim-bufkill'
  Plug 'tpope/vim-fugitive'
  Plug 'airblade/vim-gitgutter'
  Plug 'sheerun/vim-polyglot'
  Plug 'sjl/gundo.vim'
" misc
  Plug 'numirias/semshi', {'do': ':UpdateRemotePlugins'}
" documentation
  Plug 'iamcco/markdown-preview.nvim', { 'do': 'cd app & yarn install'  }
" navegation
  Plug 'scrooloose/nerdtree'
" go/lang
  Plug 'zchee/deoplete-go', { 'do': 'make'}
  Plug 'fatih/vim-go', { 'do': ':GoUpdateBinaries' }
" javascript/lang
  Plug 'carlitux/deoplete-ternjs'
  Plug 'ternjs/tern_for_vim', { 'do': 'npm install && npm install -g tern' }
"typescript
  Plug 'Shougo/vimproc.vim', { 'do': 'make' }
  Plug 'Quramy/tsuquyomi', { 'do': 'npm install -g typescript' }
  Plug 'mhartington/deoplete-typescript' 
  Plug 'myhere/vim-nodejs-complete'
" elixir/lang
  Plug 'slashmili/alchemist.vim'
" python/lang
  Plug 'davidhalter/jedi-vim'
  Plug 'zchee/deoplete-jedi'
  Plug 'plytophogy/vim-virtualenv'

call plug#end()

" deoplete }}}
  let g:deoplete#enable_at_startup = 1
  let g:deoplete#disable_auto_complete = 0
  let g:deoplete#enable_at_startup = 1
  let g:deoplete#enable_ignore_case = 1
  let g:deoplete#enable_smart_case = 1
  let g:deoplete#enable_camel_case = 1
  let g:deoplete#enable_refresh_always = 1
  let g:deoplete#max_abbr_width = 0
  let g:deoplete#max_menu_width = 0
  let g:deoplete#omni#input_patterns = get(g:,'deoplete#omni#input_patterns',{})
  call deoplete#custom#set('_', 'matchers', ['matcher_full_fuzzy'])<Paste>


  inoremap <silent><expr> <TAB> pumvisible() ? "\<C-n>" : <SID>check_back_space() ? "\<TAB>" : deoplete#mappings#manual_complete()
  
  function! s:check_back_space() abort "{{{
    let col = col('.') - 1
    return !col || getline('.')[col - 1]  =~ '\s'
  endfunction "}}}
"{{{

" ternjs }}}
  let g:tern_request_timeout = 1
  let g:tern_request_timeout = 6000
  let g:tern#command = ["tern"]
  let g:tern#arguments = ["--persistent"]
  let g:deoplete#sources#tss#javascript_support = 1
" {{{

" alchemist {{{
  let g:alchemist_tag_map = '<C-L>'
  let g:alchemist_tag_stack_map = '<C-S>'
" }}}

" jedi-vim {{{
  if exists("$VIRTUAL_ENV")
      let g:python3_host_prog=substitute(system("which -a python3 | head -n2 | tail -n1"), "\n", '', 'g')
  else
      let g:python3_host_prog=substitute(system("which python3"), "\n", '', 'g')
  endif
"}}}

" neomake {{{
  augroup localneomake
    autocmd! BufWritePost * Neomake
  augroup END

  let g:neomake_javascript_enable_makers = ['eslint']
  let g:neomale_python_enabled_makers = ['pylint']
  let g:neomake_markdown_enabled_makers = []
  let g:neomake_elixir_enabled_makers = ['mix', 'credo']
"}}}

" nvim-gdb {{{
  let g:loaded_nvimgdb = 1
  let g:nvimgdb_config_override = {
            \ 'key_next': 'n',
            \ 'key_step': 's',
            \ 'key_finish': 'f',
            \ 'key_continue': 'c',
            \ 'key_until': 'u',
            \ 'key_breakpoint': 'b',
            \ }
" }}}

" markdown-preview {{{
  let g:mkdp_preview_options = {
    \ 'mkit': {},
    \ 'katex': {},
    \ 'uml': {},
    \ 'maid': {}
    \ }
" }}}

" vim-polyglot {{{
  let g:polyglot_disabled = ['go']
" }}}

" javascript
" go
" elixir
" python
