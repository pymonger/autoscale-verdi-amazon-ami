# .bash_profile

# Get the aliases and functions
if [ -f ~/.bashrc ]; then
        . ~/.bashrc
fi

# User specific environment and startup programs

PATH=$PATH:$HOME/.local/bin:$HOME/bin

export PATH

# misc
umask 0022
export LD_LIBRARY_PATH=/usr/lib:/usr/lib64:/usr/local/lib:$LD_LIBRARY_PATH
export GIT_SSL_NO_VERIFY=true

# source verdi virtualenv
export VERDI_DIR=$HOME/verdi
source $VERDI_DIR/bin/activate
