set nofoldenable

set mouse =
set conceallevel=0
set cc=123

set tabstop=4 shiftwidth=4 expandtab
set foldmethod=indent

set list lcs=tab:\|\ 

highlight ColorColumn guibg=#3a3a3a

" nnoremap <C-b> :DlvToggleBreakpoint<CR>
" nnoremap <C-d> :DlvDebug

nnoremap Q q

" For local replace
nnoremap gr gd[{V%::s/<C-R>///gc<left><left><left>

" For global replace
nnoremap gR gD:%s/<C-R>///gc<left><left><left>

nnoremap <C-j> :m .+1<CR>==
nnoremap <C-k> :m .-2<CR>==
inoremap <C-j> <Esc>:m .+1<CR>==gi
inoremap <C-k> <Esc>:m .-2<CR>==gi
vnoremap <C-j> :m '>+1<CR>gv=gv
vnoremap <C-k> :m '<-2<CR>gv=gv

nnoremap <Tab> >>_
noremap <S-Tab> <<_
inoremap <S-Tab> <C-D>
vnoremap <Tab> >gv
vnoremap <S-Tab> <gv

let g:deoplete#sources#go#gocode_binary = $GOPATH.'/bin/gocode'

let g:python2_host_prog = expand("~/.config/nvim/python2-neovim-env/bin/python")
let g:python3_host_prog = expand("~/.config/nvim/python3-neovim-env/bin/python")

" let g:mergetool_layout = 'mr,b'
" let g:mergetool_prefer_revision = 'local'
nmap <leader>mt <plug>(MergetoolToggle)
nnoremap <silent> <leader>mb :call mergetool#toggle_layout('mr,b')<CR>

nmap <expr> <C-Left> &diff? '<Plug>(MergetoolDiffExchangeLeft)' : '<C-Left>'
nmap <expr> <C-Right> &diff? '<Plug>(MergetoolDiffExchangeRight)' : '<C-Right>'
nmap <expr> <C-Down> &diff? '<Plug>(MergetoolDiffExchangeDown)' : '<C-Down>'
nmap <expr> <C-Up> &diff? '<Plug>(MergetoolDiffExchangeUp)' : '<C-Up>'

" ---- clipboard ----
vnoremap <C-y> "+y
nnoremap <C-p> "+p
vnoremap <C-p> "+p


" ---- START NERDTree ----
autocmd vimenter * NERDTree
" let g:NERDTreeDirArrowExpandable = ""
" let g:NERDTreeDirArrowCollapsible = ""
let g:NERDTreeShowBookmarks = 1
let g:NERDTreeHighlightFolders = 1
let g:NERDTreeHighlightFoldersFullName = 1

" autocmd bufenter * if (winnr("$") == 1 && exists("b:NERDTree") && b:NERDTree.isTabTree()) | q | endif

" NERDTree File highlighting
"  function! NERDTreeHighlightFile(extension, fg, bg, guifg, guibg)
"  exec 'autocmd filetype nerdtree highlight ' . a:extension .' ctermbg='. a:bg .' ctermfg='. a:fg .' guibg='. a:guibg .' guifg='. a:guifg
"  exec 'autocmd filetype nerdtree syn match ' . a:extension .' #^\s\+.*'. a:extension .'$#'
" endfunction
"
let g:DevIconsEnableFoldersOpenClose = 1
let g:WebDevIconsUnicodeDecorateFolderNodes = 1
let g:NERDTreeGitStatusNodeColorization = 1
let g:NERDTreeGitStatusWithFlags = 1

let g:NERDTreeIndicatorMapCustom = {
    \ "Modified"  : "⋆",
    \ "Staged"    : "•",
    \ "Untracked" : "∘",
    \ "Dirty"     : "⁖",
    \ "Clean"     : "✔︎",
    \ }

let g:NERDTreeColorMapCustom = {
    \ "Modified"  : ["#528AB3", "NONE", "NONE", "NONE"],
    \ "Staged"    : ["#538B54", "NONE", "NONE", "NONE"],
    \ "Untracked" : ["#BE5849", "NONE", "NONE", "NONE"],
    \ "Dirty"     : ["#299999", "NONE", "NONE", "NONE"],
    \ "Clean"     : ["#87939A", "NONE", "NONE", "NONE"]
    \ }

" call NERDTreeHighlightFile('jade', 'green', 'none', 'green', '#282c34')
" call NERDTreeHighlightFile('ini', 'yellow', 'none', 'yellow', '#282c34')
" call NERDTreeHighlightFile('md', 'blue', 'none', '#3366FF', '#282c34')
" call NERDTreeHighlightFile('yml', 'yellow', 'none', 'yellow', '#282c34')
" call NERDTreeHighlightFile('config', 'yellow', 'none', 'yellow', '#282c34')
" call NERDTreeHighlightFile('conf', 'yellow', 'none', 'yellow', '#282c34')
" call NERDTreeHighlightFile('json', 'yellow', 'none', 'yellow', '#282c34')
" call NERDTreeHighlightFile('html', 'yellow', 'none', 'yellow', '#282c34')
" call NERDTreeHighlightFile('styl', 'cyan', 'none', 'cyan', '#282c34')
" call NERDTreeHighlightFile('css', 'cyan', 'none', 'cyan', '#282c34')
" call NERDTreeHighlightFile('coffee', 'Red', 'none', 'red', '#282c34')
" call NERDTreeHighlightFile('js', 'Red', 'none', '#ffa500', '#282c34')
" call NERDTreeHighlightFile('php', 'Magenta', 'none', '#ff00ff', '#282c34')
" call NERDTreeHighlightFile('go', '905532', 'none', '#ff00ff', '#282c34')
" call NERDTreeHighlightFile('py', 'blue', 'none', '#ff00ff', '#282c34')
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
let g:multi_cursor_use_default_mapping=0

" Default mapping
let g:multi_cursor_start_word_key      = '<C-n>'
let g:multi_cursor_select_all_word_key = '<A-n>'
let g:multi_cursor_start_key           = 'g<C-n>'
let g:multi_cursor_select_all_key      = 'g<A-n>'
let g:multi_cursor_next_key            = '<C-n>'
let g:multi_cursor_prev_key            = '<C-p>'
let g:multi_cursor_skip_key            = '<C-x>'
let g:multi_cursor_quit_key            = '<Esc>'

func! Multiple_cursors_before()
  if deoplete#is_enabled()
    call deoplete#disable()
    let g:deoplete_is_enable_before_multi_cursors = 1
  else
    let g:deoplete_is_enable_before_multi_cursors = 0
  endif
endfunc

func! Multiple_cursors_after()
  if g:deoplete_is_enable_before_multi_cursors
    call deoplete#enable()
  endif
endfunc
" ---- END vim-multiple-cursors ----


" ---- START nerdcomment ----
let g:NERDSpaceDelims = 1
let g:NERDCompactSexyComs = 1
let g:NERDDefaultAlign = 'left'
let g:NERDAltDelims_java = 1
let g:NERDCommentEmptyLines = 1
let g:NERDTrimTrailingWhitespace = 1
" ---- END ---

" ---- START prettier ----
let g:prettier#autoformat = 0
autocmd BufWritePre *.js,*.jsx,*.mjs,*.ts,*.tsx,*.css,*.less,*.scss,*.json,*.graphql,*.md,*.vue,*.yaml,*.html Prettier
" ---- END ----

" ---- START vim-go ----
let g:go_fmt_fail_silently = 1
call deoplete#custom#option('omni_patterns', { 'go': '[^. *\t]\.\w*' })
let g:go_highlight_types = 1
let g:go_highlight_diagnostic_errors = 0
let g:go_highlight_diagnostic_warnings = 0
" ---- END ----

" ---- snippets ----
" imap <C-k>     <Plug>(neosnippet_expand_or_jump)
" smap <C-k>     <Plug>(neosnippet_expand_or_jump)
" xmap <C-k>     <Plug>(neosnippet_expand_target)

smap <expr><TAB> neosnippet#expandable_or_jumpable() ?
\ "\<Plug>(neosnippet_expand_or_jump)" : "\<TAB>"

if has('conceal')
  set conceallevel=2 concealcursor=niv
endif
