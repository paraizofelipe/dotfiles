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
set ts=4 sw=4 et
set backspace=indent,eol,start

set regexpengine=0
set foldmethod=indent
set foldlevel=20
" set foldopen=all
hi Folded ctermbg=234
hi Pmenu ctermbg=253 ctermfg=232

augroup javascript_folding
    au!
    au FileType javascript setlocal foldmethod=syntax
augroup END

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


source ~/.vim/plugins.vim
source ~/.vim/keys.vim
