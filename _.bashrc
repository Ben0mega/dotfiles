#
# ~/.bashrc
#
if [ -f ~/.bashrc_noninteractive ] ; then
	source ~/.bashrc_noninteractive
fi

# If not running interactively, don't do anything
if [[ $- != *i* ]] ; then
	return
fi

if [ -f ~/.bash_aliases ] ; then
	. ~/.bash_aliases
fi

export GAME='ttysolitaire'
export TERMINAL="urxvt"

bind 'set show-all-if-ambiguous on'
#bind 'TAB:menu-complete'
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'
export HISTCONTROL=erasedups
shopt -s autocd

export LESS="IFRSX"

export PS1="\[\e[0;32m\][\u@\h:\[\e[1;34m\]\W\[\e[0;32m\]]\[\e[1;34m\]\\$ \[$(tput sgr0)\]"

export PIPENV_VENV_IN_PROJECT=1

export PYENV_ROOT="$HOME/.pyenv"
export PIPENV_PYTHON="$PYENV_ROOT/shims/python"
export PATH="$PATH:$PYENV_ROOT/bin"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

PERL5LIB="/home/bmehne/.perl5/lib/perl5${PERL5LIB:+:${PERL5LIB}}"; export PERL5LIB;
PERL_LOCAL_LIB_ROOT="/home/bmehne/.perl5${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}"; export PERL_LOCAL_LIB_ROOT;
PERL_MB_OPT="--install_base \"/home/bmehne/.perl5\""; export PERL_MB_OPT;
PERL_MM_OPT="INSTALL_BASE=/home/bmehne/.perl5"; export PERL_MM_OPT;

export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/SubFixer-4de3fa0bc760.json"

eval "$(zoxide init bash)"
eval "$(mcfly init bash)"
export MCFLY_FUZZY=2
export MCFLY_RESULTS_SORT=LAST_RUN

which fzf 2>/dev/null >/dev/null
if [ "$?" == "0" ]
then
    export CHEAT_USE_FZF=true
fi
