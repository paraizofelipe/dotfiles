let mapleader = " "

nnoremap <C-j> :m .+1<CR>==
nnoremap <C-k> :m .-2<CR>==
inoremap <C-j> <Esc>:m .+1<CR>==gi
inoremap <C-k> <Esc>:m .-2<CR>==gi
vnoremap <C-j> :m '>+1<CR>gv=gv
vnoremap <C-k> :m '<-2<CR>gv=gv

nnoremap <Tab> >>_
nnoremap <S-Tab> <<_
inoremap <S-Tab> <C-D>
vnoremap <Tab> >gv
vnoremap <S-Tab> <gv

" ---- clipboard ----
vnoremap <C-y> "+y
nnoremap <C-p> "+p
vnoremap <C-p> "+p

" ---- buffers ----
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

" ---- indentLines ----
map gut :IndentLinesToggle<CR>

" ---- NERDTree ----
map <C-n> :NERDTreeToggle<CR>

" ---- VIM-GO -----
map gob :GoBuild<CR>
map gor :GoRun<CR>
map goi :Goinstall<CR>

" ---- Python -----
map lo :lopen<CR>
map lc :lclose<CR>
map ln :lnext<CR>

" ---- Ctags ----
map tu :UpdateTags<CR>
nmap <F8> :TagbarToggle<CR>

" ---- Custom ----
function ShowNoAsciiChar()
    syntax off
    syntax match nonascii "[^\x00-\x7F]"
    highlight nonascii ctermfg=0 ctermbg=1
endfunction

nnoremap <leader>c :call ShowSpecialChar()<CR>
